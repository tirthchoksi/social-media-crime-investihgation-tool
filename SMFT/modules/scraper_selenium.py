from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import requests
from datetime import datetime

# --- CONFIGURATION ---
INSTAGRAM_USER = "alligator.88096518" # Add dummy user inside quotes
INSTAGRAM_PASS = "rudrawedsporv" # Add dummy pass inside quotes

# --- THE GARBAGE COLLECTOR ---
# This list blocks the footer text you saw
META_JUNK = [
    "Meta", "About", "Blog", "Jobs", "Help", "API", "Privacy", "Terms", 
    "Locations", "Instagram Lite", "Threads", "Contact & Non-Users", 
    "Meta Verified", "English", "Afrikaans", "Español", "Français", 
    "Bahasa", "Deutsch", "Dansk", "Suomi", "Italiano", "Nederlands", 
    "Norsk", "Polski", "Português", "Svenska", "Türkçe", "Русский", 
    "हिन्दी", "中文", "日本語", "한국어", "Log In", "Sign Up", "Loading...", 
    "Log in", "Sign up", "Forgot password?", "Get the app"
]

def login_to_instagram(driver):
    try:
        driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(4)
        if len(driver.find_elements(By.NAME, "username")) > 0:
            driver.find_element(By.NAME, "username").send_keys(INSTAGRAM_USER)
            driver.find_element(By.NAME, "password").send_keys(INSTAGRAM_PASS)
            driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            time.sleep(6)
    except: pass

def download_latest_posts_selenium(target_username, limit=3):
    print(f"[*] Launching Browser for {target_username}...")
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    posts_data = []
    download_folder = f"downloads_{target_username}"
    os.makedirs(download_folder, exist_ok=True)

    try:
        if INSTAGRAM_USER and INSTAGRAM_PASS:
            login_to_instagram(driver)

        # 1. Go to Profile
        url = f"https://www.instagram.com/{target_username}/"
        driver.get(url)
        time.sleep(5) 

        # 2. Find Post Links
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(3)
        links = driver.find_elements(By.TAG_NAME, 'a')
        post_urls = [link.get_attribute('href') for link in links if '/p/' in link.get_attribute('href')]
        post_urls = list(dict.fromkeys(post_urls))[:limit]
        
        print(f"Found {len(post_urls)} posts. Scraping...")

        # 3. Visit Each Post
        for i, post_url in enumerate(post_urls):
            driver.get(post_url)
            time.sleep(5) 
            
            try:
                # A. GET CAPTION
                caption = "No Caption"
                try:
                    meta_desc = driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']")
                    raw = meta_desc.get_attribute("content")
                    if "Instagram:" in raw: caption = raw.split("Instagram:")[-1].strip().strip('"')
                    else: caption = raw
                except: pass

                # B. NUCLEAR COMMENT SCRAPING (WITH FILTER)
                comments_found = []
                try:
                    # Click "View all"
                    try:
                        buttons = driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if "View all" in btn.text or "comments" in btn.text:
                                driver.execute_script("arguments[0].click();", btn)
                                time.sleep(2)
                                break
                    except: pass

                    # Grab ALL text
                    all_text_elements = driver.find_elements(By.XPATH, "//span | //div")
                    
                    for el in all_text_elements:
                        text = el.text.strip()
                        
                        # --- THE NEW FILTER ---
                        # 1. Must be longer than 2 chars
                        # 2. Must not be a known garbage word (Meta, About, etc.)
                        # 3. Must not be the caption itself
                        is_junk = False
                        for junk in META_JUNK:
                            if junk in text or text in junk:
                                is_junk = True
                                break
                        
                        if len(text) > 2 and not is_junk and text not in caption:
                            if text not in comments_found:
                                comments_found.append(text)
                    
                    # Limit to top 10 unique comments
                    comments_found = comments_found[:10]

                except Exception as e:
                    print(f"Comment scrape warning: {e}")

                # C. DOWNLOAD IMAGE
                img_src = None
                filename = None
                try:
                    meta_img = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']")
                    img_src = meta_img.get_attribute("content")
                except: pass

                if img_src:
                    response = requests.get(img_src)
                    filename = f"{download_folder}/post_{i}.jpg"
                    with open(filename, "wb") as f:
                        f.write(response.content)

                # D. SAVE DATA
                posts_data.append({
                    "image_path": filename,
                    "caption": caption,
                    "comments": comments_found, 
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                print(f"Scraped Post {i+1} - Cleaned {len(comments_found)} comments")

            except Exception as e:
                print(f"Error post {i}: {e}")

    except Exception as e:
        print(f"Selenium Error: {e}")
    finally:
        driver.quit()
        
    return posts_data