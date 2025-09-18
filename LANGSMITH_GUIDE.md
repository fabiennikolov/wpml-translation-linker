# LangSmith Integration Guide for Clubs1 Translation Service

This guide covers how to integrate and use LangSmith for observability, evaluation, and prompt engineering in your Clubs1 translation service.

## Table of Contents

1. [Overview](#overview)
2. [Setup and Configuration](#setup-and-configuration)
3. [Observability](#observability)
4. [Evaluation](#evaluation)
5. [Prompt Engineering](#prompt-engineering)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Overview

[LangSmith](https://docs.smith.langchain.com/) is a platform for building production-grade LLM applications. It provides:

- **Observability**: Monitor and analyze your LLM application traces
- **Evaluation**: Test and optimize your application with high-quality evaluation datasets
- **Prompt Engineering**: Iterate on prompts with version control and collaboration

## Setup and Configuration

### 1. Environment Variables

Add these to your `.env` file:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=clubs1-translation
LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # Optional: for custom endpoints

# LangChain Tracing
LANGCHAIN_API_KEY=${LANGSMITH_API_KEY}
LANGCHAIN_PROJECT=${LANGSMITH_PROJECT}
LANGCHAIN_TRACING_V2=true
```

### 2. Installation

The required packages are already in your `requirements.txt`:

```txt
langchain==0.1.0
langchain-openai==0.0.5
langsmith>=0.0.77
```

### 3. Basic Integration

Your current `translator.py` already has basic LangSmith integration:

```python
from langchain.callbacks import LangChainTracer
from langsmith import Client

# Initialize LangSmith
if self.langsmith_api_key:
    os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = self.langsmith_project
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    self.tracer = LangChainTracer()
    self.langsmith_client = Client()
```

## Observability

### 1. Automatic Tracing

LangSmith automatically traces all LangChain operations. Your current setup already enables this:

```python
# This enables automatic tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
```

### 2. Custom Tracing

Add custom traces for better observability:

```python
from langsmith import traceable
from langchain.callbacks import get_openai_callback

class Clubs1Translator:
    @traceable(name="translate_post")
    def translate_post(self, post: Dict, target_language: str = "en") -> Dict:
        """Translate a single post with detailed tracing"""
        with get_openai_callback() as cb:
            # Your translation logic here
            result = self._perform_translation(post, target_language)
            
            # Log metrics
            logger.info(f"Translation completed - Tokens: {cb.total_tokens}, Cost: ${cb.total_cost}")
            
            return result
```

### 3. Custom Metrics and Tags

```python
from langsmith import Client

def translate_with_metrics(self, text: str, target_language: str) -> str:
    """Translate with custom metrics and tags"""
    client = Client()
    
    # Add custom metadata
    metadata = {
        "source_language": "bg",
        "target_language": target_language,
        "text_length": len(text),
        "service": "clubs1-translation"
    }
    
    # Create a run with custom tags
    with client.trace(
        name="custom_translation",
        tags=["translation", "clubs1", target_language],
        metadata=metadata
    ) as tracer:
        result = self.llm.invoke([
            SystemMessage(content="You are a professional translator..."),
            HumanMessage(content=text)
        ])
        
        # Add custom outputs
        tracer.add_outputs({
            "translated_text": result.content,
            "confidence_score": 0.95
        })
        
        return result.content
```

### 4. Dashboard Configuration

Create dashboards in LangSmith to monitor:

- **Request Rate**: Translation requests per minute
- **Error Rate**: Failed translations
- **Cost Tracking**: OpenAI API costs
- **Latency**: Translation response times
- **Quality Metrics**: Custom evaluation scores

## Evaluation

### 1. Creating Evaluation Datasets

```python
from langsmith import Client, RunEvaluator
from langsmith.evaluation import StringEvaluator

def create_evaluation_dataset():
    """Create a dataset for translation quality evaluation"""
    client = Client()
    
    # Sample evaluation data
    examples = [
        {
            "input": {
                "text": "България спечели мача срещу Германия",
                "target_language": "en"
            },
            "output": "Bulgaria won the match against Germany",
            "reference": "Bulgaria won the match against Germany"
        },
        # Add more examples...
    ]
    
    # Create dataset
    dataset = client.create_dataset(
        dataset_name="translation-quality",
        description="Evaluation dataset for Bulgarian to English translations"
    )
    
    # Add examples
    for example in examples:
        client.create_example(
            inputs=example["input"],
            outputs=example["output"],
            dataset_id=dataset.id
        )
    
    return dataset
```

### 2. Custom Evaluators

```python
class TranslationQualityEvaluator(StringEvaluator):
    """Custom evaluator for translation quality"""
    
    def evaluate_strings(
        self,
        prediction: str,
        input: str,
        reference: str = None,
        **kwargs
    ) -> dict:
        """Evaluate translation quality"""
        
        # Basic checks
        score = 0.0
        feedback = []
        
        # Check if translation is not empty
        if prediction.strip():
            score += 0.2
        else:
            feedback.append("Empty translation")
        
        # Check if translation is different from input
        if prediction != input:
            score += 0.3
        else:
            feedback.append("Translation identical to input")
        
        # Check for common translation errors
        if "ERROR" not in prediction.upper():
            score += 0.2
        else:
            feedback.append("Contains error indicators")
        
        # Check length similarity (rough quality indicator)
        if 0.5 <= len(prediction) / len(input) <= 2.0:
            score += 0.3
        else:
            feedback.append("Length ratio outside expected range")
        
        return {
            "score": score,
            "feedback": feedback,
            "metadata": {
                "input_length": len(input),
                "output_length": len(prediction),
                "length_ratio": len(prediction) / len(input) if input else 0
            }
        }
```

### 3. Running Evaluations

```python
def run_translation_evaluation():
    """Run evaluation on translation quality"""
    client = Client()
    
    # Get evaluation dataset
    dataset = client.read_dataset(dataset_name="translation-quality")
    
    # Create evaluator
    evaluator = TranslationQualityEvaluator()
    
    # Run evaluation
    results = client.run_evaluation(
        dataset=dataset,
        evaluators=[evaluator],
        llm_or_chain_factory=lambda: translator.llm
    )
    
    return results
```

## Prompt Engineering

### 1. Prompt Versioning

```python
from langsmith import Client

def manage_prompt_versions():
    """Manage different versions of translation prompts"""
    client = Client()
    
    # Create prompt template
    prompt_template = """You are a professional translator specializing in sports content translation from {source_language} to {target_language}.

Please translate the following text while maintaining:
- Sports terminology accuracy
- Cultural context
- Professional tone
- Original meaning

Text to translate: {text}

Translation:"""
    
    # Save prompt template
    prompt = client.create_prompt_template(
        name="sports-translation-v1",
        prompt_template=prompt_template,
        input_variables=["source_language", "target_language", "text"]
    )
    
    return prompt
```

### 2. Prompt Testing

```python
def test_prompt_variations():
    """Test different prompt variations"""
    client = Client()
    
    # Test cases
    test_cases = [
        {
            "source_language": "bg",
            "target_language": "en",
            "text": "България спечели мача срещу Германия"
        }
    ]
    
    # Different prompt variations
    prompts = [
        "Basic translation: {text}",
        "Professional sports translation: {text}",
        "Accurate sports terminology translation: {text}"
    ]
    
    results = []
    for i, prompt in enumerate(prompts):
        for test_case in test_cases:
            result = client.run_llm(
                prompt=prompt.format(**test_case),
                llm=translator.llm,
                tags=[f"prompt-variation-{i+1}"]
            )
            results.append(result)
    
    return results
```

### 3. Prompt Optimization

```python
def optimize_prompt():
    """Optimize prompt based on evaluation results"""
    client = Client()
    
    # Get recent runs
    runs = client.list_runs(
        project_name="clubs1-translation",
        tags=["translation"],
        limit=100
    )
    
    # Analyze performance
    successful_runs = [run for run in runs if run.error is None]
    failed_runs = [run for run in runs if run.error is not None]
    
    # Calculate success rate
    success_rate = len(successful_runs) / len(runs) if runs else 0
    
    logger.info(f"Translation success rate: {success_rate:.2%}")
    
    return {
        "success_rate": success_rate,
        "total_runs": len(runs),
        "successful_runs": len(successful_runs),
        "failed_runs": len(failed_runs)
    }
```

## Best Practices

### 1. Project Organization

```python
# Organize by environment
os.environ["LANGCHAIN_PROJECT"] = f"clubs1-translation-{os.getenv('ENVIRONMENT', 'dev')}"

# Use tags for categorization
tags = ["translation", "clubs1", "production" if os.getenv("ENVIRONMENT") == "prod" else "development"]
```

### 2. Error Handling

```python
def safe_translation(self, text: str, target_language: str) -> str:
    """Safe translation with error tracking"""
    try:
        with client.trace(name="safe_translation") as tracer:
            result = self.translate_text(text, target_language)
            tracer.add_outputs({"success": True, "result": result})
            return result
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        tracer.add_outputs({"success": False, "error": str(e)})
        return f"Translation error: {str(e)}"
```

### 3. Performance Monitoring

```python
import time
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name: str):
    """Monitor operation performance"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"{operation_name} completed in {duration:.2f}s")
        
        # Send to LangSmith
        client = Client()
        client.log_metric(
            name=f"{operation_name}_duration",
            value=duration,
            step=1
        )
```

## Troubleshooting

### Common Issues

1. **API Key Issues**

   ```python
   # Check if API key is set
   if not os.getenv("LANGSMITH_API_KEY"):
       logger.warning("LANGSMITH_API_KEY not set - tracing disabled")
   ```

2. **Project Not Found**

   ```python
   # Create project if it doesn't exist
   try:
       client.read_project(project_name="clubs1-translation")
   except:
       client.create_project(project_name="clubs1-translation")
   ```

3. **Tracing Not Working**

   ```python
   # Verify tracing is enabled
   if os.getenv("LANGCHAIN_TRACING_V2") != "true":
       os.environ["LANGCHAIN_TRACING_V2"] = "true"
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("langsmith").setLevel(logging.DEBUG)
```

## Next Steps

1. **Set up your LangSmith account** at [smith.langchain.com](https://smith.langchain.com/)
2. **Configure environment variables** with your API key
3. **Create evaluation datasets** for your translation use cases
4. **Set up dashboards** to monitor your application
5. **Implement custom evaluators** for translation quality
6. **Optimize prompts** based on evaluation results

For more information, visit the [LangSmith documentation](https://docs.smith.langchain.com/).
