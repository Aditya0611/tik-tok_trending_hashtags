#!/usr/bin/env python3
"""
TikTok Hashtag Scraper V9 - Improved Reliability
"""

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timezone
import os
import re
from textblob import TextBlob
from supabase import create_client, Client
import uuid
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def init_supabase():
    """Initialize Supabase client"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            print("WARNING: SUPABASE_URL or SUPABASE_KEY environment variables not set")
            return None
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        return None

def convert_to_numeric(value: str) -> Optional[int]:
    """Convert string values like '1.2K', '5M' to numeric integers"""
    if not value or value == "N/A":
        return None
    
    try:
        clean_value = str(value).replace(',', '').replace(' ', '').upper()
        
        if 'K' in clean_value:
            number = float(clean_value.replace('K', ''))
            return int(number * 1000)
        elif 'M' in clean_value:
            number = float(clean_value.replace('M', ''))
            return int(number * 1000000)
        else:
            return int(float(clean_value))
    except (ValueError, TypeError):
        return None

def upload_to_supabase(supabase, hashtag_data, table_name="tiktok", version_id=None):
    """Upload hashtag data to Supabase"""
    try:
        print(f"\nUploading {len(hashtag_data)} hashtags to Supabase...")
        
        if not version_id:
            version_id = str(uuid.uuid4())
        
        upload_data = []
        for idx, item in enumerate(hashtag_data):
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
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "version_id": version_id
            }
            
            upload_data.append(upload_item)
        
        print(f"Inserting {len(upload_data)} records into '{table_name}'...")
        result = supabase.table(table_name).insert(upload_data).execute()
        
        if result.data:
            print(f"Successfully uploaded {len(result.data)} records")
            print(f"Version ID: {version_id}")
            return True
        else:
            print(f"Upload completed but no data returned")
            return False
            
    except Exception as e:
        print(f"Failed to upload to Supabase: {e}")
        import traceback
        traceback.print_exc()
        return False

async def wait_for_page_load(page, max_wait=60):
    """Wait for page to fully load with multiple checks"""
    print("Waiting for page to load completely...")
    
    # Wait for title to be non-empty
    for i in range(max_wait):
        title = await page.title()
        if title and len(title) > 0:
            print(f"Page title loaded: {title}")
            break
        await asyncio.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"Still waiting... ({i}s)")
    
    # Wait for body element
    try:
        await page.wait_for_selector("body", timeout=30000)
        print("Body element found")
    except PlaywrightTimeout:
        print("WARNING: Timeout waiting for body element")
    
    # Additional wait for JavaScript
    await asyncio.sleep(8)
    
    # Verify hashtag content
    content = await page.content()
    has_hashtag_content = "hashtag" in content.lower()
    print(f"Hashtag content detected: {has_hashtag_content}")
    
    return has_hashtag_content

async def ensure_hashtags_tab(page):
    """Ensure we're on the hashtags tab"""
    print("Checking if we're on hashtags page...")
    
    content = await page.content()
    
    # Check if we're on songs page
    is_on_songs = any(x in content.lower() for x in ['pocketful of sunshine', 'trending songs'])
    
    if is_on_songs:
        print("Currently on songs page, clicking Hashtags tab...")
        try:
            selectors = [
                "text=Hashtags",
                "[data-e2e='hashtag-tab']",
                "button:has-text('Hashtags')",
                "a:has-text('Hashtags')"
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        print(f"Clicked using selector: {selector}")
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        await asyncio.sleep(5)
                        return True
                except:
                    continue
            
            print("WARNING: Could not find Hashtags tab to click")
            return False
        except Exception as e:
            print(f"WARNING: Error clicking Hashtags tab: {e}")
            return False
    else:
        print("Already on hashtags page")
        return True

async def click_view_more_buttons(page, max_clicks=50):
    """Click View More buttons with improved reliability"""
    total_clicks = 0
    consecutive_failures = 0
    
    print(f"Starting to click View More buttons (max: {max_clicks})...")
    
    for attempt in range(1, max_clicks + 1):
        try:
            button = await page.query_selector("text=/view more/i")
            
            if not button:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    logger.info(f"No button found for {consecutive_failures} attempts, stopping")
                    break
                await asyncio.sleep(2)
                continue
            
            is_visible = await button.is_visible()
            
            if not is_visible:
                logger.info(f"Button not visible at attempt {attempt}, stopping")
                break
            
            consecutive_failures = 0
            
            # Scroll button into view
            await button.scroll_into_view_if_needed()
            await asyncio.sleep(1.5)
            
            # Click
            try:
                await button.click(force=True, timeout=5000)
            except:
                await button.evaluate("el => el.click()")
            
            total_clicks += 1
            
            if total_clicks % 10 == 0:
                logger.info(f"Progress: {total_clicks} clicks")
            
            # Wait longer for content to load
            await asyncio.sleep(6)
            
            # Scroll down a bit after each click to help load content
            if total_clicks % 5 == 0:
                await page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.info(f"Error at attempt {attempt}: {e}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                break
    
    print(f"Clicked View More {total_clicks} times")
    return total_clicks

def calculate_engagement_score(hashtag, posts, category, element_text):
    """Calculate engagement score 1-10"""
    try:
        score = 5.0
        
        if posts and posts != "N/A":
            posts_num = convert_to_numeric(posts)
            if posts_num:
                if posts_num >= 1000000:
                    score += 2.0
                elif posts_num >= 500000:
                    score += 1.5
                elif posts_num >= 100000:
                    score += 1.0
                elif posts_num >= 50000:
                    score += 0.5
                elif posts_num < 1000:
                    score -= 1.0
        
        high_engagement_categories = ['Entertainment', 'Music', 'Dance', 'Comedy']
        medium_engagement_categories = ['Sports & Fitness', 'Food & Cooking', 'Fashion & Beauty']
        
        if category in high_engagement_categories:
            score += 1.0
        elif category in medium_engagement_categories:
            score += 0.5
        
        if hashtag:
            hashtag_lower = hashtag.lower()
            trending_keywords = ['viral', 'trending', 'challenge', 'fyp', 'foryou']
            for keyword in trending_keywords:
                if keyword in hashtag_lower:
                    score += 0.5
                    break
            
            if len(hashtag) <= 10:
                score += 0.3
            elif len(hashtag) > 20:
                score -= 0.2
        
        return round(max(1.0, min(10.0, score)), 1)
        
    except:
        return 5.0

def analyze_sentiment(hashtag, element_text):
    """Analyze sentiment"""
    try:
        text = ""
        if hashtag:
            text += hashtag.replace('#', '') + " "
        if element_text:
            text += element_text
        
        if not text.strip():
            return 0.0, "Neutral"
        
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            label = "Positive"
        elif polarity < -0.1:
            label = "Negative"
        else:
            label = "Neutral"
        
        return float(round(polarity, 3)), label
        
    except:
        return 0.0, "Neutral"

async def scrape_with_retry(page, max_retries=2):
    """Scrape with retry logic if too few hashtags found"""
    
    for retry in range(max_retries):
        print(f"\n{'='*60}")
        print(f"SCRAPE ATTEMPT {retry + 1}/{max_retries}")
        print(f"{'='*60}\n")
        
        # Scroll to reveal content
        print("Scrolling to reveal content...")
        for i in range(8):
            await page.evaluate("window.scrollBy(0, 500)")
            await asyncio.sleep(1)
        
        # Click View More buttons
        total_clicks = await click_view_more_buttons(page, max_clicks=50)
        
        # Extended scrolling with pauses
        print("Extended scrolling to load all content...")
        for i in range(15):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)
            
            # Extra View More checks during scrolling
            if i % 5 == 0 and i > 0:
                print(f"Checking for more View More buttons... (scroll {i})")
                extra_clicks = await click_view_more_buttons(page, max_clicks=10)
                if extra_clicks > 0:
                    total_clicks += extra_clicks
        
        # Final wait
        print("Final wait before parsing...")
        await asyncio.sleep(8)
        
        # Parse content
        page_source = await page.content()
        soup = BeautifulSoup(page_source, 'html.parser')
        hashtag_elements = soup.select("[data-testid*='hashtag_item']")
        
        print(f"Found {len(hashtag_elements)} hashtag elements")
        
        # If we got a good number, return
        if len(hashtag_elements) >= 30:
            print("Good collection, proceeding with parsing")
            return hashtag_elements, page_source
        
        # If this is the last retry, accept what we have
        if retry == max_retries - 1:
            print(f"Final attempt - accepting {len(hashtag_elements)} elements")
            return hashtag_elements, page_source
        
        # Otherwise, reload and try again
        print(f"Only found {len(hashtag_elements)} elements, reloading page...")
        await page.reload(wait_until='networkidle', timeout=60000)
        await asyncio.sleep(10)
        await ensure_hashtags_tab(page)
        await asyncio.sleep(5)
    
    return [], ""

async def scrape_tiktok_hashtags(headless=True, debug=True, upload_to_db=True):
    """Main scraping function with improved reliability"""
    url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
    
    scraped_data = []
    seen_hashtags = set()
    version_id = str(uuid.uuid4())
    
    supabase = None
    if upload_to_db:
        supabase = init_supabase()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        # Realistic context
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print(f"Navigating to TikTok Creative Center...")
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Wait for page load
            page_loaded = await wait_for_page_load(page, max_wait=30)
            
            if not page_loaded:
                print("WARNING: Page may not have loaded properly")
            
            print(f"URL: {page.url}")
            print(f"Title: {await page.title()}")
            
            # Ensure hashtags tab
            await ensure_hashtags_tab(page)
            await asyncio.sleep(5)
            
            # Scrape with retry logic
            hashtag_elements, page_source = await scrape_with_retry(page, max_retries=2)
            
            if debug:
                debug_file = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"Debug file saved: {debug_file}")
            
            if not hashtag_elements:
                print("ERROR: No hashtag elements found after retries")
                await context.close()
                await browser.close()
                return []
            
            print(f"\nProcessing {len(hashtag_elements)} elements...")

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
                        r'(\d+)\s*K\s*Posts',
                        r'(\d+)\s*Posts',
                    ]
                    
                    for pattern in posts_patterns:
                        match = re.search(pattern, element_text)
                        if match:
                            posts = match.group(1) + ('K' if 'K' in match.group(0) else '')
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
                        print(f"Error on element {i+1}: {e}")
                    continue

            print(f"\nScraped {len(scraped_data)} unique hashtags")
            
            # Upload
            if upload_to_db and supabase and scraped_data:
                print(f"\n{'='*60}")
                print("UPLOADING TO SUPABASE")
                print(f"{'='*60}")
                success = upload_to_supabase(supabase, scraped_data, "tiktok", version_id)
                if success:
                    print("Upload successful!")
            
            await context.close()
            await browser.close()
            return scraped_data
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            await context.close()
            await browser.close()
            return []

async def run_scraper():
    """Main entry point"""
    print("TIKTOK SCRAPER - GitHub Actions Compatible")
    print("="*60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    
    results = await scrape_tiktok_hashtags(
        headless=True,
        debug=True,
        upload_to_db=True
    )
    
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total hashtags: {len(results)}")
    print(f"Finished: {datetime.now(timezone.utc).isoformat()}")
    print("="*60)
    
    if results:
        print(f"\nSample results:")
        for i, item in enumerate(results[:5], 1):
            print(f"  {i}. {item['hashtag']} - {item['posts']} Posts")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_scraper())