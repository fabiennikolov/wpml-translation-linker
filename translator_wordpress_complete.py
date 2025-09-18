#!/usr/bin/env python3
"""
Complete WordPress Post Translator for Clubs1.bg
Translates specific fields while preserving all original data structure
"""

import os
import json
import logging
import copy
from typing import Dict, List, Any
from datetime import datetime

import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.callbacks import get_openai_callback
from langsmith import traceable

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordPressCompleteTranslator:
    """
    Complete WordPress post translator that preserves all original data
    while translating specific fields: title.rendered, content.rendered,
    excerpt.rendered, yoast_head_json.title, yoast_head_json.description
    """

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "clubs1-translation")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Initialize OpenAI client with GPT-4o-mini (most cost-effective)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0.1, openai_api_key=self.openai_api_key
        )

        # Initialize LangSmith for tracking
        if self.langsmith_api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            logger.info(
                f"LangSmith tracking enabled for project: {self.langsmith_project}"
            )
        else:
            logger.warning(
                "LANGSMITH_API_KEY not provided. LangSmith tracking will be disabled."
            )

    @traceable(name="fetch_wordpress_posts_complete")
    def fetch_wordpress_posts(self, limit: int = 10) -> List[Dict]:
        """
        Fetch complete WordPress posts from Clubs1.bg API
        """
        try:
            url = "https://clubs1.bg/wp-json/wp/v2/posts"
            params = {
                "per_page": limit,
                "orderby": "date",
                "order": "desc",
                # No _fields parameter to get ALL data
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            posts = response.json()
            logger.info(f"Fetched {len(posts)} complete WordPress posts from Clubs1.bg")
            return posts

        except requests.RequestException as e:
            logger.error(f"Error fetching posts from Clubs1.bg: {e}")
            return []

    def load_posts_from_file(self, filename: str = "postsclubs1.json") -> List[Dict]:
        """
        Load posts from local JSON file
        """
        try:
            with open(filename, "r", encoding="utf-8") as f:
                posts = json.load(f)
            logger.info(f"Loaded {len(posts)} posts from {filename}")
            return posts
        except FileNotFoundError:
            logger.error(f"File {filename} not found")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON from {filename}: {e}")
            return []

    @traceable(name="translate_text_simple")
    def translate_text(
        self,
        text: str,
        target_language: str = "en",
        source_language: str = "bg",
        content_type: str = "general",
    ) -> str:
        """
        Translate text content while preserving HTML structure
        """
        if not text.strip():
            return ""

        # Skip translation if text is too short
        if len(text.strip()) < 3:
            return text

        # Determine content-specific instructions
        content_instructions = {
            "title": "This is a title/headline. Keep it concise and impactful.",
            "content": "This is article content with HTML formatting. Preserve all HTML tags and structure.",
            "excerpt": "This is an article excerpt/summary. Keep it concise.",
            "seo_title": "This is an SEO title for search engines. Keep it under 60 characters if possible.",
            "seo_description": "This is an SEO meta description. Keep it under 160 characters if possible.",
        }

        content_instruction = content_instructions.get(content_type, "")

        system_prompt = f"""You are a professional translator specializing in automotive and sports content translation from {source_language} to {target_language}.

        Your task is to translate the following text while:
        1. Maintaining the original meaning and context exactly
        2. Preserving all HTML tags, attributes, and structure (if present)
        3. Keeping sports terminology accurate (Formula 1, team names, driver names, etc.)
        4. Ensuring proper grammar and readability in the target language
        5. Preserving proper nouns (names, places, brands) correctly
        6. Maintaining the tone and style appropriate for automotive journalism
        
        {content_instruction}
        
        IMPORTANT: Only translate the text content - never translate HTML tags, attributes, or structural elements."""

        human_prompt = f"Please translate the following {source_language} text to {target_language}:\n\n{text}"

        try:
            with get_openai_callback() as cb:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=human_prompt),
                ]

                response = self.llm.invoke(messages)
                translated_text = response.content.strip()

                # Log cost information
                logger.info(
                    f"Translation completed ({content_type}) - Tokens: {cb.total_tokens}, "
                    f"Cost: ${cb.total_cost:.4f}, Length: {len(text)} -> {len(translated_text)} chars"
                )

                return translated_text

        except Exception as e:
            logger.error(f"Error translating text ({content_type}): {e}")
            return f"[Translation Error: {str(e)}]"

    @traceable(name="translate_wordpress_post_complete")
    def translate_wordpress_post(
        self, post: Dict[str, Any], target_language: str = "en"
    ) -> Dict[str, Any]:
        """
        Translate a complete WordPress post while preserving all original data
        """
        start_time = datetime.now()

        # Create a deep copy to preserve all original data
        translated_post = copy.deepcopy(post)

        # Extract fields to translate
        fields_to_translate = {
            "title.rendered": post.get("title", {}).get("rendered", ""),
            "content.rendered": post.get("content", {}).get("rendered", ""),
            "excerpt.rendered": post.get("excerpt", {}).get("rendered", ""),
            "yoast_head_json.title": post.get("yoast_head_json", {}).get("title", ""),
            "yoast_head_json.description": post.get("yoast_head_json", {}).get(
                "description", ""
            ),
        }

        # Log what we're translating
        logger.info(
            f"Translating post {post.get('id', 'unknown')} with fields: {list(fields_to_translate.keys())}"
        )

        translation_results = {}

        # Translate each field
        for field_path, original_text in fields_to_translate.items():
            if original_text:
                # Determine content type for better translation
                if "title" in field_path:
                    content_type = "seo_title" if "yoast" in field_path else "title"
                elif "description" in field_path:
                    content_type = "seo_description"
                elif "content" in field_path:
                    content_type = "content"
                elif "excerpt" in field_path:
                    content_type = "excerpt"
                else:
                    content_type = "general"

                translated_text = self.translate_text(
                    original_text, target_language, content_type=content_type
                )
                translation_results[field_path] = translated_text

                logger.info(
                    f"Translated {field_path}: {len(original_text)} -> {len(translated_text)} chars"
                )
            else:
                translation_results[field_path] = ""

        # Apply translations to the copied post structure
        if translation_results.get("title.rendered"):
            translated_post["title"]["rendered"] = translation_results["title.rendered"]

        if translation_results.get("content.rendered"):
            translated_post["content"]["rendered"] = translation_results[
                "content.rendered"
            ]

        if translation_results.get("excerpt.rendered"):
            translated_post["excerpt"]["rendered"] = translation_results[
                "excerpt.rendered"
            ]

        if translation_results.get("yoast_head_json.title"):
            if "yoast_head_json" not in translated_post:
                translated_post["yoast_head_json"] = {}
            translated_post["yoast_head_json"]["title"] = translation_results[
                "yoast_head_json.title"
            ]

        if translation_results.get("yoast_head_json.description"):
            if "yoast_head_json" not in translated_post:
                translated_post["yoast_head_json"] = {}
            translated_post["yoast_head_json"]["description"] = translation_results[
                "yoast_head_json.description"
            ]

        # Add translation metadata
        processing_time = (datetime.now() - start_time).total_seconds()

        # Add translation metadata without breaking the original structure
        translated_post["_translation_metadata"] = {
            "target_language": target_language,
            "translation_timestamp": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            "translated_fields": list(translation_results.keys()),
            "character_counts": {
                field: len(text) for field, text in translation_results.items()
            },
            "original_character_counts": {
                field: len(original_text)
                for field, original_text in fields_to_translate.items()
            },
        }

        logger.info(
            f"Completed translation of post {post.get('id', 'unknown')} in {processing_time:.2f} seconds"
        )
        return translated_post

    @traceable(name="batch_translate_wordpress_posts")
    def batch_translate_posts(
        self, posts: List[Dict], target_language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Translate multiple WordPress posts in batch
        """
        results = []
        total_chars_original = 0
        total_chars_translated = 0

        for i, post in enumerate(posts, 1):
            logger.info(
                f"Translating post {i}/{len(posts)} (ID: {post.get('id', 'unknown')})"
            )

            translated_post = self.translate_wordpress_post(post, target_language)
            results.append(translated_post)

            # Track character counts from metadata
            if "_translation_metadata" in translated_post:
                metadata = translated_post["_translation_metadata"]
                for field, count in metadata.get(
                    "original_character_counts", {}
                ).items():
                    total_chars_original += count
                for field, count in metadata.get("character_counts", {}).items():
                    total_chars_translated += count

        logger.info(
            f"Completed batch translation of {len(posts)} posts. "
            f"Characters: {total_chars_original:,} -> {total_chars_translated:,}"
        )
        return results


# Example usage and test function
if __name__ == "__main__":
    # Initialize translator
    translator = WordPressCompleteTranslator()

    # Load posts from local file (or fetch from API)
    print("📁 Loading posts from postsclubs1.json...")
    posts = translator.load_posts_from_file("postsclubs1.json")

    if not posts:
        print("📡 Fetching posts from API...")
        posts = translator.fetch_wordpress_posts(limit=2)

    if posts:
        # Take first post for demonstration
        test_post = posts[0]

        print(f"\n🔍 Original post structure (ID: {test_post.get('id', 'unknown')}):")
        print(f"  Title: {test_post.get('title', {}).get('rendered', '')[:50]}...")
        print(
            f"  Content length: {len(test_post.get('content', {}).get('rendered', ''))} chars"
        )
        print(
            f"  Excerpt length: {len(test_post.get('excerpt', {}).get('rendered', ''))} chars"
        )
        print(
            f"  Yoast title: {test_post.get('yoast_head_json', {}).get('title', '')[:50]}..."
        )
        print(
            f"  Yoast description: {test_post.get('yoast_head_json', {}).get('description', '')[:50]}..."
        )

        # Translate to English
        print("\n🔄 Translating to English...")
        translated_post = translator.translate_wordpress_post(
            test_post, target_language="en"
        )

        print("\n✅ Translation completed!")
        print(
            f"  Translated title: {translated_post.get('title', {}).get('rendered', '')[:50]}..."
        )
        print(
            f"  Translated content length: {len(translated_post.get('content', {}).get('rendered', ''))} chars"
        )
        print(
            f"  Translated excerpt length: {len(translated_post.get('excerpt', {}).get('rendered', ''))} chars"
        )
        print(
            f"  Translated Yoast title: {translated_post.get('yoast_head_json', {}).get('title', '')[:50]}..."
        )
        print(
            f"  Translated Yoast description: {translated_post.get('yoast_head_json', {}).get('description', '')[:50]}..."
        )

        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"wordpress_complete_translation_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(translated_post, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Complete translated post saved to: {filename}")
        print(
            f"📊 Translation metadata: {translated_post.get('_translation_metadata', {})}"
        )

    else:
        print("❌ No posts found to translate")
