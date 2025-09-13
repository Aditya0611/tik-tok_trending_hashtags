import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
import pandas as pd
import random
from datetime import datetime
import os
import re
import requests
from textblob import TextBlob
from supabase import create_client, Client

# Supabase Configuration
SUPABASE_URL = "https://rnrnbbxnmtajjxscawrc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJucm5iYnhubXRhamp4c2Nhd3JjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY4MzI4OTYsImV4cCI6MjA3MjQwODg5Nn0.WMigmhXcYKYzZxjQFmn6p_Y9y8oNVjuo5YJ0-xzY4h4"
  # Replace with your Supabase anon key

def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized successfully")
        return supabase
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")
        return None

def upload_to_supabase(supabase, hashtag_data, table_name="tiktok_hashtags"):
    """Upload hashtag data to Supabase"""
    try:
        print(f"📤 Uploading {len(hashtag_data)} hashtags to Supabase...")
        
        # Prepare data for Supabase
        upload_data = []
        for item in hashtag_data:
            upload_item = {
                "rank": int(item["rank"]) if item["rank"] != "N/A" else None,
                "hashtag": item["hashtag"],
                "posts": item["posts"],
                "views": item["views"],
                "category": item["category"],
                "engagement_score": float(item["engagement_score"]) if item["engagement_score"] != "N/A" else None,
                "sentiment_polarity": float(item["sentiment_polarity"]) if item["sentiment_polarity"] != "N/A" else None,
                "sentiment_label": item["sentiment_label"],
                "scraped_at": item["scraped_at"],
                "original_text": item["original_text"]
            }
            upload_data.append(upload_item)
        
        # Insert data into Supabase
        result = supabase.table(table_name).insert(upload_data).execute()
        
        if result.data:
            print(f"✅ Successfully uploaded {len(result.data)} hashtags to Supabase")
            return True
        else:
            print(f"⚠️ Upload completed but no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Failed to upload to Supabase: {e}")
        return False

def test_connection(url):
    """Test if we can reach the URL before using Selenium"""
    try:
        print(f"🔍 Testing connection to: {url}")
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        })
        print(f"✅ Connection test successful: Status {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def find_and_click_view_more_buttons(driver, max_attempts=20):
    """Dedicated function to find and click 'View More' buttons"""
    print("🔍 Searching for 'View More' buttons...")
    total_clicks = 0
    
    for attempt in range(max_attempts):
        try:
            print(f"   Attempt {attempt + 1}/{max_attempts}: Looking for 'View More' buttons...")
            
            # Comprehensive list of selectors for "View More" buttons
            button_selectors = [
                # Text-based XPath selectors
                "//button[contains(text(), 'View More')]",
                "//button[contains(text(), 'view more')]",
                "//button[contains(text(), 'View more')]",
                "//button[contains(text(), 'VIEW MORE')]",
                "//a[contains(text(), 'View More')]",
                "//span[contains(text(), 'View More')]/parent::button",
                "//div[contains(text(), 'View More')]/parent::button",
                "//div[contains(text(), 'View More')]",
                "//span[contains(text(), 'View More')]",
                
                # Additional specific selectors for TikTok
                "//button[contains(@class, 'Button') and contains(text(), 'View More')]",
                "//div[contains(@class, 'button') and contains(text(), 'View More')]",
                "//div[contains(text(), 'View more top hashtags')]",
                "//button[contains(text(), 'Load more')]",
                "//button[contains(text(), 'Show more')]",
                "//div[contains(text(), 'Load more')]",
                "//div[contains(text(), 'Show more')]",
                
                # Class-based selectors
                "//button[contains(@class, 'view-more')]",
                "//button[contains(@class, 'load-more')]",
                "//button[contains(@class, 'show-more')]",
                "//button[contains(@class, 'more-btn')]",
                "//button[contains(@class, 'expand')]",
                "//button[contains(@class, 'Button')]",
                
                # CSS selectors
                "button[class*='view-more']",
                "button[class*='load-more']",
                "button[class*='show-more']",
                "a[class*='view-more']",
                "div[class*='view-more']",
                "div[class*='load-more']",
                
                # Generic button selectors (might catch View More buttons)
                "button",  # All buttons - we'll filter by text
            ]
            
            found_button = None
            used_selector = None
            
            # Try each selector
            for selector in button_selectors:
                try:
                    if selector.startswith('//'):
                        # XPath selector
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector  
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    print(f"      Selector '{selector}' found {len(elements)} elements")
                    
                    if elements:
                        # Check each element
                        for element in elements:
                            try:
                                # Get element text
                                element_text = element.text.strip().lower()
                                
                                # Check if it's a "View More" type button
                                view_more_keywords = ['view more', 'load more', 'show more', 'see more', 'more']
                                
                                if any(keyword in element_text for keyword in view_more_keywords):
                                    if element.is_displayed() and element.is_enabled():
                                        found_button = element
                                        used_selector = selector
                                        print(f"      ✅ Found clickable button with text: '{element.text}'")
                                        break
                                elif selector == "button" and len(element_text) > 0:
                                    # For generic button selector, show all button texts for debugging
                                    print(f"         Button found: '{element_text}'")
                                        
                            except Exception as e:
                                continue
                        
                        if found_button:
                            break
                            
                except Exception as e:
                    print(f"      Error with selector '{selector}': {e}")
                    continue
            
            if found_button:
                try:
                    print(f"🎯 Attempting to click button: '{found_button.text}' using selector: {used_selector}")
                    
                    # Scroll to button
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", found_button)
                    time.sleep(3)
                    
                    # Highlight the button for debugging (optional)
                    driver.execute_script("arguments[0].style.border='3px solid red'", found_button)
                    time.sleep(1)
                    
                    # Try multiple click methods
                    click_successful = False
                    
                    # Method 1: Regular click
                    try:
                        found_button.click()
                        click_successful = True
                        print("      ✅ Regular click successful")
                    except Exception as e:
                        print(f"      ❌ Regular click failed: {e}")
                    
                    # Method 2: JavaScript click
                    if not click_successful:
                        try:
                            driver.execute_script("arguments[0].click();", found_button)
                            click_successful = True
                            print("      ✅ JavaScript click successful")
                        except Exception as e:
                            print(f"      ❌ JavaScript click failed: {e}")
                    
                    # Method 3: ActionChains click
                    if not click_successful:
                        try:
                            ActionChains(driver).move_to_element(found_button).click().perform()
                            click_successful = True
                            print("      ✅ ActionChains click successful")
                        except Exception as e:
                            print(f"      ❌ ActionChains click failed: {e}")
                    
                    if click_successful:
                        total_clicks += 1
                        print(f"🎉 Successfully clicked 'View More' button #{total_clicks}")
                        
                        # Wait for content to load with longer timeout
                        print("⏳ Waiting for new content to load...")
                        time.sleep(8)  # Increased wait time
                        
                        # Scroll down to see if new content appeared
                        old_height = driver.execute_script("return document.body.scrollHeight")
                        driver.execute_script("window.scrollBy(0, 1000);")
                        time.sleep(3)
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        
                        if new_height > old_height:
                            print(f"      ✅ New content loaded (height: {old_height} → {new_height})")
                        else:
                            print(f"      ⚠️ No height change detected")
                        
                        # Continue looking for more buttons
                        continue
                    else:
                        print("      ❌ All click methods failed")
                        break
                        
                except Exception as e:
                    print(f"❌ Error clicking button: {e}")
                    break
            else:
                print(f"🔍 No 'View More' buttons found in attempt {attempt + 1}")
                # Try scrolling to reveal more buttons
                if attempt < max_attempts - 1:
                    print("   📜 Scrolling to look for more buttons...")
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(2)
                else:
                    break
                
        except Exception as e:
            print(f"⚠️ Error in attempt {attempt + 1}: {e}")
            continue
    
    print(f"✅ Finished clicking 'View More' buttons. Total clicks: {total_clicks}")
    return total_clicks

def calculate_engagement_score(hashtag, posts, category, element_text):
    """
    Calculate engagement score from 1-10 based on multiple factors
    """
    try:
        score = 5.0  # Base score
        
        # Factor 1: Posts count (if available)
        if posts and posts != "N/A":
            try:
                posts_str = str(posts).replace(',', '')
                if 'K' in posts_str:
                    posts_num = int(posts_str.replace('K', '')) * 1000
                elif 'M' in posts_str:
                    posts_num = int(posts_str.replace('M', '')) * 1000000
                else:
                    posts_num = int(posts_str)
                
                if posts_num > 1000000:  # 1M+ posts
                    score += 2.5
                elif posts_num > 100000:  # 100K+ posts
                    score += 2.0
                elif posts_num > 10000:   # 10K+ posts
                    score += 1.5
                elif posts_num > 1000:    # 1K+ posts
                    score += 1.0
                elif posts_num > 100:     # 100+ posts
                    score += 0.5
            except:
                pass
        
        # Factor 2: Category popularity (some categories are more engaging)
        high_engagement_categories = ['Entertainment', 'Music', 'Gaming', 'Comedy', 'Dance']
        medium_engagement_categories = ['Fashion & Beauty', 'Food & Cooking', 'Sports & Fitness']
        
        if category in high_engagement_categories:
            score += 1.0
        elif category in medium_engagement_categories:
            score += 0.5
        
        # Factor 3: Hashtag characteristics
        if hashtag:
            hashtag_lower = hashtag.lower()
            # Trending keywords boost engagement
            trending_keywords = ['viral', 'trending', 'challenge', 'fyp', 'foryou', 'dance', 'funny']
            for keyword in trending_keywords:
                if keyword in hashtag_lower:
                    score += 0.5
                    break
            
            # Length factor (shorter hashtags tend to be more memorable)
            if len(hashtag) <= 10:
                score += 0.3
            elif len(hashtag) > 20:
                score -= 0.2
        
        # Factor 4: Text content analysis
        if element_text:
            text_lower = element_text.lower()
            engagement_indicators = ['popular', 'trending', 'viral', 'hot', 'top', 'best']
            for indicator in engagement_indicators:
                if indicator in text_lower:
                    score += 0.3
                    break
        
        # Ensure score is between 1-10
        score = max(1.0, min(10.0, score))
        return round(score, 1)
        
    except Exception as e:
        return 5.0  # Default score if calculation fails

def analyze_sentiment(hashtag, element_text):
    """
    Analyze sentiment using TextBlob
    Returns sentiment polarity (-1 to 1) and classification
    """
    try:
        # Combine hashtag and element text for analysis
        text_to_analyze = ""
        if hashtag:
            text_to_analyze += hashtag.replace('#', '') + " "
        if element_text:
            text_to_analyze += element_text
        
        if not text_to_analyze.strip():
            return 0.0, "Neutral"
        
        # Use TextBlob for sentiment analysis
        blob = TextBlob(text_to_analyze)
        polarity = blob.sentiment.polarity
        
        # Classify sentiment
        if polarity > 0.1:
            sentiment_label = "Positive"
        elif polarity < -0.1:
            sentiment_label = "Negative"
        else:
            sentiment_label = "Neutral"
        
        return round(polarity, 3), sentiment_label
        
    except Exception as e:
        return 0.0, "Neutral"

def scrape_tiktok_hashtags_v4(scrolls=15, delay=3, headless=False, output_file=None, debug=True):
    """
    Version 4: Focus on View More button clicking and improved hashtag extraction
    """
    url = "https://ads.tiktok.com/business/creativecenter/inspiration/popular/hashtag/pc/en"
    
    # Test connection first
    if not test_connection(url):
        print("❌ Cannot reach TikTok website. Check your internet connection or try using a VPN.")
        return []
    
    # Enhanced Chrome options
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
    
    if headless:
        options.add_argument("--headless=new")
    
    driver = None
    scraped_data = []
    seen_hashtags = set()

    try:
        print("🚀 Initializing Chrome driver...")
        driver = uc.Chrome(options=options, version_main=139, use_subprocess=True)
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        print("✅ Chrome driver initialized successfully")
        
        print(f"🌐 Navigating to TikTok...")
        driver.get(url)
        
        # Wait for initial page load
        print("⏳ Waiting for initial page load...")
        time.sleep(15)
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
        # Wait for hashtag content to appear
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid*='hashtag']")))
            print("✅ Initial hashtag content loaded")
        except TimeoutException:
            print("⚠️ No hashtag content detected, but continuing...")
        
        time.sleep(5)
        
        # **PRIMARY FOCUS: Find and click View More buttons**
        total_view_more_clicks = find_and_click_view_more_buttons(driver, max_attempts=20)
        
        # After clicking View More buttons, do some additional scrolling
        if total_view_more_clicks > 0:
            print(f"📜 Doing additional scrolling after {total_view_more_clicks} View More clicks...")
            for i in range(10):  # Reduced scrolling since we clicked View More
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Look for more View More buttons during scrolling
                if i % 3 == 0:
                    try:
                        more_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'View More') or contains(text(), 'view more')]")
                        for btn in more_buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                driver.execute_script("arguments[0].scrollIntoView();", btn)
                                time.sleep(1)
                                driver.execute_script("arguments[0].click();", btn)
                                total_view_more_clicks += 1
                                print(f"✅ Found and clicked additional View More button #{total_view_more_clicks}")
                                time.sleep(3)
                                break
                    except Exception:
                        pass
        else:
            print("⚠️ No View More buttons were clicked, doing regular scrolling...")
            # Do normal scrolling if no View More buttons were found
            for i in range(scrolls):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(delay)
                print(f"📍 Scroll {i + 1}/{scrolls}")
        
        print("🔍 Final wait before parsing...")
        time.sleep(5)

        # Parse with BeautifulSoup
        print("📖 Parsing page content...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        if debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file = f"debug_page_source_v4_{timestamp}.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"💾 Debug file saved: {debug_file}")

        # Find hashtag elements
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
            return []

        print(f"📊 Processing {len(hashtag_elements)} elements...")

        # Enhanced hashtag extraction for the new text patterns
        for i, element in enumerate(hashtag_elements):
            try:
                element_text = element.get_text(strip=True)
                
                if debug and i < 15:
                    print(f"\n🔍 Element {i+1}: '{element_text[:120]}{'...' if len(element_text) > 120 else ''}'")
                
                hashtag = None
                posts = None
                views = None
                rank = None
                category = None
                
                # Extract rank (leading number)
                rank_match = re.search(r'^(\d+)', element_text)
                if rank_match:
                    rank = int(rank_match.group(1))
                
                # Updated hashtag extraction for patterns like:
                # "11# languagelearningEducation954PostsSee analytics"
                # "224# wednesdaynetflixNews & Entertainment308PostsSee analytics"
                hashtag_patterns = [
                    r'\d+#\s*([a-zA-Z]+)',              # "11# languagelearning" -> "languagelearning"
                    r'\d+#([a-zA-Z]+)',                 # "11#languagelearning" -> "languagelearning" 
                    r'#\s*([a-zA-Z]+)',                 # "# languagelearning" -> "languagelearning"
                    r'#([a-zA-Z]+)',                    # "#languagelearning" -> "languagelearning"
                    r'(?:^|\s)([a-zA-Z]{3,}?)(?=\d)',   # Word before digits: "languagelearningEducation954" -> "languagelearningEducation"
                ]
                
                for pattern_idx, pattern in enumerate(hashtag_patterns):
                    match = re.search(pattern, element_text)
                    if match:
                        hashtag_word = match.group(1)
                        if len(hashtag_word) >= 3 and hashtag_word.isalpha():  # Only alphabetic, min 3 chars
                            hashtag = f"#{hashtag_word}"
                            if debug and i < 10:
                                print(f"   ✅ Pattern {pattern_idx+1} matched: '{hashtag}' from '{match.group()}'")
                            break
                        elif debug and i < 10:
                            print(f"   ⚠️ Pattern {pattern_idx+1} matched but invalid: '{hashtag_word}'")
                
                # Extract posts count
                posts_patterns = [
                    r'(\d+)\s*K\s*Posts',                   # "7K Posts"
                    r'(\d+)\s*Posts',                       # "954 Posts" or "897 Posts"
                    r'(\d+)Posts',                          # "954Posts"
                    r'Posts?\D*(\d+)',                      # "Posts954" or "Posts 954"
                ]
                
                for pattern in posts_patterns:
                    match = re.search(pattern, element_text)
                    if match:
                        posts_value = match.group(1)
                        # Handle K notation
                        if 'K' in match.group(0):
                            posts = f"{posts_value}K"
                        else:
                            posts = posts_value
                        break
                
                # Extract category (improved logic)
                category = "General"  # Default category
                
                if hashtag:
                    hashtag_word = hashtag[1:].lower()  # Remove # and convert to lowercase
                    
                    # Define comprehensive category mappings
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
                            'musician', 'band', 'concert', 'festival', 'party', 'fun', 'entertainment'
                        ],
                        'Music': [
                            'music', 'song', 'sing', 'singing', 'singer', 'musician', 'band', 'album',
                            'concert', 'festival', 'dance', 'dancing', 'dj', 'beat', 'rhythm', 'melody',
                            'guitar', 'piano', 'drums', 'violin', 'instrument', 'audio', 'sound',
                            'spotify', 'playlist', 'cover', 'remix', 'rap', 'hiphop', 'rock', 'pop',
                            'jazz', 'classical', 'country', 'electronic', 'edm'
                        ],
                        'Sports & Fitness': [
                            'sports', 'fitness', 'gym', 'workout', 'exercise', 'training', 'health',
                            'football', 'soccer', 'basketball', 'tennis', 'baseball', 'hockey', 'golf',
                            'swimming', 'running', 'cycling', 'yoga', 'pilates', 'crossfit', 'bodybuilding',
                            'weightlifting', 'cardio', 'marathon', 'athlete', 'competition', 'olympics',
                            'sport', 'team', 'game', 'match', 'championship'
                        ],
                        'Food & Cooking': [
                            'food', 'cooking', 'recipe', 'chef', 'kitchen', 'baking', 'cake', 'bread',
                            'pizza', 'pasta', 'burger', 'sandwich', 'salad', 'soup', 'dinner', 'lunch',
                            'breakfast', 'snack', 'dessert', 'chocolate', 'coffee', 'tea', 'drink',
                            'restaurant', 'cafe', 'foodie', 'delicious', 'tasty', 'yummy', 'cuisine',
                            'italian', 'chinese', 'mexican', 'indian', 'japanese', 'thai', 'vegan',
                            'vegetarian', 'healthy', 'diet', 'nutrition'
                        ],
                        'Fashion & Beauty': [
                            'fashion', 'style', 'outfit', 'clothes', 'clothing', 'dress', 'shirt', 'pants',
                            'shoes', 'accessories', 'jewelry', 'bag', 'beauty', 'makeup', 'skincare',
                            'hair', 'hairstyle', 'nails', 'cosmetics', 'lipstick', 'foundation', 'eyeshadow',
                            'perfume', 'fragrance', 'model', 'runway', 'designer', 'brand', 'luxury',
                            'shopping', 'boutique', 'trend', 'fashionable', 'stylish', 'chic', 'elegant'
                        ],
                        'Travel': [
                            'travel', 'trip', 'vacation', 'holiday', 'journey', 'adventure', 'explore',
                            'destination', 'tourist', 'tourism', 'sightseeing', 'backpacking', 'hotel',
                            'resort', 'beach', 'mountain', 'city', 'country', 'culture', 'local',
                            'flight', 'airport', 'passport', 'visa', 'luggage', 'photography', 'landscape',
                            'wanderlust', 'nomad', 'roadtrip', 'cruise', 'island', 'europe', 'asia',
                            'america', 'africa', 'australia'
                        ],
                        'Technology': [
                            'technology', 'tech', 'gadget', 'device', 'smartphone', 'phone', 'iphone',
                            'android', 'computer', 'laptop', 'tablet', 'ipad', 'software', 'app',
                            'application', 'website', 'internet', 'online', 'digital', 'cyber',
                            'artificial', 'intelligence', 'ai', 'machine', 'robot', 'automation',
                            'innovation', 'startup', 'entrepreneur', 'business', 'coding', 'programming',
                            'developer', 'engineer', 'data', 'cloud', 'security', 'blockchain'
                        ],
                        'Gaming': [
                            'gaming', 'game', 'gamer', 'video', 'console', 'pc', 'mobile', 'online',
                            'multiplayer', 'esports', 'tournament', 'competition', 'stream', 'streaming',
                            'twitch', 'youtube', 'playstation', 'xbox', 'nintendo', 'switch', 'steam',
                            'minecraft', 'fortnite', 'pubg', 'lol', 'dota', 'csgo', 'valorant', 'apex',
                            'cod', 'fifa', 'nba2k', 'rpg', 'mmo', 'fps', 'strategy', 'puzzle', 'arcade'
                        ],
                        'Lifestyle': [
                            'lifestyle', 'life', 'daily', 'routine', 'morning', 'evening', 'weekend',
                            'home', 'house', 'apartment', 'decor', 'interior', 'design', 'diy',
                            'organization', 'cleaning', 'productivity', 'motivation', 'inspiration',
                            'goals', 'success', 'happiness', 'wellness', 'mindfulness', 'meditation',
                            'self', 'personal', 'development', 'growth', 'tips', 'advice', 'hacks'
                        ],
                        'News & Politics': [
                            'news', 'politics', 'political', 'government', 'election', 'vote', 'voting',
                            'democracy', 'president', 'minister', 'parliament', 'congress', 'senate',
                            'policy', 'law', 'legal', 'court', 'justice', 'rights', 'freedom', 'protest',
                            'activism', 'social', 'justice', 'equality', 'climate', 'environment',
                            'global', 'world', 'international', 'economy', 'economic', 'finance',
                            'market', 'stock', 'business', 'corporate', 'industry'
                        ],
                        'Pets & Animals': [
                            'pet', 'pets', 'animal', 'animals', 'dog', 'dogs', 'cat', 'cats', 'puppy',
                            'kitten', 'bird', 'fish', 'rabbit', 'hamster', 'guinea', 'pig', 'reptile',
                            'snake', 'lizard', 'turtle', 'horse', 'cow', 'pig', 'sheep', 'goat',
                            'chicken', 'duck', 'wildlife', 'nature', 'zoo', 'veterinary', 'vet',
                            'training', 'care', 'feeding', 'grooming', 'cute', 'adorable', 'funny'
                        ]
                    }
                    
                    # Check for category matches
                    for category_name, keywords in category_mappings.items():
                        for keyword in keywords:
                            if keyword in hashtag_word:
                                category = category_name
                                break
                        if category != "General":
                            break
                    
                    # Additional context-based category detection from original text
                    if category == "General" and element_text:
                        text_lower = element_text.lower()
                        for category_name, keywords in category_mappings.items():
                            for keyword in keywords:
                                if keyword in text_lower:
                                    category = category_name
                                    break
                            if category != "General":
                                break
                
                # Store valid hashtags
                if hashtag and hashtag not in seen_hashtags and len(hashtag) > 3:
                    seen_hashtags.add(hashtag)
                    
                    # Calculate engagement score and sentiment analysis
                    engagement_score = calculate_engagement_score(hashtag, posts, category, element_text)
                    sentiment_polarity, sentiment_label = analyze_sentiment(hashtag, element_text)
                    
                    entry = {
                        "rank": rank or "N/A",
                        "hashtag": hashtag,
                        "posts": posts or "N/A", 
                        "views": views or "N/A",
                        "category": category or "General",
                        "engagement_score": engagement_score,
                        "sentiment_polarity": sentiment_polarity,
                        "sentiment_label": sentiment_label,
                        "scraped_at": datetime.now().isoformat(),
                        "original_text": element_text[:200]  # Keep original for debugging
                    }
                    scraped_data.append(entry)
                    
                    if debug:
                        print(f"   📝 EXTRACTED: Rank {rank}, {hashtag}, Posts: {posts}, Category: {category}, Engagement Score: {engagement_score}, Sentiment: {sentiment_label}")
                
                elif debug and i < 15:
                    print(f"   ❌ No valid hashtag extracted")
                        
            except Exception as e:
                if debug:
                    print(f"⚠️ Error processing element {i + 1}: {e}")
                continue

    except Exception as e:
        print(f"❌ Scraping error: {e}")
        
    finally:
        print("🔚 Closing browser...")
        if driver:
            try:
                driver.close()  # Close the browser window first
                driver.quit()   # Then quit the driver
            except Exception:
                # Ignore any cleanup errors
                pass

    # Save and display results
    if scraped_data:
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"tiktok_hashtags_v4_{timestamp}.csv"
        
        df = pd.DataFrame(scraped_data)
        df = df.drop_duplicates(subset=['hashtag'])
        df = df.sort_values('hashtag')
        
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        
        print(f"\n✅ Successfully scraped {len(scraped_data)} unique hashtags")
        print(f"📁 Saved to: {output_file}")
        
        # Display results
        print(f"\n📋 Sample data:")
        display_cols = ['rank', 'hashtag', 'posts', 'category', 'engagement_score', 'sentiment_label']
        sample_df = df[display_cols].head(15)
        print(sample_df.to_string(index=False))
        
        print(f"\n📊 Summary:")
        print(f"   Total hashtags: {len(scraped_data)}")
        print(f"   View More clicks: {total_view_more_clicks}")
        
    else:
        print(f"\n❌ No hashtags were extracted")
        print(f"💡 Check the debug HTML file to see what content was loaded")

    return scraped_data

def main():
    """Main function for V4"""
    print("🚀 TikTok Hashtag Scraper V4 - Focus on View More Buttons")
    print("This version prioritizes finding and clicking 'View More' buttons")
    
    # Initialize Supabase client
    print("\n🔗 Initializing Supabase connection...")
    supabase = init_supabase()
    
    config = {
        'scrolls': 15,          # Reduced since we're clicking View More
        'delay': 3,             
        'headless': False,      # Keep visual for debugging
        'output_file': None,    
        'debug': True           
    }
    
    print("\n⚙️ Configuration:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    print("\n" + "="*60)
    results = scrape_tiktok_hashtags_v4(**config)
    print("="*60)
    
    if results:
        print(f"\n🎉 SUCCESS! Scraped {len(results)} hashtags")
        
        # Upload to Supabase if connection is available
        if supabase:
            print("\n📤 Uploading data to Supabase...")
            upload_success = upload_to_supabase(supabase, results)
            if upload_success:
                print("✅ Data successfully uploaded to Supabase!")
            else:
                print("❌ Failed to upload data to Supabase")
        else:
            print("⚠️ Supabase connection not available - data saved locally only")
    else:
        print(f"\n😞 No hashtags were scraped")

if __name__ == "__main__":
    main()