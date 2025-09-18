# Clubs1 Translation Service

An AI-powered translation service for [Clubs1.bg](https://clubs1.bg) sports content using OpenAI, LangChain, and LangSmith for cost tracking.

## Features

- 🌐 **Multi-language Translation**: Translate Bulgarian sports content to any language
- 🤖 **AI-Powered**: Uses OpenAI GPT-4 for high-quality translations
- 📊 **Cost Tracking**: LangSmith integration for monitoring OpenAI usage costs
- 🚀 **FastAPI Web Service**: RESTful API for easy integration
- 💻 **CLI Interface**: Command-line tool for quick translations
- 📈 **Analytics**: Track translation costs and usage statistics
- 🔄 **Batch Processing**: Translate multiple posts efficiently

## Installation

1. **Clone and navigate to the service directory:**

   ```bash
   cd translation_service
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**

   ```bash
   cp env_example.txt .env
   # Edit .env with your API keys
   ```

4. **Configure API keys:**
   - Get an [OpenAI API key](https://platform.openai.com/api-keys)
   - Get a [LangSmith API key](https://smith.langchain.com/) (optional, for cost tracking)

## Configuration

Edit the `.env` file with your API keys:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for cost tracking)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=clubs1-translation

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
```

## Usage

### Command Line Interface (CLI)

#### Translate Recent Posts

```bash
# Translate 5 recent posts to English
python cli.py translate-posts --limit 5 --target en

# Translate to Spanish
python cli.py translate-posts --limit 3 --target es

# Save to custom file
python cli.py translate-posts --limit 10 --target en --output my_translations.json
```

#### Translate Specific Post

```bash
# Translate post by ID
python cli.py translate-post --post-id 225262 --target en
```

#### Translate Custom Text

```bash
# Translate Bulgarian text to English
python cli.py translate-text --text "Спортен текст" --target en

# Translate to different language
python cli.py translate-text --text "Sports text" --source en --target bg
```

#### Get Cost Analytics

```bash
# Get analytics for last 7 days
python cli.py analytics --days 7

# Get analytics for last 30 days
python cli.py analytics --days 30
```

#### Health Check

```bash
python cli.py health
```

### Web API Service

#### Start the API Server

```bash
python api.py
```

The service will be available at `http://localhost:8000`

#### API Endpoints

**Health Check:**

```bash
curl http://localhost:8000/health
```

**Translate Posts:**

```bash
curl -X POST "http://localhost:8000/translate/posts" \
  -H "Content-Type: application/json" \
  -d '{"target_language": "en", "limit": 5}'
```

**Translate Single Post:**

```bash
curl -X POST "http://localhost:8000/translate/post/225262" \
  -H "Content-Type: application/json" \
  -d '{"target_language": "en"}'
```

**Translate Text:**

```bash
curl -X POST "http://localhost:8000/translate/text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Спортен текст", "target_language": "en"}'
```

**Get Cost Analytics:**

```bash
curl "http://localhost:8000/analytics/cost?days=7"
```

**Get Recent Posts (without translation):**

```bash
curl "http://localhost:8000/posts/recent?limit=10"
```

#### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Example Output

### Translated Post Structure

```json
{
  "original": {
    "id": "225262",
    "title": "Според Монтоя само забрана от Ред Бул би спряла Хорнер да се върне в F1",
    "content": "Кристиан Хорнер ще се върне във Формула 1...",
    "excerpt": "Бившият F1 пилот коментира...",
    "slug": "spored-montoya-samo-zabrana-ot-rid-bul-bi-spryala-horner-da-se-varne-v-f1",
    "date": "2025-08-25T11:18:27",
    "link": "https://clubs1.bg/news/spored-montoya-samo-zabrana-ot-rid-bul-bi-spryala-horner-da-se-varne-v-f1/"
  },
  "translated": {
    "title": "According to Montoya, only a Red Bull ban would prevent Horner from returning to F1",
    "content": "Christian Horner will return to Formula 1...",
    "excerpt": "The former F1 driver commented...",
    "slug": "spored-montoya-samo-zabrana-ot-rid-bul-bi-spryala-horner-da-se-varne-v-f1",
    "date": "2025-08-25T11:18:27",
    "link": "https://clubs1.bg/news/spored-montoya-samo-zabrana-ot-rid-bul-bi-spryala-horner-da-se-varne-v-f1/"
  },
  "metadata": {
    "target_language": "en",
    "processing_time_seconds": 2.34,
    "translation_timestamp": "2025-01-27T10:30:00",
    "post_id": "225262"
  }
}
```

### Cost Analytics

```json
{
  "period_days": 7,
  "total_runs": 45,
  "total_tokens": 125000,
  "estimated_cost_usd": 0.3750,
  "average_cost_per_run": 0.0083
}
```

## Supported Languages

The service supports translation to any language supported by OpenAI GPT-4. Common language codes:

- `en` - English
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean

## Cost Tracking with LangSmith

When LangSmith is configured, you can:

1. **Monitor costs** in real-time at [smith.langchain.com](https://smith.langchain.com)
2. **Track usage** patterns and optimize translations
3. **Analyze performance** and quality metrics
4. **Set up alerts** for cost thresholds

### LangSmith Dashboard Features

- Token usage tracking
- Cost per translation
- Response time monitoring
- Quality metrics
- Usage trends

## Development

### Project Structure

```
translation_service/
├── translator.py      # Core translation logic
├── api.py            # FastAPI web service
├── cli.py            # Command-line interface
├── requirements.txt  # Python dependencies
├── env_example.txt   # Environment variables template
└── README.md         # This file
```

### Adding New Features

1. **Custom Translation Models:**

   ```python
   # In translator.py, modify the translate_text method
   def translate_text(self, text: str, target_language: str = "en", source_language: str = "bg") -> str:
       # Custom logic here
   ```

2. **New API Endpoints:**

   ```python
   # In api.py, add new endpoints
   @app.post("/translate/custom")
   async def custom_translation():
       # Custom endpoint logic
   ```

3. **CLI Commands:**

   ```python
   # In cli.py, add new subparsers
   custom_parser = subparsers.add_parser("custom", help="Custom command")
   ```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error:**

   ```
   Error: OPENAI_API_KEY environment variable is required
   ```

   **Solution:** Set your OpenAI API key in the `.env` file

2. **LangSmith Connection Error:**

   ```
   Error getting analytics: Connection failed
   ```

   **Solution:** Check your LangSmith API key or disable LangSmith tracking

3. **Clubs1.bg API Error:**

   ```
   Error fetching posts from Clubs1.bg: 404 Not Found
   ```

   **Solution:** Check if the Clubs1.bg API is accessible

### Performance Optimization

1. **Batch Processing:** Use batch endpoints for multiple translations
2. **Caching:** Implement caching for repeated translations
3. **Rate Limiting:** Respect OpenAI API rate limits
4. **Token Optimization:** Use shorter prompts for cost efficiency

## License

This project is part of the Clubs1 WordPress setup and follows the same licensing terms.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check LangSmith dashboard for detailed logs
4. Contact the development team

---

**Note:** This service is specifically designed for translating Bulgarian sports content from Clubs1.bg. The translation quality is optimized for sports journalism and Formula 1 content.
