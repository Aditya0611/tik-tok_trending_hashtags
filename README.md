# TikTok Hashtag Scraper V4

A powerful Python-based web scraper that extracts trending hashtags from TikTok's Creative Center with advanced features including engagement scoring, sentiment analysis, and automatic Supabase database integration.

## 🚀 Features

### Core Functionality
- **Multi-URL Strategy**: Scrapes from multiple TikTok Creative Center regions (US, GB, IN, SG)
- **Smart "View More" Detection**: Automatically finds and clicks pagination buttons to load additional content
- **Comprehensive Data Extraction**: Extracts hashtag names, post counts, rankings, and categories
- **Duplicate Prevention**: Automatically removes duplicate hashtags

### Advanced Analytics
- **Engagement Score Calculation**: 1-10 scale scoring based on:
  - Post volume (100+ to 1M+ posts)
  - Category popularity (Entertainment, Music, Gaming get higher scores)
  - Trending keywords (viral, fyp, challenge)
  - Hashtag characteristics (length, engagement indicators)

- **Sentiment Analysis**: Uses TextBlob library to analyze:
  - Sentiment polarity (-1 to 1 scale)
  - Classification (Positive/Negative/Neutral)
  - Combined hashtag and context analysis

- **Smart Categorization**: Automatically categorizes hashtags into 12 major categories:
  - Education, Entertainment, Music, Sports & Fitness
  - Food & Cooking, Fashion & Beauty, Travel, Technology
  - Gaming, Lifestyle, News & Politics, Pets & Animals

### Database Integration
- **Supabase Integration**: Automatic upload to cloud database
- **Local CSV Export**: Backup data storage with timestamps
- **Error Handling**: Robust error recovery and logging

## 📋 Requirements

### Python Dependencies
```
selenium>=4.0.0
undetected-chromedriver>=3.5.0
beautifulsoup4>=4.11.0
pandas>=1.5.0
requests>=2.28.0
textblob>=0.17.0
supabase>=1.0.0
```

### System Requirements
- Python 3.8 or higher
- Chrome browser (latest version recommended)
- Internet connection
- Windows/macOS/Linux support

## 🛠️ Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd tik-tok-ampify
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install selenium undetected-chromedriver beautifulsoup4 pandas requests textblob supabase
   ```

4. **Download TextBlob corpora** (for sentiment analysis)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('brown')"
   ```

## ⚙️ Configuration

### Supabase Setup
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Update the credentials in `base.py`:
   ```python
   SUPABASE_URL = "your-supabase-url"
   SUPABASE_KEY = "your-supabase-anon-key"
   ```

3. Create the database table:
   ```sql
   CREATE TABLE tiktok_hashtags (
       id SERIAL PRIMARY KEY,
       rank INTEGER,
       hashtag TEXT NOT NULL,
       posts TEXT,
       views TEXT,
       category TEXT DEFAULT 'General',
       engagement_score DECIMAL(3,1),
       sentiment_polarity DECIMAL(4,3),
       sentiment_label TEXT DEFAULT 'Neutral',
       scraped_at TIMESTAMP DEFAULT NOW(),
       original_text TEXT
   );
   ```

## 🚀 Usage

### Basic Usage
```bash
python base.py
```

### Configuration Options
Modify the `config` dictionary in the `main()` function:

```python
config = {
    'scrolls': 15,          # Number of scroll attempts
    'delay': 3,             # Delay between scrolls (seconds)
    'headless': False,      # Run browser in background
    'output_file': None,    # Custom output filename
    'debug': True           # Enable debug output
}
```

### Expected Output
```
🚀 TikTok Hashtag Scraper V4 - Focus on View More Buttons
🔗 Initializing Supabase connection...
✅ Supabase client initialized successfully
🌐 Navigating to TikTok...
🎯 Attempting to click button: 'View More'
✅ Successfully scraped 6 unique hashtags
📁 Saved to: tiktok_hashtags_v4_20250913_032300.csv
📤 Uploading data to Supabase...
✅ Data successfully uploaded to Supabase!
```

## 📊 Output Data Structure

### CSV Columns
| Column | Description | Example |
|--------|-------------|---------|
| `rank` | Hashtag ranking position | 2 |
| `hashtag` | Hashtag name with # | #biscoitocut |
| `posts` | Number of posts | 8K |
| `category` | Auto-detected category | General |
| `engagement_score` | 1-10 engagement rating | 6.0 |
| `sentiment_label` | Positive/Negative/Neutral | Neutral |
| `sentiment_polarity` | -1 to 1 sentiment score | 0.0 |
| `scraped_at` | Timestamp | 2025-09-13T03:23:00 |
| `original_text` | Raw extracted text | For debugging |

### Sample Data
```
rank      hashtag posts category  engagement_score sentiment_label
   2 #biscoitocut    8K  General               6.0         Neutral
  91      #iconik   26K  General               6.8         Neutral
 104    #paradise   13K  General               6.8         Neutral
```

## 🔧 Advanced Features

### View More Button Detection
The scraper uses multiple strategies to find pagination buttons:
- Text-based XPath selectors
- Class-based CSS selectors
- Generic button detection with text filtering
- Multiple click methods (regular, JavaScript, ActionChains)

### Engagement Score Algorithm
```python
Base Score: 5.0
+ Post Volume: +0.5 to +2.5 (based on 100+ to 1M+ posts)
+ Category Bonus: +1.0 (Entertainment, Music, Gaming)
+ Trending Keywords: +0.5 (viral, fyp, challenge)
+ Length Factor: +0.3 (short hashtags)
+ Content Indicators: +0.3 (popular, trending words)
Final Score: 1.0 - 10.0
```

### Category Detection
Uses comprehensive keyword matching across:
- Hashtag text analysis
- Context text analysis
- 12 predefined categories with 20+ keywords each

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Errors**
```
Solution: Update Chrome browser or try different version_main values
```

**Network Timeouts**
```
Solution: Check internet connection, try VPN, increase timeout values
```

**No Hashtags Found**
```
Solution: Check debug HTML files, verify TikTok site structure
```

**Supabase Upload Fails**
```
Solution: Verify credentials, check table schema, review error logs
```

### Debug Files
The scraper generates debug files for troubleshooting:
- `debug_page_source_v4_TIMESTAMP.html` - Full page source
- `tiktok_hashtags_v4_TIMESTAMP.csv` - Extracted data

## 📁 File Structure
```
tik-tok-ampify/
├── base.py                 # Main scraper script
├── README.md              # This documentation
├── venv/                  # Virtual environment
├── *.csv                  # Output data files
└── debug_*.html          # Debug files
```

## 🔄 Version History

- **V4**: Focus on "View More" button detection and improved extraction
- **V3**: Multi-URL strategy and enhanced scrolling
- **V2**: Basic hashtag extraction with data-testid selectors
- **V1**: Initial implementation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please respect TikTok's terms of service and rate limits.

## ⚠️ Disclaimer

This scraper is designed for research and educational purposes. Users are responsible for complying with TikTok's terms of service and applicable laws. The authors are not responsible for any misuse of this tool.

---

**Last Updated**: September 2025  
**Version**: 4.0  
**Compatibility**: Python 3.8+, Chrome Latest
