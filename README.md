# TikTok Trending Hashtags Scraper

Automated scraper that collects trending TikTok hashtags every 3 hours and stores them in Supabase with sentiment analysis and engagement metrics.

## Features

- **Automated Scraping**: Runs every 3 hours via GitHub Actions
- **Sentiment Analysis**: Uses TextBlob to analyze hashtag sentiment
- **Engagement Scoring**: Calculates engagement scores (1-10) based on posts, views, and category
- **Category Classification**: Automatically categorizes hashtags (Entertainment, Music, Sports, Education, etc.)
- **Cloud Database**: Stores data in Supabase with version tracking
- **Headless Browser**: Uses Playwright for reliable web scraping
- **Zero Cost**: Completely free using GitHub Actions

## Architecture

```
GitHub Actions (Scheduler)
    ↓
Runs Python Scraper (Every 3 Hours)
    ↓
Playwright Browser Automation
    ↓
Scrapes TikTok Creative Center
    ↓
Sentiment Analysis & Categorization
    ↓
Uploads to Supabase Database
```

## Tech Stack

- **Python 3.11**
- **Playwright**: Browser automation
- **BeautifulSoup4**: HTML parsing
- **TextBlob**: Sentiment analysis
- **Pandas**: Data manipulation
- **Supabase**: PostgreSQL database
- **GitHub Actions**: Automation

## Installation

### Prerequisites

- Python 3.11+
- GitHub account
- Supabase account

### Local Setup

1. Clone the repository:
```bash
git clone https://github.com/Aditya0611/tik-tok_trending_hashtags.git
cd tik-tok_trending_hashtags
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

4. Set environment variables:
```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-key"
```

5. Run the scraper:
```bash
python tiktok_scraper.py
```

## Automated Setup (GitHub Actions)

### 1. Fork/Clone this repository

### 2. Add GitHub Secrets

Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Add these secrets:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon/public key

### 3. Enable GitHub Actions

The workflow is configured in `.github/workflows/scrape-tiktok.yml` and will automatically:
- Run every 3 hours (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC)
- Can be manually triggered from the Actions tab

### 4. Monitor Runs

View workflow runs at: `Actions` → `TikTok Scraper - Every 3 Hours`

## Database Schema

The scraper stores data in a Supabase table with this structure:

```sql
CREATE TABLE tiktok (
  id BIGSERIAL PRIMARY KEY,
  platform TEXT DEFAULT 'TikTok',
  topic TEXT NOT NULL,
  engagement_score FLOAT,
  sentiment_polarity FLOAT,
  sentiment_label TEXT,
  posts BIGINT,
  views BIGINT,
  metadata JSONB,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  version_id UUID NOT NULL
);
```

## Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `topic` | TEXT | Hashtag name (e.g., #fyp) |
| `engagement_score` | FLOAT | Calculated score from 1-10 |
| `sentiment_polarity` | FLOAT | Sentiment score from -1 to 1 |
| `sentiment_label` | TEXT | Positive/Neutral/Negative |
| `posts` | BIGINT | Number of posts using hashtag |
| `views` | BIGINT | Total views for hashtag |
| `metadata` | JSONB | Rank, category, source URL |
| `version_id` | UUID | Unique ID for each scrape run |

## Usage Examples

### Query Latest Hashtags
```sql
SELECT topic, engagement_score, sentiment_label, posts
FROM tiktok
ORDER BY scraped_at DESC
LIMIT 20;
```

### Find Top Trending
```sql
SELECT topic, posts, engagement_score
FROM tiktok
WHERE scraped_at >= NOW() - INTERVAL '24 hours'
ORDER BY engagement_score DESC
LIMIT 10;
```

### Sentiment Analysis
```sql
SELECT 
  sentiment_label,
  COUNT(*) as count,
  AVG(engagement_score) as avg_engagement
FROM tiktok
WHERE scraped_at >= NOW() - INTERVAL '24 hours'
GROUP BY sentiment_label;
```

## Customization

### Change Schedule

Edit `.github/workflows/scrape-tiktok.yml`:

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
    # or
    - cron: '0 0 * * *'    # Daily at midnight
```

### Modify Scraping Parameters

Edit `tiktok_scraper.py`:

```python
results = await scrape_tiktok_hashtags_fixed(
    scrolls=20,        # Increase for more hashtags
    delay=5,           # Increase delay between actions
    headless=True,     # Set to False to see browser
    upload_to_db=True
)
```

## Cleanup Old Data

To automatically delete data older than 7 days:

```sql
CREATE OR REPLACE FUNCTION delete_old_tiktok_rows()
RETURNS void AS $$
BEGIN
  DELETE FROM tiktok
  WHERE scraped_at < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule(
  'tiktok-cleanup-daily',
  '0 0 * * *',
  'SELECT delete_old_tiktok_rows();'
);
```

## Troubleshooting

### Workflow Not Running
- Check if Actions are enabled: `Settings` → `Actions` → `Allow all actions`
- Verify workflow file exists: `.github/workflows/scrape-tiktok.yml`

### Scraper Fails
- Check GitHub Actions logs for detailed errors
- Verify Supabase credentials in Secrets
- Ensure Supabase table exists with correct schema

### No Data Uploaded
- Check if `SUPABASE_URL` and `SUPABASE_KEY` secrets are set correctly
- Verify Supabase table permissions (anon role needs INSERT access)

## Cost

**Total: $0/month**

- GitHub Actions: 2,000 free minutes/month
- Scraper usage: ~5-10 minutes per run
- 8 runs/day × 30 days = ~1,200-2,400 minutes/month
- Well within free tier

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for any purpose.

## Disclaimer

This scraper is for educational purposes. Always respect TikTok's Terms of Service and rate limits. The scraper uses publicly available data from TikTok's Creative Center.

## Author

**Aditya**
- GitHub: [@Aditya0611](https://github.com/Aditya0611)

## Acknowledgments

- TikTok Creative Center for providing public trending data
- Playwright team for the excellent browser automation library
- Supabase for the free PostgreSQL database

---

**Last Updated**: October 2025