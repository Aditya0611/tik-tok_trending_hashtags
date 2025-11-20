#!/usr/bin/env python3
"""
TikTok Hashtag Scraper V10 - Production Ready
Enhanced with centralized selectors, exponential backoff, structured logging,
hardened utilities, log-scaled scoring, and comprehensive testing.
"""

import asyncio
import random
import math
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import os
import re
from supabase import create_client, Client
import uuid
from typing import Optional, List, Dict, Any
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Centralized selector configuration with fallbacks
SELECTORS = {
    'hashtag_tab': [
        "text=Hashtags",
        "[data-e2e='hashtag-tab']",
        "button:has-text('Hashtags')",
        "a:has-text('Hashtags')",
        "[role='tab']:has-text('Hashtag')"
    ],
    'view_more_button': [
        "text=/view more/i",
        "button:has-text('View more')",
        "[data-e2e='view-more-button']",
        ".view-more-btn"
    ],
    'hashtag_item': [
        "[data-testid*='hashtag_item']",
        "[data-e2e*='hashtag']",
        ".hashtag-item",
        "[class*='HashtagItem']"
    ],
    'body': ['body']
}

# Configuration constants
MAX_VIEW_MORE_CLICKS = 25  # Cap to avoid infinite loops
MIN_WAIT_SEC = 2.0  # Minimum wait between actions
MAX_WAIT_SEC = 5.0  # Maximum wait between actions
MAX_RETRIES = 3  # Number of retry attempts
BASE_BACKOFF_SEC = 2.0  # Base backoff for exponential retry
CHUNK_SIZE = 50  # Chunk size for Supabase upserts

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Proxy Configuration (optional)
PROXY_SERVER = os.environ.get("PROXY_SERVER")  # e.g., "http://proxy.example.com:8080"
PROXY_USERNAME = os.environ.get("PROXY_USERNAME")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")

# Alternate URLs to try if primary fails
ALTERNATE_URLS = [
    "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/{region}",
    "https://www.tiktok.com/business/en/inspiration/popular/hashtag/pc/{region}",
]

def jittered_wait(min_sec: float = MIN_WAIT_SEC, max_sec: float = MAX_WAIT_SEC) -> float:
    """Return a random wait time with jitter to mimic human behavior."""
    wait_time = random.uniform(min_sec, max_sec)
    return wait_time

def init_supabase():
    """Initialize Supabase client"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("SUPABASE_URL or SUPABASE_KEY environment variables not set")
            return None
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def convert_to_numeric(value: str) -> Optional[int]:
    """Convert string values like '1.2K', '5.3M', '2.1B' to numeric integers.
    
    Handles:
    - K/M/B suffixes with decimals (e.g., '1.5K', '2.3M', '1.1B')
    - Stray symbols like commas, spaces, currency symbols
    - Various edge cases and malformed input
    
    Args:
        value: String representation of a number (e.g., '1.2K', '$5.3M', '2,300')
    
    Returns:
        Integer representation or None if conversion fails
    """
    if not value or value == "N/A":
        return None
    
    try:
        # Remove common stray symbols and whitespace
        clean_value = str(value).strip()
        # Remove currency symbols, commas, parentheses, etc.
        clean_value = re.sub(r'[^0-9.KMBkmb-]', '', clean_value)
        clean_value = clean_value.upper()
        
        if not clean_value:
            return None
        
        # Handle K, M, B suffixes
        multiplier = 1
        if 'B' in clean_value:
            multiplier = 1_000_000_000
            clean_value = clean_value.replace('B', '')
        elif 'M' in clean_value:
            multiplier = 1_000_000
            clean_value = clean_value.replace('M', '')
        elif 'K' in clean_value:
            multiplier = 1_000
            clean_value = clean_value.replace('K', '')
        
        # Convert to float first to handle decimals, then to int
        number = float(clean_value)
        return int(number * multiplier)
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Failed to convert '{value}' to numeric: {e}")
        return None

def upload_to_supabase(supabase, hashtag_data, table_name="tiktok", version_id=None, top_n=10):
    """Upload top N hashtags to Supabase with chunked inserts.
    
    Performs inserts in chunks to avoid overwhelming the database.
    Only uploads the top N hashtags sorted by engagement score.
    
    Args:
        supabase: Supabase client
        hashtag_data: List of hashtag dictionaries
        table_name: Database table name
        version_id: Session ID for this run
        top_n: Number of top hashtags to upload (default: 10)
    """
    try:
        # Sort by engagement score and take top N
        sorted_data = sorted(hashtag_data, key=lambda x: x.get('engagement_score', 0), reverse=True)
        top_hashtags = sorted_data[:top_n]
        
        logger.info(f"Uploading top {len(top_hashtags)} hashtags (from {len(hashtag_data)} total) to Supabase")
        
        if not version_id:
            version_id = str(uuid.uuid4())
        
        current_time = datetime.now(timezone.utc)
        
        upload_data = []
        for idx, item in enumerate(top_hashtags):
            posts_numeric = convert_to_numeric(item.get("posts", "N/A"))
            views_numeric = convert_to_numeric(item.get("views", "N/A"))
            
            sentiment_polarity = item.get("sentiment_polarity", 0.0)
            if isinstance(sentiment_polarity, str):
                sentiment_polarity = float(sentiment_polarity)
            
            sentiment_label = item.get("sentiment_label", "Neutral")
            
            engagement_score = item.get("engagement_score", 5.0)
            if isinstance(engagement_score, str):
                engagement_score = float(engagement_score)
            
            metadata = {
                "rank": item.get("rank", "N/A"),
                "category": item.get("category", "General"),
                "source_url": "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
            }
            
            upload_item = {
                "platform": "TikTok",
                "topic": item["hashtag"],
                "engagement_score": engagement_score,
                "sentiment_polarity": sentiment_polarity,
                "sentiment_label": sentiment_label,
                "posts": posts_numeric,
                "views": views_numeric,
                "metadata": metadata,
                "scraped_at": current_time.isoformat(),
                "version_id": version_id
            }
            
            upload_data.append(upload_item)
        
        # Perform chunked inserts
        total_uploaded = 0
        for i in range(0, len(upload_data), CHUNK_SIZE):
            chunk = upload_data[i:i + CHUNK_SIZE]
            logger.info(f"Inserting chunk {i//CHUNK_SIZE + 1}/{(len(upload_data)-1)//CHUNK_SIZE + 1} ({len(chunk)} records)")
            
            try:
                result = supabase.table(table_name).insert(chunk).execute()
                
                if result.data:
                    total_uploaded += len(result.data)
                    logger.debug(f"Chunk inserted successfully: {len(result.data)} records")
            except Exception as chunk_error:
                logger.error(f"Failed to insert chunk {i//CHUNK_SIZE + 1}: {chunk_error}")
                # Continue with next chunk instead of failing entirely
                continue
        
        logger.info(f"Successfully uploaded {total_uploaded} records total")
        logger.info(f"Version ID: {version_id}")
        return total_uploaded > 0
            
    except Exception as e:
        logger.error(f"Failed to upload to Supabase: {e}", exc_info=True)
        return False

async def wait_for_page_load(page, max_wait=60):
    """Wait for page to fully load with multiple checks"""
    logger.info("Waiting for page to load completely...")
    
    # Wait for title to be non-empty
    for i in range(max_wait):
        title = await page.title()
        if title and len(title) > 0:
            logger.info(f"Page title loaded: {title}")
            break
        await asyncio.sleep(1)
        if i % 10 == 0 and i > 0:
            logger.info(f"Still waiting... ({i}s)")
    
    # Wait for body element with fallbacks
    for selector in SELECTORS['body']:
        try:
            await page.wait_for_selector(selector, timeout=30000)
            logger.info("Body element found")
            break
        except PlaywrightTimeout:
            logger.warning(f"Timeout waiting for body element with selector: {selector}")
            continue
    
    # Additional wait for JavaScript with jitter
    wait_time = jittered_wait(3.0, 6.0)
    await asyncio.sleep(wait_time)
    
    # Verify hashtag content
    content = await page.content()
    has_hashtag_content = "hashtag" in content.lower()
    logger.info(f"Hashtag content detected: {has_hashtag_content}")
    
    return has_hashtag_content

async def ensure_hashtags_tab(page):
    """Ensure we're on the hashtags tab using centralized selectors with fallbacks"""
    logger.info("Checking if we're on hashtags page...")
    
    content = await page.content()
    
    # Check if we're on songs page
    is_on_songs = any(x in content.lower() for x in ['pocketful of sunshine', 'trending songs'])
    
    if is_on_songs:
        logger.info("Currently on songs page, clicking Hashtags tab...")
        try:
            # Use centralized selectors with fallbacks
            for selector in SELECTORS['hashtag_tab']:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        logger.info(f"Clicked Hashtags tab using selector: {selector}")
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        wait_time = jittered_wait(3.0, 6.0)
                        await asyncio.sleep(wait_time)
                        return True
                except Exception as e:
                    logger.debug(f"Failed with selector {selector}: {e}")
                    continue
            
            logger.warning("Could not find Hashtags tab to click after trying all selectors")
            return False
        except Exception as e:
            logger.error(f"Error clicking Hashtags tab: {e}")
            return False
    else:
        logger.info("Already on hashtags page")
        return True

async def click_view_more_buttons(page, max_clicks=MAX_VIEW_MORE_CLICKS):
    """Click View More buttons with capped clicks and jittered waits.
    
    Uses centralized selectors with fallbacks and human-like timing.
    """
    total_clicks = 0
    consecutive_failures = 0
    
    logger.info(f"Starting to click View More buttons (max: {max_clicks})...")
    
    for attempt in range(1, max_clicks + 1):
        try:
            button = None
            # Try each selector until we find a button
            for selector in SELECTORS['view_more_button']:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        logger.debug(f"Found View More button with selector: {selector}")
                        break
                except:
                    continue
            
            if not button:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.info(f"No button found for {consecutive_failures} attempts, stopping")
                    break
                wait_time = jittered_wait(1.5, 3.0)
                await asyncio.sleep(wait_time)
                continue
            
            is_visible = await button.is_visible()
            
            if not is_visible:
                logger.info(f"Button not visible at attempt {attempt}, stopping")
                break
            
            consecutive_failures = 0
            
            # Scroll button into view with jitter
            await button.scroll_into_view_if_needed()
            wait_time = jittered_wait(0.8, 1.5)
            await asyncio.sleep(wait_time)
            
            # Click with fallback
            try:
                await button.click(force=True, timeout=5000)
            except:
                await button.evaluate("el => el.click()")
            
            total_clicks += 1
            
            if total_clicks % 10 == 0:
                logger.info(f"Progress: {total_clicks} clicks")
            
            # Wait for content to load with jitter
            wait_time = jittered_wait(4.0, 7.0)
            await asyncio.sleep(wait_time)
            
            # Scroll down periodically to help load content
            if total_clicks % 5 == 0:
                await page.evaluate("window.scrollBy(0, 300)")
                wait_time = jittered_wait(1.5, 3.0)
                await asyncio.sleep(wait_time)
                
        except Exception as e:
            logger.debug(f"Error at attempt {attempt}: {e}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                break
    
    logger.info(f"Clicked View More {total_clicks} times")
    return total_clicks

def calculate_engagement_score(hashtag: str, posts: str, category: str, element_text: str) -> float:
    """Calculate engagement score (1-10) using log-scaling to resist outliers.
    
    Uses logarithmic transformation of post counts to prevent extreme values
    from dominating the score. Final score is clamped between 1.0 and 10.0.
    
    Args:
        hashtag: The hashtag text
        posts: Post count as string (e.g., '1.5K', '2.3M')
        category: Category of the hashtag
        element_text: Full text of the element
    
    Returns:
        Float between 1.0 and 10.0
    """
    try:
        base_score = 5.0
        
        # Log-scaled post count contribution
        if posts and posts != "N/A":
            posts_num = convert_to_numeric(posts)
            if posts_num and posts_num > 0:
                # Use log10 to scale: log10(1000) = 3, log10(1M) = 6, log10(1B) = 9
                # Scale to contribute roughly 0-4 points
                log_posts = math.log10(posts_num)
                post_score = min(4.0, log_posts / 2.0)  # Cap at 4 points
                base_score += post_score
        
        # Category bonus (smaller impact)
        high_engagement_categories = ['Entertainment', 'Music', 'Dance', 'Comedy']
        medium_engagement_categories = ['Sports & Fitness', 'Food & Cooking', 'Fashion & Beauty']
        
        if category in high_engagement_categories:
            base_score += 0.5
        elif category in medium_engagement_categories:
            base_score += 0.3
        
        # Hashtag characteristics
        if hashtag:
            hashtag_lower = hashtag.lower()
            trending_keywords = ['viral', 'trending', 'challenge', 'fyp', 'foryou']
            for keyword in trending_keywords:
                if keyword in hashtag_lower:
                    base_score += 0.3
                    break
            
            # Short hashtags are often more memorable
            if len(hashtag) <= 10:
                base_score += 0.2
            elif len(hashtag) > 25:
                base_score -= 0.2
        
        # Clamp between 1.0 and 10.0
        final_score = max(1.0, min(10.0, base_score))
        return round(final_score, 1)
        
    except Exception as e:
        logger.debug(f"Error calculating engagement score: {e}")
        return 5.0

def analyze_sentiment(hashtag: str, element_text: str) -> tuple[float, str]:
    """Return deterministic sentiment placeholder.
    
    TODO: Replace with VADER for language-aware sentiment scoring.
    For now, returns neutral sentiment to avoid TextBlob dependency and
    ensure consistent, predictable results.
    
    Args:
        hashtag: The hashtag text
        element_text: Full text of the element
    
    Returns:
        Tuple of (polarity: float, label: str)
    """
    # Deterministic placeholder - all hashtags are neutral for now
    # This will be replaced with VADER sentiment analysis later
    return 0.0, "Neutral"

async def scrape_with_retry(page, max_retries=2):
    """Scrape with retry logic if too few hashtags found"""
    
    for retry in range(max_retries):
        logger.info(f"\n{'='*60}")
        logger.info(f"SCRAPE ATTEMPT {retry + 1}/{max_retries}")
        logger.info(f"{'='*60}\n")
        
        # Scroll to reveal content with jitter
        logger.info("Scrolling to reveal content...")
        for i in range(8):
            await page.evaluate("window.scrollBy(0, 500)")
            wait_time = jittered_wait(0.8, 1.5)
            await asyncio.sleep(wait_time)
        
        # Click View More buttons (capped at MAX_VIEW_MORE_CLICKS)
        total_clicks = await click_view_more_buttons(page)
        
        # Extended scrolling with pauses
        logger.info("Extended scrolling to load all content...")
        for i in range(15):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            wait_time = jittered_wait(1.2, 2.0)
            await asyncio.sleep(wait_time)
            
            # Extra View More checks during scrolling
            if i % 5 == 0 and i > 0:
                logger.info(f"Checking for more View More buttons... (scroll {i})")
                extra_clicks = await click_view_more_buttons(page, max_clicks=10)
                if extra_clicks > 0:
                    total_clicks += extra_clicks
        
        # Final wait with jitter
        logger.info("Final wait before parsing...")
        wait_time = jittered_wait(5.0, 8.0)
        await asyncio.sleep(wait_time)
        
        # Parse content using centralized selectors
        page_source = await page.content()
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Try each selector until we find hashtag elements
        hashtag_elements = []
        for selector in SELECTORS['hashtag_item']:
            hashtag_elements = soup.select(selector)
            if hashtag_elements:
                logger.debug(f"Found elements using selector: {selector}")
                break
        
        logger.info(f"Found {len(hashtag_elements)} hashtag elements")
        
        # If we got a good number, return
        if len(hashtag_elements) >= 30:
            logger.info("Good collection, proceeding with parsing")
            return hashtag_elements, page_source
        
        # If this is the last retry, accept what we have
        if retry == max_retries - 1:
            logger.info(f"Final attempt - accepting {len(hashtag_elements)} elements")
            return hashtag_elements, page_source
        
        # Otherwise, reload and try again
        logger.warning(f"Only found {len(hashtag_elements)} elements, reloading page...")
        await page.reload(wait_until='networkidle', timeout=60000)
        wait_time = jittered_wait(8.0, 12.0)
        await asyncio.sleep(wait_time)
        await ensure_hashtags_tab(page)
        wait_time = jittered_wait(3.0, 6.0)
        await asyncio.sleep(wait_time)
    
    return [], ""

async def scrape_single_attempt(browser, url: str, debug: bool = True, use_proxy: bool = False) -> tuple[List[Dict[str, Any]], str]:
    """Perform a single scrape attempt with a fresh browser context.
    
    Returns tuple of (scraped_data, page_source)
    """
    scraped_data = []
    seen_hashtags = set()
    
    # Enhanced browser context with stealth features
    context_options = {
        'viewport': {'width': 1920, 'height': 1080},
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'locale': 'en-US',
        'timezone_id': 'America/New_York',
        'permissions': ['geolocation'],
        'geolocation': {'latitude': 40.7128, 'longitude': -74.0060},  # New York
        'color_scheme': 'light',
        'java_script_enabled': True,
        'bypass_csp': True,
        'ignore_https_errors': True,
        'extra_http_headers': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
    }
    
    # Add proxy if configured and requested
    if use_proxy and PROXY_SERVER:
        proxy_config = {'server': PROXY_SERVER}
        if PROXY_USERNAME and PROXY_PASSWORD:
            proxy_config['username'] = PROXY_USERNAME
            proxy_config['password'] = PROXY_PASSWORD
        context_options['proxy'] = proxy_config
        logger.info(f"Using proxy: {PROXY_SERVER}")
    
    context = await browser.new_context(**context_options)
    page = await context.new_page()
    
    # Add stealth scripts to avoid detection
    await page.add_init_script("""
        // Override the navigator.webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock plugins to appear more realistic
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });
        
        // Add chrome property
        window.chrome = {
            runtime: {}
        };
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
    """)
    
    try:
        logger.info(f"Navigating to TikTok Creative Center...")
        logger.info(f"URL: {url}")
        
        # Add random mouse movements before navigation to appear more human
        try:
            await page.mouse.move(random.randint(100, 300), random.randint(100, 300))
            await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass
        
        # Navigate with increased timeout and networkidle for better reliability
        try:
            await page.goto(url, wait_until='networkidle', timeout=90000)
        except PlaywrightTimeout:
            logger.warning("Timeout with networkidle, trying domcontentloaded...")
            await page.goto(url, wait_until='domcontentloaded', timeout=90000)
        
        # Wait for page load
        page_loaded = await wait_for_page_load(page, max_wait=30)
        
        if not page_loaded:
            logger.warning("Page may not have loaded properly")
        
        logger.info(f"URL: {page.url}")
        logger.info(f"Title: {await page.title()}")
        
        # Ensure hashtags tab
        await ensure_hashtags_tab(page)
        wait_time = jittered_wait(3.0, 6.0)
        await asyncio.sleep(wait_time)
        
        # Scrape with retry logic
        hashtag_elements, page_source = await scrape_with_retry(page, max_retries=2)
        
        if debug:
            debug_file = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info(f"Debug file saved: {debug_file}")
        
        if not hashtag_elements:
            logger.error("No hashtag elements found")
            await context.close()
            return [], ""
        
        logger.info(f"Processing {len(hashtag_elements)} elements...")

        # Process elements
        for i, element in enumerate(hashtag_elements):
            try:
                element_text = element.get_text(strip=True)
                
                # Extract data
                hashtag = None
                posts = None
                rank = None
                category = "General"
                
                # Rank
                rank_match = re.search(r'^(\d+)', element_text)
                if rank_match:
                    rank = int(rank_match.group(1))
                
                # Hashtag
                patterns = [
                    r'\d+#\s*([a-zA-Z]+?)(?=[A-Z][a-z])',
                    r'\d+#\s*([a-zA-Z]+?)(?=\d)',
                    r'\d+#\s*([a-zA-Z]+?)(?=[A-Z])',
                    r'\d+#\s*([a-zA-Z]+)',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, element_text)
                    if match:
                        word = match.group(1)
                        
                        # Filter songs
                        song_words = ['pocketful', 'sunshine', 'feeling', 'trolls']
                        if len(word) >= 3 and word.isalpha() and not any(s in word.lower() for s in song_words):
                            hashtag = f"#{word}"
                            break
                
                # Posts
                posts_patterns = [
                    r'(\d+\.?\d*)\s*[MB]?\s*Posts',  # Support decimals and M/B
                    r'(\d+)\s*K\s*Posts',
                    r'(\d+)\s*Posts',
                ]
                
                for pattern in posts_patterns:
                    match = re.search(pattern, element_text)
                    if match:
                        num = match.group(1)
                        if 'M' in match.group(0):
                            posts = f"{num}M"
                        elif 'B' in match.group(0):
                            posts = f"{num}B"
                        elif 'K' in match.group(0):
                            posts = f"{num}K"
                        else:
                            posts = num
                        break
                
                if not hashtag or hashtag in seen_hashtags:
                    continue
                
                seen_hashtags.add(hashtag)
                
                # Scores
                engagement = calculate_engagement_score(hashtag, posts, category, element_text)
                polarity, sentiment = analyze_sentiment(hashtag, element_text)
                
                scraped_data.append({
                    "rank": rank if rank else "N/A",
                    "hashtag": hashtag,
                    "posts": posts if posts else "N/A",
                    "views": "N/A",
                    "category": category,
                    "engagement_score": engagement,
                    "sentiment_polarity": polarity,
                    "sentiment_label": sentiment
                })
            
            except Exception as e:
                if debug:
                    logger.debug(f"Error on element {i+1}: {e}")
                continue

        logger.info(f"Scraped {len(scraped_data)} unique hashtags")
        await context.close()
        return scraped_data, page_source
        
    except Exception as e:
        logger.error(f"Scrape attempt failed: {e}", exc_info=True)
        await context.close()
        return [], ""

async def scrape_tiktok_hashtags(headless=True, debug=True, upload_to_db=True, region="en"):
    """Main scraping function with exponential backoff and fresh browser contexts.
    
    Uses exponential backoff strategy with fresh browser context per retry
    to avoid state leakage between attempts. Includes proxy support and URL fallbacks.
    """
    version_id = str(uuid.uuid4())
    
    supabase = None
    if upload_to_db:
        supabase = init_supabase()

    async with async_playwright() as p:
        # Launch with additional args for better stealth
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--start-maximized',
                '--disable-extensions',
                '--disable-gpu',
                '--enable-features=NetworkService',
                '--ignore-certificate-errors',
                '--allow-running-insecure-content',
            ]
        )
        
        scraped_data = []
        last_error = None
        
        # Try different URLs and strategies
        urls_to_try = [url.format(region=region) for url in ALTERNATE_URLS]
        
        # Exponential backoff retry logic
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"ATTEMPT {attempt + 1}/{MAX_RETRIES}")
                logger.info(f"{'='*60}")
                
                # Rotate through URLs on each attempt
                url_index = attempt % len(urls_to_try)
                current_url = urls_to_try[url_index]
                logger.info(f"Trying URL {url_index + 1}/{len(urls_to_try)}: {current_url}")
                
                # Use proxy on retry attempts if configured
                use_proxy = (attempt > 0 and PROXY_SERVER is not None)
                
                data, page_source = await scrape_single_attempt(browser, current_url, debug=debug, use_proxy=use_proxy)
                
                if data and len(data) >= 10:  # Success threshold
                    scraped_data = data
                    logger.info(f"Successfully scraped {len(scraped_data)} hashtags")
                    break
                else:
                    logger.warning(f"Attempt {attempt + 1} yielded insufficient data: {len(data)} hashtags")
                    
                    # If this is not the last attempt, wait with exponential backoff
                    if attempt < MAX_RETRIES - 1:
                        backoff_time = BASE_BACKOFF_SEC * (2 ** attempt) + random.uniform(0, 1)
                        logger.info(f"Waiting {backoff_time:.1f}s before retry...")
                        await asyncio.sleep(backoff_time)
                    
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    backoff_time = BASE_BACKOFF_SEC * (2 ** attempt) + random.uniform(0, 1)
                    logger.info(f"Waiting {backoff_time:.1f}s before retry...")
                    await asyncio.sleep(backoff_time)
        
        await browser.close()
        
        # Upload if we have data (top 10 only)
        if upload_to_db and supabase and scraped_data:
            logger.info(f"\n{'='*60}")
            logger.info("UPLOADING TOP 10 HASHTAGS TO SUPABASE")
            logger.info(f"{'='*60}")
            success = upload_to_supabase(supabase, scraped_data, "tiktok", version_id, top_n=10)
            if success:
                logger.info("Upload successful!")
        
        if not scraped_data and last_error:
            raise last_error
        
        return scraped_data

async def run_scraper(platform: str = "TikTok", region: str = "en", headless: bool = True, debug: bool = True, upload_to_db: bool = True):
    """Main entry point with run-level metadata emission.
    
    Args:
        platform: Platform name (default: TikTok)
        region: Region code for scraping (default: en)
        headless: Run browser in headless mode
        debug: Enable debug mode with HTML output
        upload_to_db: Upload results to database
    
    Returns:
        List of scraped hashtag data
    """
    start_time = datetime.now(timezone.utc)
    run_id = str(uuid.uuid4())
    
    # Emit run-level metadata
    run_metadata = {
        "run_id": run_id,
        "platform": platform,
        "region": region,
        "started_at": start_time.isoformat(),
        "headless": headless,
        "debug": debug,
        "upload_to_db": upload_to_db,
        "max_retries": MAX_RETRIES,
        "max_view_more_clicks": MAX_VIEW_MORE_CLICKS
    }
    
    logger.info("="*60)
    logger.info(f"TIKTOK SCRAPER - Run ID: {run_id}")
    logger.info("="*60)
    logger.info(f"Platform: {platform}")
    logger.info(f"Region: {region}")
    logger.info(f"Started: {start_time.isoformat()}")
    logger.info(f"Headless: {headless}, Debug: {debug}, Upload: {upload_to_db}")
    logger.info("="*60)
    
    try:
        results = await scrape_tiktok_hashtags(
            headless=headless,
            debug=debug,
            upload_to_db=upload_to_db,
            region=region
        )
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Emit completion metadata
        logger.info(f"\n{'='*60}")
        logger.info("SCRAPING COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Total hashtags: {len(results)}")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info(f"Finished: {end_time.isoformat()}")
        logger.info("="*60)
        
        if results:
            logger.info(f"\nSample results:")
            for i, item in enumerate(results[:5], 1):
                logger.info(f"  {i}. {item['hashtag']} - {item['posts']} Posts - Score: {item['engagement_score']}")
        
        run_metadata["finished_at"] = end_time.isoformat()
        run_metadata["duration_seconds"] = duration
        run_metadata["total_hashtags"] = len(results)
        run_metadata["status"] = "success"
        
        return results
        
    except Exception as e:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        logger.error(f"\n{'='*60}")
        logger.error("SCRAPING FAILED")
        logger.error(f"{'='*60}")
        logger.error(f"Run ID: {run_id}")
        logger.error(f"Error: {e}")
        logger.error(f"Duration: {duration:.2f}s")
        logger.error("="*60)
        
        run_metadata["finished_at"] = end_time.isoformat()
        run_metadata["duration_seconds"] = duration
        run_metadata["status"] = "failed"
        run_metadata["error"] = str(e)
        
        raise

if __name__ == "__main__":
    asyncio.run(run_scraper())