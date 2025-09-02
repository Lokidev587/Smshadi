from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import re
import requests
import os

# Configuration
USERNAME = 'Keshav2009'
PASSWORD = 'Rana@54321'
BASE_URL = 'http://185.2.83.39'
TELEGRAM_BOT_TOKEN = "8399381709:AAHmPWWzDBJZK9Y149c_asffbLEC4D_bAog"
TELEGRAM_CHAT_IDS = ["-1002780854648", "-1001635870008"]

# Import country flags handling
from flags import get_country_flag, COUNTRY_FLAGS

def extract_country_and_flag(range_str):
    """Extract country name and get its flag"""
    if not range_str:
        return "UNKNOWN", "🌍"
    country = range_str.split()[0].strip().upper()
    flag = get_country_flag(country)
    return country, flag

def extract_otp(sms):
    """Extract OTP from SMS message"""
    patterns = [
        r"(?:FB-)?(\d{5})",  # FB-12345 format or just 12345
        r"(\d{3}-\d{3})",    # 123-456 format
        r"(\d{6})"           # 123456 format
    ]
    for pattern in patterns:
        match = re.search(pattern, sms)
        if match:
            return match.group(1) if "FB-" in pattern else match.group(0)
    return "N/A"

def mask_number(number):
    """Mask middle digits of phone number"""
    if len(number) <= 8:
        return number
    return number[:4] + 'x' * (len(number) - 8) + number[-4:]

def send_telegram_message(msg_html):
    """Send message to Telegram channels with inline buttons"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    print("\nSending to Telegram channels...")
    
    # Define inline keyboard with two buttons
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "NUMBER CHANNEL", "url": "https://t.me/BugsNum"},
                {"text": "DEVELOPER", "url": "https://t.me/Mehedi5710"}
            ]
        ]
    }
    
    for chat_id in TELEGRAM_CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": msg_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": json.dumps(inline_keyboard)  # Add the inline keyboard
        }
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                print(f"Successfully sent to chat ID: {chat_id}")
            else:
                print(f"Failed to send to {chat_id}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Failed to send message to {chat_id}: {e}")

def process_message(msg):
    """Process and format message for Telegram"""
    country, flag = extract_country_and_flag(msg["range"])
    service = msg["cli"]
    otp = extract_otp(msg["sms"])
    masked_number = mask_number(msg["number"])
    
    msg_html = f'''
<b>🔥 {service} {country} ✨</b>
<blockquote>⏰ Time: {msg['date']}</blockquote>
<blockquote>🌍 Country: {country} {flag}</blockquote>
<blockquote>⚙️ Service: {service}</blockquote>
<blockquote>☎️ Number: {masked_number}</blockquote>
<blockquote>🔑 OTP: <code>{otp}</code></blockquote>
<blockquote>📩 Full Message:</blockquote>
<blockquote>{msg['sms']}</blockquote>
'''
    return msg_html

def setup_chrome_driver():
    """Setup Chrome driver with proper options for Render deployment"""
    print("Initializing Chrome Driver...")
    options = Options()
    
    # Essential options for Render/server deployment
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-web-security')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Try to use system chrome on Render
    try:
        # On Render, Chrome is typically installed via buildpacks
        service = Service()  # Use default ChromeDriver
        driver = webdriver.Chrome(service=service, options=options)
        print("✓ Chrome driver initialized successfully")
        return driver
    except Exception as e:
        print(f"Failed to initialize Chrome driver: {e}")
        # Fallback: try with webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✓ Chrome driver initialized with webdriver-manager")
            return driver
        except Exception as e2:
            print(f"Failed with webdriver-manager too: {e2}")
            raise Exception("Could not initialize Chrome driver")

def main():
    """Main function to run SMS monitoring"""
    driver = None
    try:
        # Setup Chrome Driver
        driver = setup_chrome_driver()
        wait = WebDriverWait(driver, 15)

        print("Navigating to login page...")
        driver.get(f'{BASE_URL}/ints/login')
        
        # Fill in username and password
        driver.find_element(By.NAME, 'username').send_keys(USERNAME)
        driver.find_element(By.NAME, 'password').send_keys(PASSWORD)
        
        # Handle reCAPTCHA
        driver.switch_to.default_content()
        captcha_iframe = None
        for frame in driver.find_elements(By.TAG_NAME, "iframe"):
            src = frame.get_attribute("src")
            if src and "recaptcha" in src:
                captcha_iframe = frame
                break
                
        if captcha_iframe:
            driver.switch_to.frame(captcha_iframe)
            checkbox = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border")))
            checkbox.click()
            time.sleep(2)
            driver.switch_to.default_content()
            
            # Handle audio challenge
            challenge_iframe = None
            for _ in range(15):
                for frame in driver.find_elements(By.TAG_NAME, "iframe"):
                    title = frame.get_attribute("title")
                    if title and "recaptcha challenge" in title:
                        challenge_iframe = frame
                        break
                if challenge_iframe:
                    break
                time.sleep(1)
                
            if challenge_iframe:
                driver.switch_to.frame(challenge_iframe)
                audio_btn = wait.until(EC.element_to_be_clickable((By.ID, "recaptcha-audio-button")))
                audio_btn.click()
                time.sleep(2)
                
                # Get and process audio
                audio_src = wait.until(EC.presence_of_element_located((By.ID, "audio-source"))).get_attribute("src")
                print("\nAudio source URL:", audio_src)
                
                # Use RapidAPI for transcription
                url = "https://speech-to-text-ai.p.rapidapi.com/transcribe"
                querystring = {"url": audio_src, "lang": "en", "task": "transcribe"}
                headers = {
                    "x-rapidapi-key": "55c16d2ed5msh8228e6120dda6fbp1d2fbajsn2e0cf583a007",
                    "x-rapidapi-host": "speech-to-text-ai.p.rapidapi.com"
                }
                response = requests.post(url, headers=headers, params=querystring)
                result = response.json()
                text = result.get("text", "")
                print(f"Transcribed text: {text}")
                
                # Submit audio response and handle verification errors
                if len(text.strip()) < 3 or "manage" in text.lower() or "organizational" in text.lower():
                    print("Invalid transcription. Retrying audio challenge...")
                    driver.find_element(By.ID, "recaptcha-reload-button").click()
                    time.sleep(2)
                    
                    # Get and process audio again
                    audio_src = wait.until(EC.presence_of_element_located((By.ID, "audio-source"))).get_attribute("src")
                    print("\nRetrying with new audio...")
                    response = requests.post(url, headers=headers, params={"url": audio_src, "lang": "en", "task": "transcribe"})
                    result = response.json()
                    text = result.get("text", "").strip()
                    print(f"New transcribed text: {text}")
                
                response_input = driver.find_element(By.ID, "audio-response")
                response_input.clear()  # Clear any existing text
                response_input.send_keys(text)
                time.sleep(1)  # Small delay before clicking verify
                verify_btn = driver.find_element(By.ID, "recaptcha-verify-button")
                verify_btn.click()
                print("Submitted audio response")
                
                # Wait for verification
                driver.switch_to.default_content()
                print("Waiting for verification...")
                time.sleep(3)
                
                # Click login button
                login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login100-form-btn")))
                login_button.click()
                print("Clicked login button")
                time.sleep(3)
                
                # Check login success (give more time and check multiple URLs)
                time.sleep(5)  # Give more time for redirect
                print(f"Current URL after login: {driver.current_url}")
                
                # Check multiple possible success URLs
                if any(x in driver.current_url for x in ["/dashboard", "/agent", "/ints/agent"]):
                    print("\nLogin successful!")
                    
                    # Navigate to SMS page
                    print("Navigating to SMS monitoring page...")
                    driver.get(f"{BASE_URL}/ints/agent/SMSCDRReports")
                    time.sleep(3)
                    
                    # First get last 5 messages
                    seen = set()
                    print("\nFetching last 5 messages first...")
                    
                    # Click Show Report to get initial messages
                    show_report_btn = wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input#sbutton[value='Show Report']")))
                    driver.execute_script("arguments[0].scrollIntoView(true);", show_report_btn)
                    time.sleep(2)
                    driver.execute_script("arguments[0].click();", show_report_btn)
                    time.sleep(3)
                    
                    # Get initial messages
                    rows = driver.find_elements(By.CSS_SELECTOR, "table#dt tbody tr")
                    message_count = 0
                    
                    for row in rows[:5]:  # Only process first 5 messages
                        if row.get_attribute("style") and "display: none" in row.get_attribute("style"):
                            continue
                            
                        tds = row.find_elements(By.TAG_NAME, "td")
                        if len(tds) < 9:
                            continue
                        
                        msg = {
                            "date": tds[0].text.strip(),
                            "range": tds[1].text.strip(),
                            "number": tds[2].text.strip(),
                            "cli": tds[3].text.strip(),
                            "sms": tds[5].text.strip(),
                            "currency": tds[6].text.strip(),
                            "payout": tds[7].text.strip(),
                            "client_payout": tds[8].text.strip()
                        }
                        
                        row_key = tuple(td.text.strip() for td in tds)
                        if row_key in seen:
                            continue
                        
                        msg_html = process_message(msg)
                        print(f"\nSending previous message {message_count + 1} of 5")
                        send_telegram_message(msg_html)
                        seen.add(row_key)
                        message_count += 1
                        time.sleep(1)
                    
                    print(f"\nSent {message_count} previous messages")
                    print("\nNow monitoring for new SMS messages. Press Ctrl+C to stop.")
                    
                    # Monitor for new messages
                    retry_count = 0
                    max_retries = 3
                    
                    while True:
                        try:
                            # Refresh and get new messages
                            driver.refresh()
                            time.sleep(5)  # Increased wait time after refresh
                            
                            # Check if we're still logged in
                            if "login" in driver.current_url:
                                raise Exception("Session expired")
                                
                            show_report_btn = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR, "input#sbutton[value='Show Report']")))
                            driver.execute_script("arguments[0].scrollIntoView(true);", show_report_btn)
                            time.sleep(2)  # Increased wait time before clicking
                            driver.execute_script("arguments[0].click();", show_report_btn)
                            time.sleep(3)  # Wait after clicking
                            
                            rows = driver.find_elements(By.CSS_SELECTOR, "table#dt tbody tr")
                            for row in rows:
                                try:
                                    style = row.get_attribute("style") or ""
                                    if "display: none" in style:
                                        continue
                                        
                                    tds = row.find_elements(By.TAG_NAME, "td")
                                    if len(tds) < 9:
                                        continue
                                    
                                    row_key = tuple(td.text.strip() for td in tds)
                                    if row_key in seen:
                                        continue
                                    seen.add(row_key)
                                    
                                    msg = {
                                        "date": tds[0].text.strip(),
                                        "range": tds[1].text.strip(),
                                        "number": tds[2].text.strip(),
                                        "cli": tds[3].text.strip(),
                                        "sms": tds[5].text.strip(),
                                        "currency": tds[6].text.strip(),
                                        "payout": tds[7].text.strip(),
                                        "client_payout": tds[8].text.strip()
                                    }
                                    
                                    msg_html = process_message(msg)
                                    print("\nNew SMS Message:")
                                    print(json.dumps(msg, indent=2, ensure_ascii=False))
                                    send_telegram_message(msg_html)
                                except Exception as row_error:
                                    print(f"Error processing row: {row_error}")
                                    continue
                            
                            # Reset retry count on successful iteration
                            retry_count = 0
                            time.sleep(10)
                            
                        except Exception as e:
                            print(f"\nError during monitoring: {e}")
                            retry_count += 1
                            
                            if "login" in driver.current_url:
                                print("\nSession expired, performing re-login...")
                                
                                # Fill in username and password
                                driver.find_element(By.NAME, 'username').send_keys(USERNAME)
                                driver.find_element(By.NAME, 'password').send_keys(PASSWORD)
                                
                                # Handle reCAPTCHA (simplified for re-login)
                                try:
                                    driver.switch_to.default_content()
                                    captcha_iframe = None
                                    for frame in driver.find_elements(By.TAG_NAME, "iframe"):
                                        src = frame.get_attribute("src")
                                        if src and "recaptcha" in src:
                                            captcha_iframe = frame
                                            break
                                    
                                    if captcha_iframe:
                                        driver.switch_to.frame(captcha_iframe)
                                        checkbox = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border")))
                                        checkbox.click()
                                        time.sleep(2)
                                        driver.switch_to.default_content()
                                        
                                        # Click login button
                                        login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login100-form-btn")))
                                        login_button.click()
                                        time.sleep(3)
                                        
                                        # Navigate back to SMS page after successful login
                                        print("\nNavigating back to SMS monitoring page...")
                                        driver.get(f"{BASE_URL}/ints/agent/SMSCDRReports")
                                        time.sleep(3)
                                        continue  # Continue monitoring
                                except Exception as captcha_error:
                                    print(f"Error handling re-login captcha: {captcha_error}")
                                        
                            if retry_count >= max_retries:
                                print(f"Maximum retries ({max_retries}) reached. Restarting...")
                                retry_count = 0
                                
                            print(f"Retry attempt {retry_count}/{max_retries}")
                            print("Attempting to recover...")
                            time.sleep(5)  # Short wait between retries
                            
                            # Try to navigate back to the SMS page
                            print("Navigating back to SMS page...")
                            driver.get(f"{BASE_URL}/ints/agent/SMSCDRReports")
                            time.sleep(3)
                                
                else:
                    print("Login failed. Please check the credentials and try again.")
            else:
                print("Could not find challenge iframe")
        else:
            print("Could not find captcha iframe")
            
    except KeyboardInterrupt:
        print("\nStopping script by user request...")
    except Exception as e:
        print(f"\nCritical error: {e}")
    finally:
        print("\nClosing browser...")
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()