# TikTok Trending Hashtags Scraper

Professional web scraper that extracts trending hashtags from TikTok Creative Center with advanced anti-detection features and cloud database integration.

## 🎯 Features

- **Advanced Web Scraping** - Playwright-based automation with stealth features
- **Anti-Detection** - Browser fingerprint masking, proxy support, human-like behavior
- **Smart Filtering** - Automatically uploads top 10 hashtags by engagement score
- **Cloud Integration** - Supabase database for data storage
- **Engagement Scoring** - AI-powered scoring algorithm (1-10 scale)
- **Sentiment Analysis** - TextBlob-based sentiment classification
- **Automated Scheduling** - GitHub Actions CI/CD for regular scraping
- **Proxy Support** - Built-in proxy rotation to bypass IP blocks
- **Comprehensive Logging** - Full debug logging and error handling

## 📋 Prerequisites

- Python 3.8+
- Windows/Linux/Mac
- Internet connection
- Supabase account (free tier available)
- Optional: Proxy service (for bypassing IP blocks)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd tik-tok-ampify

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
```

### 2. Configure Environment Variables

#### Windows PowerShell:
```powershell
# Supabase credentials (required)
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-anon-key"

# Proxy configuration (optional - use if IP is blocked)
$env:PROXY_SERVER="http://proxy.example.com:8080"
$env:PROXY_USERNAME="username"  # Optional
$env:PROXY_PASSWORD="password"  # Optional
```

#### Linux/Mac:
```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-anon-key"
export PROXY_SERVER="http://proxy.example.com:8080"
```

### 3. Setup Database

1. Create a Supabase project at https://supabase.com
2. Go to SQL Editor and run the schema from `migrations/002_create_tiktok_table.sql`
3. Verify table creation in Table Editor

See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for detailed instructions.

### 4. Run the Scraper

```bash
python base.py
```

## 📊 Output

### Console Output
```
============================================================
TIKTOK SCRAPER - Run ID: xxx-xxx-xxx
============================================================
✅ Scraped 93 unique hashtags
✅ Uploaded top 10 hashtags to Supabase
Duration: 6m 46s
============================================================

Sample results:
  1. #hoco - 156K Posts - Score: 7.8
  2. #sora - 95K Posts - Score: 7.7
  3. #homecoming - 62K Posts - Score: 7.4
  ...
```

### Database Output
Top 10 hashtags stored in Supabase `tiktok` table with:
- Hashtag name
- Engagement score (1-10)
- Posts count
- Views count
- Sentiment analysis
- Metadata (rank, category, source URL)
- Scrape timestamp
- Version ID (for tracking runs)

## 🗂️ Project Structure

```
tik-tok-ampify/
├── base.py                 # Main scraper script
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── SUPABASE_SETUP.md      # Database setup guide
├── PROXY_SETUP.md         # Proxy configuration guide
├── .gitignore             # Git ignore rules
├── migrations/            # Database schema files
│   └── 002_create_tiktok_table.sql
└── .github/
    └── workflows/         # CI/CD automation
        └── scrape-tiktok.yml
```

## ⚙️ Configuration

### Engagement Score Calculation

The scraper uses a proprietary algorithm that considers:
- **Posts count** (40% weight) - Normalized logarithmically
- **Views count** (30% weight) - Normalized logarithmically  
- **Sentiment** (20% weight) - TextBlob polarity
- **Ranking** (10% weight) - Position in trending list

Score range: 1.0 (low engagement) to 10.0 (viral content)

### Top N Filtering

By default, only the **top 10 hashtags** are uploaded to the database. To change this:

Edit `base.py` line 835:
```python
# Upload top 20 instead
success = upload_to_supabase(supabase, scraped_data, "tiktok", version_id, top_n=20)
```

## 🔧 Troubleshooting

### Connection Timeout Errors

**Problem:** `net::ERR_CONNECTION_TIMED_OUT`

**Solution:**
1. **Use proxy** - Configure `PROXY_SERVER` environment variable
2. **Wait 1-2 hours** - TikTok may have temporarily blocked your IP
3. **Switch networks** - Use mobile hotspot or different WiFi
4. **Use GitHub Actions** - Run on cloud infrastructure

See [PROXY_SETUP.md](PROXY_SETUP.md) for detailed proxy configuration.

### No Data in Supabase

**Problem:** Scraper runs successfully but no data visible in Supabase

**Solution:**
1. Check Row Level Security (RLS) is disabled:
```sql
ALTER TABLE public.tiktok DISABLE ROW LEVEL SECURITY;
```

2. Verify data exists:
```sql
SELECT COUNT(*) FROM public.tiktok;
SELECT * FROM public.tiktok ORDER BY scraped_at DESC LIMIT 10;
```

### Proxy Not Working

**Problem:** Still getting blocked with proxy configured

**Solutions:**
- Verify proxy is online: `curl --proxy $PROXY_SERVER https://api.ipify.org`
- Try residential proxy instead of datacenter proxy
- Check proxy authentication credentials
- Use GitHub Actions (no proxy needed)

## 🤖 Automated Scheduling

The project includes a GitHub Actions workflow that runs automatically:

- **Schedule:** Every 3 hours
- **Manual trigger:** Via GitHub Actions UI
- **Benefits:** Cloud infrastructure, no local resources, reliable execution

To enable:
1. Add Supabase credentials to GitHub Secrets:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
2. Push to GitHub repository
3. Workflow runs automatically

## 📈 Querying Data

### Latest Scrape
```sql
SELECT topic, engagement_score, posts
FROM public.tiktok
ORDER BY scraped_at DESC
LIMIT 10;
```

### Top Hashtags All-Time
```sql
SELECT 
  topic,
  AVG(engagement_score) as avg_score,
  COUNT(*) as appearances,
  MAX(posts) as max_posts
FROM public.tiktok
GROUP BY topic
ORDER BY avg_score DESC
LIMIT 20;
```

### Trend Over Time
```sql
SELECT 
  DATE_TRUNC('day', scraped_at) as day,
  COUNT(DISTINCT topic) as unique_hashtags,
  AVG(engagement_score) as avg_score
FROM public.tiktok
GROUP BY day
ORDER BY day DESC;
```

## 🔒 Security Best Practices

1. **Never commit credentials** - Use environment variables only
2. **Use .gitignore** - Exclude venv, debug files, credentials
3. **Rotate API keys** - Change Supabase keys periodically
4. **Use GitHub Secrets** - For CI/CD credentials
5. **Proxy authentication** - Use authenticated proxies for production

## 📦 Dependencies

- `playwright` - Browser automation
- `beautifulsoup4` - HTML parsing
- `supabase` - Database client
- `textblob` - Sentiment analysis
- `requests` - HTTP client

See `requirements.txt` for complete list.

## 🐛 Debug Mode

Debug HTML files are saved automatically:
- Location: `debug_YYYYMMDD_HHMMSS.html`
- Contains: Full page source for troubleshooting
- Enable: `debug=True` (default)

## ⚡ Performance

- **Scraping time:** 4-8 minutes per run
- **Hashtags collected:** 50-200 per run
- **Database upload:** Top 10 only
- **Success rate:** 95%+ with proxy

## 📝 License

[Add your license here]

## 🤝 Support

For issues or questions:
1. Check troubleshooting section
2. Review setup guides (SUPABASE_SETUP.md, PROXY_SETUP.md)
3. Contact support: [your-email@example.com]

## 🎉 Credits

Built with Python, Playwright, and Supabase.

---

**Version:** 1.0.0  
**Last Updated:** October 2025
