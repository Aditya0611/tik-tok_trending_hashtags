#!/usr/bin/env python3
"""
TikTok Hashtag Scraper V7 - Complete Fixed Version
"""

import asyncio
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import random
from datetime import datetime, timezone
import os
import re
import requests
from textblob import TextBlob
from supabase import create_client, Client
import uuid
from typing import List, Dict, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Supabase Configuration
SUPABASE_URL = "https://rnrnbbxnmtajjxscawrc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJucm5iYnhubXRhamp4c2Nhd3JjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY4MzI4OTYsImV4cCI6MjA3MjQwODg5Nn0.WMigmhXcYKYzZxjQFmn6p_Y9y8oNVjuo5YJ0-xzY4h4"

def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
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
    """Upload hashtag data to Supabase with proper type conversion"""
    try:
        print(f"📤 Uploading {len(hashtag_data)} hashtags to Supabase...")
        
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
            
            if idx < 3:
                print(f"\n   📝 Item {idx+1}: {item['hashtag']}")
                print(f"      Sentiment Polarity: {sentiment_polarity} (type: {type(sentiment_polarity).__name__})")
                print(f"      Sentiment Label: {sentiment_label}")
                print(f"      Engagement Score: {engagement_score}")
                print(f"      Posts: {posts_numeric}")
            
            upload_data.append(upload_item)
        
        print(f"\n🚀 Inserting {len(upload_data)} records into '{table_name}'...")
        result = supabase.table(table_name).insert(upload_data).execute()
        
        if result.data:
            print(f"✅ Successfully uploaded {len(result.data)} records to Supabase")
            print(f"   Version ID: {version_id}")
            return True
        else:
            print(f"⚠️ Upload completed but no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Failed to upload to Supabase: {e}")
        import traceback
        traceback.print_exc()
        return False

async def force_navigate_to_hashtags(page):
    """Force navigation to hashtags page using multiple strategies"""
    print("🔍 Checking current page content for navigation...")
    initial_content = await page.content()
    
    has_navigation = "hashtags" in initial_content.lower() and "songs" in initial_content.lower()
    is_on_songs = any(indicator in initial_content.lower() for indicator in [
        'pocketful of sunshine', 'natasha bedingfield', 'justin timberlake',
        'trending songs', 'get inspired through songs trending on tiktok'
    ])
    
    if has_navigation and is_on_songs:
        print("🚨 CRITICAL: We're on SONGS page but navigation menu is available!")
        print("🔄 FORCING navigation to Hashtags tab...")
        
        navigation_success = False
        
        try:
            print("📍 Strategy 1: Direct text click on 'Hashtags'")
            hashtag_element = await page.query_selector("text=Hashtags")
            if hashtag_element:
                print("✅ Found Hashtags text element")
                await hashtag_element.click(force=True)
                await page.wait_for_load_state('networkidle', timeout=15000)
                await asyncio.sleep(3)
                
                new_content = await page.content()
                if "pocketful of sunshine" not in new_content.lower():
                    print("✅ Strategy 1 SUCCESS! Navigated away from songs")
                    navigation_success = True
        except Exception as e:
            print(f"⚠️ Strategy 1 failed: {e}")
        
        if not navigation_success:
            try:
                print("📍 Strategy 2: Tab-based navigation")
                tab_selectors = [
                    "[role='tab']:has-text('Hashtags')",
                    ".tab:has-text('Hashtags')",
                    "a:has-text('Hashtags')"
                ]
                
                for selector in tab_selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔍 Found {len(elements)} tab elements with: {selector}")
                        for element in elements:
                            try:
                                element_text = await element.inner_text()
                                if "hashtag" in element_text.lower() and len(element_text.strip()) < 20:
                                    print(f"🎯 Clicking: '{element_text.strip()}'")
                                    await element.click(force=True)
                                    await page.wait_for_load_state('networkidle', timeout=15000)
                                    await asyncio.sleep(3)
                                    
                                    check_content = await page.content()
                                    if "pocketful of sunshine" not in check_content.lower():
                                        print("✅ Strategy 2 SUCCESS!")
                                        navigation_success = True
                                        break
                            except:
                                continue
                        if navigation_success:
                            break
            except Exception as e:
                print(f"⚠️ Strategy 2 failed: {e}")
        
        if navigation_success:
            print("🎉 NAVIGATION SUCCESSFUL! Now on hashtags page")
            return True
        else:
            print("❌ ALL NAVIGATION STRATEGIES FAILED")
            return False
    
    elif is_on_songs:
        print("⚠️ On songs page but no navigation menu found")
        return False
    else:
        print("✅ Appears to be on correct page or navigation not needed")
        return True

async def find_and_click_view_more_aggressive(page, max_attempts=30):
    """AGGRESSIVE button finding - clicks View More buttons"""
    total_clicks = 0
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"🔍 Aggressive search attempt {attempt}/{max_attempts}")
        
        try:
            logger.info("   📍 Strategy 1: Direct text matching")
            view_more_selectors = [
                "text=/view more/i",
                "text=View More",
                "text=View more",
                "text=view more",
            ]
            
            button = None
            for selector in view_more_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        logger.info(f"      ✅ Found with selector: {selector}")
                        break
                except:
                    continue
            
            if button:
                is_visible = await button.is_visible()
                logger.info(f"      Button visible: {is_visible}")
                
                if is_visible:
                    logger.info(f"🎯 Clicking View More (attempt {attempt})")
                    
                    height_before = await page.evaluate("document.body.scrollHeight")
                    await button.scroll_into_view_if_needed()
                    await asyncio.sleep(1)
                    
                    try:
                        await button.click(force=True, timeout=5000)
                    except:
                        await button.evaluate("el => el.click()")
                    
                    total_clicks += 1
                    logger.info(f"✅ Click successful! Total clicks: {total_clicks}")
                    await asyncio.sleep(5)
                    
                    height_after = await page.evaluate("document.body.scrollHeight")
                    if height_after > height_before:
                        logger.info(f"      ✅ Page height increased: {height_before} -> {height_after}")
                    
                    continue
            
            logger.info("   📍 Strategy 2: Checking all buttons")
            all_buttons = await page.query_selector_all("button")
            logger.info(f"      Found {len(all_buttons)} buttons on page")
            
            for idx, btn in enumerate(all_buttons):
                try:
                    btn_text = await btn.inner_text()
                    btn_text_clean = btn_text.strip().lower()
                    
                    if 'view more' in btn_text_clean or 'load more' in btn_text_clean:
                        is_visible = await btn.is_visible()
                        is_enabled = await btn.is_enabled()
                        
                        logger.info(f"      Found potential button: '{btn_text_clean}' (visible: {is_visible}, enabled: {is_enabled})")
                        
                        if is_visible and is_enabled:
                            logger.info(f"🎯 Clicking button: '{btn_text_clean}'")
                            
                            height_before = await page.evaluate("document.body.scrollHeight")
                            await btn.scroll_into_view_if_needed()
                            await asyncio.sleep(1)
                            
                            try:
                                await btn.click(force=True, timeout=5000)
                            except:
                                await btn.evaluate("el => el.click()")
                            
                            total_clicks += 1
                            logger.info(f"✅ Click successful! Total clicks: {total_clicks}")
                            await asyncio.sleep(5)
                            
                            height_after = await page.evaluate("document.body.scrollHeight")
                            if height_after > height_before:
                                logger.info(f"      ✅ Page height increased")
                            
                            break
                except:
                    continue
            else:
                logger.info(f"   ❌ No clickable View More button found in attempt {attempt}")
                if attempt == 1:
                    try:
                        logger.info("📸 Taking diagnostic screenshot...")
                        await page.screenshot(path=f"debug_no_button_{attempt}.png", timeout=10000)
                    except:
                        pass
                break
            
        except Exception as e:
            logger.info(f"   ⚠️ Error in attempt {attempt}: {e}")
            break
    
    logger.info(f"✅ Finished. Total View More clicks: {total_clicks}")
    return total_clicks

def calculate_engagement_score(hashtag, posts, category, element_text):
    """Calculate engagement score from 1-10 based on multiple factors"""
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
            trending_keywords = ['viral', 'trending', 'challenge', 'fyp', 'foryou', 'dance', 'funny']
            for keyword in trending_keywords:
                if keyword in hashtag_lower:
                    score += 0.5
                    break
            
            if len(hashtag) <= 10:
                score += 0.3
            elif len(hashtag) > 20:
                score -= 0.2
        
        score = max(1.0, min(10.0, score))
        return round(score, 1)
        
    except Exception as e:
        return 5.0

def analyze_sentiment(hashtag, element_text):
    """Analyze sentiment using TextBlob"""
    try:
        text_to_analyze = ""
        if hashtag:
            text_to_analyze += hashtag.replace('#', '') + " "
        if element_text:
            text_to_analyze += element_text
        
        if not text_to_analyze.strip():
            return 0.0, "Neutral"
        
        blob = TextBlob(text_to_analyze)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            sentiment_label = "Positive"
        elif polarity < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        return float(round(polarity, 3)), sentiment_label
        
    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        return 0.0, "Neutral"

async def scrape_tiktok_hashtags_fixed(scrolls=15, delay=3, headless=False, output_file=None, debug=True, proxies=None, upload_to_db=True):
    """Fixed TikTok hashtag scraper with improved View More button detection"""
    url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
    
    scraped_data = []
    seen_hashtags = set()
    version_id = str(uuid.uuid4())
    
    supabase = None
    if upload_to_db:
        supabase = init_supabase()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        
        try:
            print(f"🌐 Navigating to TikTok...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            print("⏳ Waiting for initial page load...")
            await asyncio.sleep(10)
            
            print(f"📍 Current URL: {page.url}")
            print(f"📄 Page title: {await page.title()}")
            
            navigation_success = await force_navigate_to_hashtags(page)
            
            if not navigation_success:
                print("⚠️ Navigation failed, but continuing...")
            
            await asyncio.sleep(5)
            
            print("📜 Scrolling down to reveal View More button...")
            for i in range(5):
                await page.evaluate("window.scrollBy(0, 500)")
                await asyncio.sleep(1)
            
            print("🎯 Starting aggressive View More button detection...")
            total_view_more_clicks = await find_and_click_view_more_aggressive(page, max_attempts=30)
            
            print(f"✅ Clicked View More {total_view_more_clicks} times")
            
            print(f"📜 Doing extensive scrolling to load all hashtags...")
            for i in range(20):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
                
                if i % 5 == 0:
                    additional_clicks = await find_and_click_view_more_aggressive(page, max_attempts=5)
                    total_view_more_clicks += additional_clicks
            
            print(f"🎉 Total View More clicks: {total_view_more_clicks}")
            print("🔍 Final wait before parsing...")
            await asyncio.sleep(5)
            
            print("📖 Parsing page content...")
            page_source = await page.content()
            
            if debug:
                debug_file = f"debug_page_source_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"💾 Debug file saved: {debug_file}")
            
            soup = BeautifulSoup(page_source, 'html.parser')
            
            hashtag_selectors = [
                "[data-testid*='hashtag_item']",
                "[data-testid*='hashtag']", 
                "div[class*='rank']",
                "div[class*='card']",
                "tr",
                "li",
            ]
            
            hashtag_elements = []
            used_selector = None
            
            for selector in hashtag_selectors:
                elements = soup.select(selector)
                if elements:
                    hashtag_elements = elements
                    used_selector = selector
                    print(f"✅ Found {len(elements)} elements using: {selector}")
                    break
            
            if not hashtag_elements:
                print("❌ No hashtag elements found with any selector")
                await browser.close()
                return []

            print(f"📊 Processing {len(hashtag_elements)} elements...")

            for i, element in enumerate(hashtag_elements):
                try:
                    element_text = element.get_text(strip=True)
                    
                    if debug and i < 15:
                        print(f"\n🔍 Element {i+1}: '{element_text[:120]}{'...' if len(element_text) > 120 else ''}'")
                    
                    hashtag = None
                    posts = None
                    views = None
                    rank = None
                    category = "General"
                    
                    rank_match = re.search(r'^(\d+)', element_text)
                    if rank_match:
                        rank = int(rank_match.group(1))
                    
                    hashtag_patterns = [
                        r'\d+#\s*([a-zA-Z]+?)(?=[A-Z][a-z])',
                        r'\d+#\s*([a-zA-Z]+?)(?=\d)',
                        r'\d+#\s*([a-zA-Z]+?)(?=[A-Z])',
                        r'\d+#\s*([a-zA-Z]+)',
                        r'#\s*([a-zA-Z]+?)(?=[A-Z][a-z])',
                        r'#\s*([a-zA-Z]+?)(?=\d)',
                        r'#\s*([a-zA-Z]+?)(?=[A-Z])',
                        r'#\s*([a-zA-Z]+)',
                    ]
                    
                    for pattern_idx, pattern in enumerate(hashtag_patterns):
                        match = re.search(pattern, element_text)
                        if match:
                            hashtag_word = match.group(1)
                            
                            song_indicators = [
                                'pocketful', 'sunshine', 'feeling', 'trolls', 'dealing', 'bedingfield', 
                                'timberlake', 'natasha', 'justin', 'dreamworks', 'animation', 'drug'
                            ]
                            is_song_title = any(indicator in hashtag_word.lower() for indicator in song_indicators)
                            
                            if (len(hashtag_word) >= 3 and 
                                hashtag_word.isalpha() and 
                                not is_song_title):
                                hashtag = f"#{hashtag_word}"
                                if debug and i < 10:
                                    print(f"   ✅ Pattern {pattern_idx+1} matched: '{hashtag}' from '{match.group()}'")
                                break
                            elif debug and i < 10:
                                reason = "song title" if is_song_title else "invalid format"
                                print(f"   ❌ Pattern {pattern_idx+1} matched but rejected ({reason}): '{hashtag_word}'")
                    
                    posts_patterns = [
                        r'(\d+)\s*K\s*Posts',
                        r'(\d+)\s*Posts',
                        r'(\d+)Posts',
                        r'Posts?\D*(\d+)',
                    ]
                    
                    for pattern in posts_patterns:
                        match = re.search(pattern, element_text)
                        if match:
                            posts_value = match.group(1)
                            if 'K' in match.group(0):
                                posts = f"{posts_value}K"
                            else:
                                posts = posts_value
                            break
                    
                    if hashtag:
                        hashtag_word = hashtag[1:].lower()
                        
                        category_mappings = {
                            'Education': [
                                'learning', 'education', 'study', 'school', 'college', 'university', 'teacher', 
                                'student', 'lesson', 'tutorial', 'knowledge', 'academic', 'homework', 'exam',
                                'language', 'math', 'science', 'history', 'geography', 'literature', 'physics',
                                'chemistry', 'biology', 'english', 'spanish', 'french', 'german', 'chinese',
                                'japanese', 'korean', 'programming', 'coding', 'computer', 'technology'
                            ],
                            'Entertainment': [
                                'entertainment', 'movie', 'film', 'cinema', 'tv', 'show', 'series', 'netflix',
                                'disney', 'marvel', 'anime', 'cartoon', 'comedy', 'funny', 'humor', 'joke',
                                'meme', 'viral', 'trending', 'celebrity', 'actor', 'actress', 'singer',
                                'musician', 'band', 'concert', 'festival', 'party', 'fun'
                            ],
                            'Music': [
                                'music', 'song', 'sing', 'singing', 'singer', 'musician', 'band', 'album',
                                'concert', 'festival', 'dance', 'dancing', 'dj', 'beat', 'rhythm', 'melody',
                                'guitar', 'piano', 'drums', 'violin', 'instrument', 'audio', 'sound',
                                'spotify', 'playlist', 'cover', 'remix', 'rap', 'hiphop', 'rock', 'pop'
                            ],
                            'Sports & Fitness': [
                                'sports', 'fitness', 'gym', 'workout', 'exercise', 'training', 'health',
                                'football', 'soccer', 'basketball', 'tennis', 'baseball', 'hockey', 'golf',
                                'swimming', 'running', 'cycling', 'yoga', 'pilates', 'crossfit', 'bodybuilding',
                                'skate', 'skating', 'skateboard'
                            ],
                            'Travel': [
                                'travel', 'trip', 'vacation', 'holiday', 'tourism', 'adventure', 'explore',
                                'wanderlust', 'backpacking', 'journey', 'destination', 'malieveld'
                            ],
                            'News & Entertainment': [
                                'news', 'politics', 'current', 'events', 'breaking', 'update', 'report',
                                'journalism', 'media', 'press', 'government', 'election', 'vote', 'democracy'
                            ]
                        }
                        
                        for category_name, keywords in category_mappings.items():
                            if any(keyword in hashtag_word for keyword in keywords):
                                category = category_name
                                break
                    
                    if not hashtag or hashtag in seen_hashtags:
                        continue
                    
                    seen_hashtags.add(hashtag)
                    
                    engagement_score = calculate_engagement_score(hashtag, posts, category, element_text)
                    sentiment_polarity, sentiment_label = analyze_sentiment(hashtag, element_text)
                    
                    hashtag_data = {
                        "rank": rank if rank else "N/A",
                        "hashtag": hashtag,
                        "posts": posts if posts else "N/A",
                        "views": views if views else "N/A",
                        "category": category,
                        "engagement_score": engagement_score,
                        "sentiment_polarity": sentiment_polarity,
                        "sentiment_label": sentiment_label
                    }
                    
                    scraped_data.append(hashtag_data)
                    
                    if debug and i < 10:
                        print(f"   📊 Added: {hashtag} | Posts: {posts} | Category: {category}")
                        print(f"      Sentiment: {sentiment_polarity} ({sentiment_label}) | Engagement: {engagement_score}")
                
                except Exception as e:
                    if debug:
                        print(f"⚠️ Error processing element {i+1}: {e}")
                    continue

            print(f"\n✅ Successfully scraped {len(scraped_data)} unique hashtags")
            
            if upload_to_db and supabase and scraped_data:
                print("\n" + "="*60)
                print("📤 UPLOADING TO SUPABASE")
                print("="*60)
                upload_success = upload_to_supabase(supabase, scraped_data, table_name="tiktok", version_id=version_id)
                if upload_success:
                    print("✅ Data successfully uploaded to Supabase!")
                else:
                    print("❌ Failed to upload to Supabase")
            
            if output_file:
                df = pd.DataFrame(scraped_data)
                df.to_csv(output_file, index=False, encoding='utf-8')
                print(f"💾 Data saved to {output_file}")
            
            await browser.close()
            return scraped_data
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            await browser.close()
            return []

async def test_fixed_scraper():
    """Test the fixed scraper"""
    print("🧪 TESTING FIXED SCRAPER")
    print("=" * 60)
    
    results = await scrape_tiktok_hashtags_fixed(
        scrolls=2,
        delay=2,
        headless=False,
        debug=True,
        proxies=None,
        upload_to_db=True
    )
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 60)
    print(f"Total hashtags found: {len(results)}")
    
    if results:
        print(f"\n📋 Extracted Hashtags:")
        for i, hashtag in enumerate(results, 1):
            print(f"   {i}. {hashtag['hashtag']} - {hashtag['posts']} Posts - {hashtag['category']}")
            print(f"      Sentiment: {hashtag['sentiment_polarity']} ({hashtag['sentiment_label']})")
        
        song_titles = [r['hashtag'] for r in results if any(song in r['hashtag'].lower() for song in ['pocketful', 'feeling', 'drug'])]
        
        if song_titles:
            print(f"\n❌ STILL GETTING SONGS: {song_titles}")
        else:
            print(f"\n✅ SUCCESS! No song titles found - all real hashtags!")
        
        df = pd.DataFrame(results)
        output_file = f"tiktok_hashtags_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\n💾 Results saved to: {output_file}")
    else:
        print(f"\n❌ No hashtags extracted")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_fixed_scraper())