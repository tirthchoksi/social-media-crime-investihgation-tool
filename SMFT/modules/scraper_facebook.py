from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CONFIGURATION ---
FB_EMAIL = "2403031267005@paruluniversity.ac.in"
FB_PASS = "Choksi@90"
# ---------------------

def login_to_facebook(driver):
    """Robust Login Function"""
    try:
        print("[*] Logging into Facebook...")
        driver.get("https://www.facebook.com/login")
        time.sleep(3)

        try:
            # Handle Cookie Consent if it pops up
            cookie_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]")
            if cookie_btn: cookie_btn[0].click()
        except: pass

        driver.find_element(By.ID, "email").send_keys(FB_EMAIL)
        driver.find_element(By.ID, "pass").send_keys(FB_PASS)
        
        # Click login (Generic selector to be safe)
        login_btn = driver.find_element(By.CSS_SELECTOR, "button[name='login']")
        login_btn.click()
        
        time.sleep(8)
        
        # Verify Login
        if "login" not in driver.current_url:
            print("[*] Login Successful.")
            return True
        else:
            print("[!] Login Failed.")
            return False
    except Exception as e:
        print(f"[!] Login Error: {e}")
        return False

def scrape_facebook_profile(page_name, limit=3):
    print(f"[*] Launching Deep Scraper for {page_name}...")
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    profile_data = [] # We will store everything here
    
    try:
        if FB_EMAIL and FB_PASS:
            login_to_facebook(driver)

        # 1. NAVIGATE TO PROFILE
        if "facebook.com" in page_name:
            url = page_name
        else:
            url = f"https://www.facebook.com/{page_name}"
            
        driver.get(url)
        time.sleep(5)
        
        # Close any popups
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()

        # ==================================================
        # 🟢 PART 1: EXTRACT PROFILE INFO (BIO, LOCATION)
        # ==================================================
        print("[*] Scanning Profile Info...")
        
        # We look for the "Intro" section by text, not class name
        intro_text = "No Intro Found"
        try:
            # Find the header that says "Intro" and get the text following it
            intro_element = driver.find_element(By.XPATH, "//span[text()='Intro']/ancestor::div[2]")
            intro_text = intro_element.text.replace("Intro", "").strip()
        except: 
            pass
        
        # Save Profile Metadata as the "First Post" so it appears at the top of your report
        profile_data.append({
            "text": f"[PROFILE METADATA]\nBIO/INTRO: {intro_text}",
            "date": "Profile Info"
        })

        # ==================================================
        # 🟢 PART 2: EXTRACT POSTS (WITH DATES)
        # ==================================================
        print("[*] Scrolling for posts...")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Strategy: Find all "Articles" (Facebook posts usually have role='article')
        posts = driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
        
        print(f"[*] Found {len(posts)} potential posts. Analyzing...")
        
        count = 0
        for post in posts:
            if count >= limit: break
            
            try:
                # 1. Extract Text
                # We look for the user-typed text container (dir='auto') INSIDE the post
                try:
                    content_el = post.find_element(By.CSS_SELECTOR, "div[dir='auto']")
                    text = content_el.text
                except:
                    text = "[Media/Image Only - No Text]"

                # 2. Extract Date
                # Dates are usually in links that have 'aria-label' or specific hover text
                timestamp = "Unknown Date"
                try:
                    # Look for the link that contains the time (it usually has an aria-label like "1 d", "2 h")
                    # Or look for the <use> tag which FB uses for timestamps sometimes
                    time_el = post.find_element(By.TAG_NAME, "a")
                    aria_label = time_el.get_attribute("aria-label")
                    if aria_label and len(aria_label) < 20: # Valid dates are short
                        timestamp = aria_label
                except: pass

                # Only save if it looks like a real post (not an ad)
                if len(text) > 5 or text == "[Media/Image Only - No Text]":
                    profile_data.append({
                        "text": text,
                        "date": timestamp
                    })
                    count += 1
                    
            except Exception as e:
                # Skip broken posts
                continue

    except Exception as e:
        print(f"[!] Scraper Error: {e}")

    finally:
        driver.quit()
        
    return profile_data