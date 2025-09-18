import os
import json
import requests
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from translator_wordpress_complete import WordPressCompleteTranslator

# Adapter class to bridge API calls with the actual translator
class TranslatorAdapter:
    def __init__(self):
        self.translator = WordPressCompleteTranslator()
        self.openai_api_key = self.translator.openai_api_key
        self.langsmith_api_key = self.translator.langsmith_api_key
    
    def fetch_wordpress_posts(self, limit: int = 10):
        return self.translator.fetch_wordpress_posts(limit)
    
    def batch_translate_posts(self, posts, target_language="en"):
        return self.translator.batch_translate_posts(posts, target_language)
    
    def translate_text(self, text, target_language="en", source_language="bg"):
        return self.translator.translate_text(text, target_language, source_language)
    
    def extract_post_content(self, post):
        # Simple extraction - just return the post for now
        return post
    
    def translate_post(self, post, target_language="en"):
        # Use the complete translator method
        return self.translator.translate_wordpress_post(post, target_language)
    
    def get_cost_analytics(self, days=7):
        # Mock implementation - return empty analytics
        return {"message": "Cost analytics not implemented yet", "days": days}

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Clubs1 Translation Service",
    description="AI-powered translation service for Clubs1.bg sports content using OpenAI and LangChain",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize translator
translator = None


@app.on_event("startup")
async def startup_event():
    global translator
    try:
        translator = TranslatorAdapter()
        print("Translation service initialized successfully")
    except Exception as e:
        print(f"Failed to initialize translation service: {e}")
        raise


# Pydantic models
class TranslationRequest(BaseModel):
    target_language: str = Field(
        default="en", description="Target language code (e.g., 'en', 'es', 'fr')"
    )
    source_language: str = Field(default="bg", description="Source language code")
    limit: int = Field(
        default=5, ge=1, le=20, description="Number of posts to fetch and translate"
    )


class PostTranslationRequest(BaseModel):
    post_id: str = Field(description="WordPress post ID")
    target_language: str = Field(default="en", description="Target language code")


class TextTranslationRequest(BaseModel):
    text: str = Field(description="Text to translate")
    target_language: str = Field(default="en", description="Target language code")
    source_language: str = Field(default="bg", description="Source language code")


class AnalyticsRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=30, description="Number of days to analyze")


class WordPressPostRequest(BaseModel):
    title: str = Field(description="Post title")
    content: str = Field(description="Post content")
    excerpt: Optional[str] = Field(default="", description="Post excerpt")
    status: str = Field(default="publish", description="Post status")
    wpml_language: str = Field(default="en", description="WPML language code")
    original_post_id: Optional[int] = Field(default=None, description="Original post ID for linking")
    wordpress_url: str = Field(description="WordPress site URL")
    username: str = Field(description="WordPress username")
    password: str = Field(description="WordPress application password")


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Clubs1 Translation Service",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if translator is None:
        raise HTTPException(
            status_code=503, detail="Translation service not initialized"
        )

    return {
        "status": "healthy",
        "openai_configured": bool(translator.openai_api_key),
        "langsmith_configured": bool(translator.langsmith_api_key),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/translate/posts", response_model=List[Dict[str, Any]])
async def translate_posts(request: TranslationRequest):
    """
    Fetch and translate posts from Clubs1.bg
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        # Fetch posts from Clubs1.bg
        posts = translator.fetch_wordpress_posts(limit=request.limit)

        if not posts:
            return []

        # Translate posts
        translated_posts = translator.batch_translate_posts(
            posts, target_language=request.target_language
        )

        return translated_posts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/translate/post/{post_id}")
async def translate_single_post(post_id: str, request: PostTranslationRequest):
    """
    Translate a specific post by ID
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        # Fetch specific post
        url = f"https://clubs1.bg/wp-json/wp/v2/posts/{post_id}"
        response = requests.get(url)
        response.raise_for_status()

        post = response.json()
        post_content = translator.extract_post_content(post)
        translated_post = translator.translate_post(
            post_content, request.target_language
        )

        return translated_post

    except requests.RequestException:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/translate/text")
async def translate_text(request: TextTranslationRequest):
    """
    Translate a single piece of text
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        translated_text = translator.translate_text(
            request.text,
            target_language=request.target_language,
            source_language=request.source_language,
        )

        return {
            "original_text": request.text,
            "translated_text": translated_text,
            "source_language": request.source_language,
            "target_language": request.target_language,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.get("/analytics/cost")
async def get_cost_analytics(days: int = 7):
    """
    Get cost analytics from LangSmith
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        analytics = translator.get_cost_analytics(days=days)
        return analytics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics failed: {str(e)}")


@app.get("/posts/recent")
async def get_recent_posts(limit: int = 10):
    """
    Get recent posts from Clubs1.bg without translation
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        posts = translator.fetch_clubs1_posts(limit=limit)
        return posts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@app.post("/translate/batch", response_model=List[Dict[str, Any]])
async def batch_translate_custom_posts(
    posts: List[Dict[str, Any]], target_language: str = "en"
):
    """
    Translate a batch of custom posts
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    try:
        results = []

        for post in posts:
            post_content = translator.extract_post_content(post)
            translated_post = translator.translate_post(post_content, target_language)
            results.append(translated_post)

        return results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Batch translation failed: {str(e)}"
        )


# Background task for async translation
@app.post("/translate/async")
async def start_async_translation(
    request: TranslationRequest, background_tasks: BackgroundTasks
):
    """
    Start an asynchronous translation job
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")

    job_id = f"translation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Store job info (in a real app, you'd use a database)
    job_info = {
        "job_id": job_id,
        "status": "started",
        "request": request.dict(),
        "started_at": datetime.now().isoformat(),
    }

    # Add background task
    background_tasks.add_task(
        run_async_translation, job_id, request.target_language, request.limit
    )

    return {
        "job_id": job_id,
        "status": "started",
        "message": "Translation job started. Check status with /jobs/{job_id}",
    }


async def run_async_translation(job_id: str, target_language: str, limit: int):
    """
    Background task for async translation
    """
    try:
        # This would be stored in a database in a real application
        print(f"Starting async translation job {job_id}")

        posts = translator.fetch_clubs1_posts(limit=limit)
        translated_posts = translator.batch_translate_posts(posts, target_language)

        # Save results (in a real app, save to database)
        with open(f"translation_job_{job_id}.json", "w", encoding="utf-8") as f:
            json.dump(translated_posts, f, ensure_ascii=False, indent=2)

        print(f"Completed async translation job {job_id}")

    except Exception as e:
        print(f"Error in async translation job {job_id}: {e}")


@app.post("/wordpress/create-post")
async def create_wordpress_post(request: WordPressPostRequest):
    """
    Create a new WordPress post with WPML language support
    """
    try:
        # Prepare WordPress REST API request
        wp_api_url = f"{request.wordpress_url.rstrip('/')}/wp-json/wp/v2/posts"
        
        # Create authentication header
        credentials = f"{request.username}:{request.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        # Prepare post data
        post_data = {
            "title": request.title,
            "content": request.content,
            "excerpt": request.excerpt,
            "status": request.status,
            "meta": {
                "wpml_language": request.wpml_language
            }
        }
        
        # Create the post
        response = requests.post(wp_api_url, headers=headers, json=post_data)
        response.raise_for_status()
        
        created_post = response.json()
        post_id = created_post.get("id")
        
        # If we have an original post ID, link the translations using the plugin
        if request.original_post_id and post_id:
            link_result = await link_wpml_translations(
                request.wordpress_url,
                request.username,
                request.password,
                request.original_post_id,
                post_id,
                request.wpml_language
            )
            
            return {
                "success": True,
                "post_id": post_id,
                "post_url": created_post.get("link"),
                "wpml_language": request.wpml_language,
                "translation_linked": link_result.get("success", False),
                "trid": link_result.get("trid") if link_result.get("success") else None,
                "created_post": created_post
            }
        
        return {
            "success": True,
            "post_id": post_id,
            "post_url": created_post.get("link"),
            "wpml_language": request.wpml_language,
            "translation_linked": False,
            "created_post": created_post
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"WordPress API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@app.post("/wordpress/translate-and-create")
async def translate_and_create_wordpress_post(
    post_id: str,
    wordpress_url: str,
    username: str,
    password: str,
    target_language: str = "en",
    source_language: str = "bg"
):
    """
    Translate a Clubs1.bg post and create it in WordPress with WPML linking
    """
    if translator is None:
        raise HTTPException(status_code=503, detail="Translation service not available")
    
    try:
        # Fetch and translate the post
        url = f"https://clubs1.bg/wp-json/wp/v2/posts/{post_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        post = response.json()
        post_content = translator.extract_post_content(post)
        translated_post = translator.translate_post(post_content, target_language)
        
        # Create WordPress post request
        wp_request = WordPressPostRequest(
            title=translated_post.get("title", ""),
            content=translated_post.get("content", ""),
            excerpt=translated_post.get("excerpt", ""),
            status="publish",
            wpml_language=target_language,
            original_post_id=int(post_id),
            wordpress_url=wordpress_url,
            username=username,
            password=password
        )
        
        # Create the post
        result = await create_wordpress_post(wp_request)
        
        return {
            "success": True,
            "original_post_id": post_id,
            "translated_post_id": result.get("post_id"),
            "translation_data": translated_post,
            "wordpress_result": result
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=404, detail=f"Post {post_id} not found: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation and creation failed: {str(e)}")


async def link_wpml_translations(wordpress_url: str, username: str, password: str, 
                                original_post_id: int, translated_post_id: int, 
                                target_language: str, source_language: str = "bg"):
    """
    Helper function to link translations using the WPML plugin
    """
    try:
        # Use the plugin's REST API endpoint
        link_api_url = f"{wordpress_url.rstrip('/')}/wp-json/wpml-linker/v1/link-translations"
        
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }
        
        link_data = {
            "original_post_id": original_post_id,
            "translated_post_id": translated_post_id,
            "target_language": target_language,
            "source_language": source_language
        }
        
        response = requests.post(link_api_url, headers=headers, json=link_data)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        print(f"Failed to link translations: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8001"))

    uvicorn.run(app, host=host, port=port)
