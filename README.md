# TikTok Hashtag Scraper V7 - Complete Fixed Version

A production-ready TikTok hashtag scraping tool with Playwright automation, aggressive View More button detection, Supabase integration, and serverless deployment capabilities.

## 🚀 Features

### V7 Core Capabilities
- ✅ **Playwright Automation**: Stealth browser automation for reliable scraping
- ✅ **Aggressive View More Detection**: Multiple strategies to load maximum hashtags
- ✅ **Smart Navigation**: Ensures correct page navigation before scraping
- ✅ **Song Title Filtering**: Prevents extracting music titles as hashtags
- ✅ **Engagement Scoring**: 1-10 scale algorithm based on posts and category
- ✅ **Sentiment Analysis**: TextBlob polarity and label classification
- ✅ **Numeric Conversion**: K/M notation to integers (1.2K → 1200)
- ✅ **Supabase Integration**: Real-time cloud database uploads
- ✅ **CSV Export**: Timestamped file generation
- ✅ **UUID Session Tracking**: Version ID for batch tracking
- ✅ **Debug Mode**: HTML page saves and detailed logging
- ✅ **Error Recovery**: Comprehensive exception handling

### Data Quality Features
- Category-based engagement boost algorithm
- Duplicate hashtag detection and filtering
- ISO 8601 timestamp formatting
- JSONB metadata storage for extensibility

## 📋 Requirements

- **Python**: 3.8 or higher
- **Playwright**: Browser automation framework
- **Supabase Account**: For cloud database storage
- **Internet Connection**: Required for TikTok scraping
- **Disk Space**: ~500MB for Playwright browsers

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Aditya0611/tik-tok_trending_hashtags.git
   cd tik-tok_trending_hashtags
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Download TextBlob corpora** (for sentiment analysis)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
   ```

## ⚙️ Configuration

### Supabase Configuration

**Option 1: Edit base.py directly** (Current method)
```python
# In base.py, update these variables:
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_key_here"
```

**Option 2: Environment Variables** (Recommended for production)
```bash
# Create .env file:
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here

# Then modify base.py to use os.getenv():
# SUPABASE_URL = os.getenv('SUPABASE_URL')
# SUPABASE_KEY = os.getenv('SUPABASE_KEY')
```

### Function Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scrolls` | int | 15 | Number of scroll attempts to load more hashtags |
| `delay` | int | 3 | Delay between scrolls in seconds |
| `headless` | bool | False | Run browser in headless mode (no GUI) |
| `debug` | bool | True | Enable debug logging and HTML saving |
| `upload_to_db` | bool | True | Upload results to Supabase |
| `output_file` | str | None | Custom CSV filename (auto-generated if None) |
| `proxies` | dict | None | Proxy configuration (not currently implemented) |

### Database Table Setup

**Required**: Your Supabase table must have these columns:
- `platform` (TEXT)
- `topic` (TEXT) - The hashtag
- `engagement_score` (DECIMAL)
- `sentiment_polarity` (DECIMAL)
- `sentiment_label` (TEXT)
- `posts` (BIGINT) - Numeric posts count
- `views` (BIGINT) - Numeric views count
- `metadata` (JSONB)
- `scraped_at` (TIMESTAMPTZ)
- `version_id` (TEXT) - Session tracking UUID

## 🚀 Usage

### Basic Usage

```python
import asyncio
from base import scrape_tiktok_hashtags_fixed

# Simple run with defaults
async def main():
    results = await scrape_tiktok_hashtags_fixed(
        scrolls=15,           # Number of scroll attempts
        delay=3,              # Delay between scrolls (seconds)
        headless=False,       # Show browser window
        debug=True,           # Enable debug logging
        upload_to_db=True     # Upload to Supabase
    )
    print(f"✅ Scraped {len(results)} hashtags")
    return results

asyncio.run(main())
```

### Advanced Configuration

```python
import asyncio
from base import scrape_tiktok_hashtags_fixed

# Production mode with custom settings
async def production_scrape():
    results = await scrape_tiktok_hashtags_fixed(
        scrolls=20,              # More scrolls for max data
        delay=5,                 # Longer delays to avoid detection
        headless=True,           # Run in background
        debug=False,             # Disable debug mode
        upload_to_db=True,       # Upload to Supabase
        output_file="custom_hashtags.csv"  # Custom CSV filename
    )
    return results

asyncio.run(production_scrape())
```

### Quick Test

```bash
# Run the built-in test function
python -c "import asyncio; from base import test_fixed_scraper; asyncio.run(test_fixed_scraper())"
```

## 📊 Data Schema

### V7 Clean Schema
```json
{
  "platform": "TikTok",
  "topic": "#trending",
  "engagement_score": 8.5,
  "sentiment_polarity": 0.3,
  "sentiment_label": "Positive",
  "posts": 1500000,
  "views": 50000000,
  "metadata": {
    "rank": 1,
    "category": "Entertainment",
    "source_url": "https://ads.tiktok.com/..."
  },
  "scraped_at": "2024-01-01T12:00:00Z",
  "version_id": "uuid-string"
}
```

## 🗄️ Database Setup

### Supabase Table Schema
```sql
CREATE TABLE tiktok (
    id SERIAL PRIMARY KEY,
    platform TEXT DEFAULT 'TikTok',
    topic TEXT NOT NULL,
    engagement_score DECIMAL(3,1),
    sentiment_polarity DECIMAL(4,3),
    sentiment_label TEXT,
    posts BIGINT,
    views BIGINT,
    metadata JSONB,
    scraped_at TIMESTAMPTZ,
    version_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_tiktok_topic ON tiktok(topic);
CREATE INDEX idx_tiktok_scraped_at ON tiktok(scraped_at);
CREATE INDEX idx_tiktok_engagement_score ON tiktok(engagement_score);
```

## 📈 Monitoring & Analytics

### Supabase Analytics Queries
```sql
-- Get trending hashtags by engagement score
SELECT topic, engagement_score, sentiment_label, posts
FROM tiktok 
WHERE scraped_at >= NOW() - INTERVAL '7 days'
ORDER BY engagement_score DESC
LIMIT 20;

-- Sentiment distribution
SELECT sentiment_label, COUNT(*) as count
FROM tiktok 
WHERE scraped_at >= NOW() - INTERVAL '7 days'
GROUP BY sentiment_label;

-- Category performance
SELECT metadata->>'category' as category, 
       AVG(engagement_score) as avg_engagement,
       COUNT(*) as hashtag_count
FROM tiktok 
WHERE scraped_at >= NOW() - INTERVAL '7 days'
GROUP BY metadata->>'category'
ORDER BY avg_engagement DESC;
```

## 🔧 Advanced Configuration

### Navigation Fix Settings
The scraper includes multiple strategies to ensure proper navigation to hashtags:

```python
# Navigation strategies in order of execution:
# 1. Direct URL navigation to hashtags page
# 2. Find and click hashtags navigation element  
# 3. JavaScript-based navigation
# 4. Fallback with warning if all fail
```

### View More Button Detection
Enhanced detection with multiple strategies:

```python
# Button detection strategies:
# 1. Direct text matching ("View More", "Load More")
# 2. Comprehensive button scanning
# 3. Force click with JavaScript fallback
# 4. Page height monitoring for success verification
```

## 📝 Logging & Debugging

### Debug Features
- **HTML Page Source**: Saves debug HTML files when `debug=True`
- **Screenshot Capture**: Takes screenshots when buttons aren't found
- **Detailed Console Output**: Step-by-step progress logging
- **Element Text Analysis**: Shows extracted text for debugging

### Log Levels
- **INFO**: Navigation and scraping progress
- **WARNING**: Non-critical issues (failed navigation attempts)
- **ERROR**: Critical errors (connection failures, parsing errors)
- **DEBUG**: Detailed element analysis and extraction details

## 🚨 Error Handling

### V7 Enhanced Error Handling
- **Navigation Failures**: Multiple fallback strategies
- **Button Detection Failures**: Aggressive retry mechanisms  
- **Song Title Filtering**: Prevents extracting music titles as hashtags
- **Network Issues**: Graceful timeout handling
- **Database Errors**: Detailed error reporting with stack traces

## 🔧 Troubleshooting

### Common Issues

**1. Playwright browser not installed**
```bash
Error: Executable doesn't exist at ...
Solution: playwright install chromium
```

**2. NLTK/TextBlob data missing**
```bash
Error: Resource punkt not found
Solution: python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
```

**3. Supabase connection failed**
```bash
Error: Failed to initialize Supabase client
Solution: Check SUPABASE_URL and SUPABASE_KEY in base.py
```

**4. No hashtags scraped**
- Enable debug mode: `debug=True`
- Check if View More button was found in logs
- Try increasing `scrolls` parameter
- Run with `headless=False` to see browser behavior

**5. Song titles appearing as hashtags**
- This is filtered automatically in V7
- Check logs for "Song title filtered" messages
- Verify song title keywords in categorize_hashtag() function

### Debug Mode

When `debug=True`, the scraper will:
- Save HTML page source to `debug_page.html`
- Print detailed element extraction info
- Show all found hashtag candidates
- Log View More button detection attempts

## 🔒 Security & Privacy

### Security Best Practices
- **Never commit credentials**: Add `.env` to `.gitignore`
- **Use environment variables**: Store `SUPABASE_URL` and `SUPABASE_KEY` securely
- **Row Level Security**: Enable RLS policies in Supabase for access control
- **API Key Rotation**: Periodically rotate Supabase anon keys

### Anti-Detection Measures
- Built-in delays between scrolls
- Random user agent rotation (if implemented)
- Headless mode for stealth operation
- Respects website's robots.txt and terms of service

⚠️ **Disclaimer**: Use this tool responsibly and in compliance with TikTok's Terms of Service. The scraper is for educational and research purposes only.

## 📊 Performance Tips

### Optimization Strategies
1. **Increase Scrolls**: Set `scrolls=20` or higher for maximum data collection
2. **Headless Mode**: Use `headless=True` for faster execution (no GUI overhead)
3. **Delay Tuning**: Reduce `delay` for faster scraping (risk: detection), increase for stealth
4. **Batch Processing**: Use `version_id` to track scraping sessions
5. **Database Indexing**: Create indexes on `topic`, `scraped_at`, `engagement_score`

### Best Practices
- Run during off-peak hours for better reliability
- Use headless mode for automated/scheduled runs
- Enable debug mode only when troubleshooting
- Monitor CSV files to verify data quality
- Regularly clean old data from Supabase

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the logs for error details
2. Review the configuration settings
3. Test individual components separately
4. Create an issue with detailed information

## 🔄 Version History

### V7 (Current) - Complete Production Version
- ✅ **Fixed Navigation**: Aggressive navigation to hashtags page
- ✅ **Enhanced View More Detection**: Multiple strategies for button detection
- ✅ **Song Title Filtering**: Intelligent filtering to avoid music titles
- ✅ **Clean Data Schema**: Proper numeric type conversion (posts, views)
- ✅ **Supabase Integration**: Direct database upload with UUID session tracking
- ✅ **Sentiment Analysis**: TextBlob-based sentiment scoring
- ✅ **Engagement Scoring**: Advanced 1-10 scale scoring algorithm
- ✅ **CSV Export**: Timestamped CSV file generation
- ✅ **Debug Mode**: HTML saving and detailed logging
- ✅ **Error Handling**: Comprehensive error recovery mechanisms

### Previous Versions
- **V6**: Enhanced View More button detection and error handling  
- **V5**: Playwright integration, proxy rotation, enhanced schema
- **V4**: Selenium-based with "View More" button detection
- **V3**: Basic scraping with engagement scoring
- **V2**: Initial Supabase integration
- **V1**: Basic hashtag extraction

## 🎯 Project Structure

```
e:\tik tok ampify\
├── base.py                 # Main scraper (V7 Complete)
├── base copy.py            # Backup/alternate version
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── tiktok_hashtags_*.csv  # Generated CSV outputs
└── venv/                  # Virtual environment (not in git)
```

## 🚀 Quick Start

1. **Clone and setup**
   ```bash
   git clone https://github.com/Aditya0611/tik-tok_trending_hashtags.git
   cd tik-tok_trending_hashtags
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Configure Supabase (optional)**
   ```bash
   # Edit base.py and update:
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```

3. **Run locally**
   ```bash
   python -c "import asyncio; from base import test_fixed_scraper; asyncio.run(test_fixed_scraper())"
   ```

4. **View results**
   - Check generated CSV files: `tiktok_hashtags_YYYYMMDD_HHMMSS.csv`
   - Query Supabase dashboard (if configured)
   - Review console logs for scraping details
