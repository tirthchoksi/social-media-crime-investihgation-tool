from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- CRITICAL: FILL ALL THREE ---
X_USER = "choksi90"
X_PASS = "choksi@90"
X_EMAIL = "rupangikuanl@gmail.com" 
# --------------------------------

def login_to_x(driver):
    """Robust X Login that handles 3-step verification."""
    try:
        print("[*] Logging into X...")
        driver.get("https://x.com/i/flow/login")
        time.sleep(5)
        
        # STEP 1: Username
        try:
            user_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            user_input.send_keys(X_USER)
            
            # Click Next
            buttons = driver.find_elements(By.XPATH, "//span[text()='Next']")
            if buttons: buttons[0].click()
            time.sleep(3)
        except Exception as e:
            print(f"Login Step 1 Error: {e}")
            return False

        # STEP 2: Unusual Activity Check (Email/Phone)
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            # If asking for text input again (and not password), it's verification
            if inputs and inputs[0].get_attribute("name") == "text":
                print("[!] X asked for verification (Email/Phone)...")
                inputs[0].send_keys(X_EMAIL)
                
                buttons = driver.find_elements(By.XPATH, "//span[text()='Next']")
                if buttons: buttons[0].click()
                time.sleep(3)
        except:
            pass 

        # STEP 3: Password
        try:
            pass_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            pass_input.send_keys(X_PASS)
            
            login_btns = driver.find_elements(By.XPATH, "//span[text()='Log in']")
            if login_btns: login_btns[0].click()
            time.sleep(5)
        except:
            print("[!] Could not find password field.")

        # FINAL CHECK
        if "home" in driver.current_url or "explore" in driver.current_url:
            print("[*] Login Successful!")
            return True
        else:
            print("[!] Login verification needed. You have 15 seconds to solve it manually...")
            time.sleep(15)
            return True

    except Exception as e:
        print(f"[!] Login Critical Failure: {e}")
        return False

def scrape_twitter_profile(target_username, limit=3):
    print(f"[*] Launching X Scraper for @{target_username}...")
    
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    tweets_data = []
    
    try:
        # 1. Login
        if X_USER and X_PASS:
            login_to_x(driver)
        
        # 2. Go to Profile
        driver.get(f"https://x.com/{target_username}")
        time.sleep(5)
        
        # 3. Scroll
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(4)
        
        # 4. Scrape
        articles = driver.find_elements(By.TAG_NAME, "article")
        print(f"Found {len(articles)} tweets.")

        for i, article in enumerate(articles[:limit]):
            try:
                # Get Text
                try:
                    text_el = article.find_element(By.CSS_SELECTOR, '[data-testid="tweetText"]')
                    text = text_el.text
                except: text = "No Text (Media)"

                # Get Time (FIXED TYPO HERE)
                try:
                    time_el = article.find_element(By.TAG_NAME, "time")
                    timestamp = time_el.get_attribute("datetime") # Fixed variable name
                except: timestamp = "Unknown"

                tweets_data.append({"text": text, "date": timestamp})
            except: pass
            
    except Exception as e:
        print(f"X Scraper Error: {e}")
    finally:
        driver.quit()
        
    return tweets_data