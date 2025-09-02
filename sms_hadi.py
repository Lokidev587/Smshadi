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
import threading
import os
from flask import Flask

# Flask server for uptime monitoring
app = Flask(__name__)

@app.route('/')
def home():
    return {'status': 'Bot is running', 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}, 200

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'sms-monitoring-bot'}, 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

# Start Flask server in background thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()
print("Flask server started")

# Configuration
USERNAME = 'Keshav2009'
PASSWORD = 'Rana@54321'
BASE_URL = 'http://185.2.83.39'
TELEGRAM_BOT_TOKEN = "8399381709:AAHmPWWzDBJZK9Y149c_asffbLEC4D_bAog"
TELEGRAM_CHAT_IDS = ["-1002780854648", "-1001635870008"]

# Import country flags handling
from flags import get_country_flag, COUNTRY_FLAGS

# Setup Chrome Driver with proper options for Docker
print("Initializing Chrome Driver...")
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-extensions')
options.add_argument('--disable-web-security')
options.add_argument('--allow-running-insecure-content')
options.add_argument('--disable-background-networking')
options.add_argument('--disable-background-timer-throttling')
options.add_argument('--disable-renderer-backgrounding')
options.add_argument('--disable-backgrounding-occluded-windows')
options.add_argument('--disable-client-side-phishing-detection')
options.add_argument('--disable-crash-reporter')
options.add_argument('--disable-oopr-debug-crash-dump')
options.add_argument('--no-crash-upload')
options.add_argument('--disable-low-res-tiling')
options.add_argument('--disable-ipc-flooding-protection')

# Set Chrome binary path
options.binary_location = '/usr/bin/google-chrome'

try:
    # Use installed ChromeDriver
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 15)
    print("Chrome Driver initialized successfully")
except Exception as e:
    print(f"Failed to initialize Chrome: {e}")
    print("Keeping Flask server running...")
    while True:
        time.sleep(60)

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
            "reply_markup": json.dumps(inline_keyboard)
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
    
    msg_html = f'''<b>🔥 {service} {country} ✨</b>

⏰ Time: {msg['date']}
🌍 Country: {country} {flag}
⚙️ Service: {service}
☎️ Number: {masked_number}

<code>🔑 OTP: {otp}</code>

📩 Full Message: {msg['sms']}'''
    
    return msg_html

# Main execution with your existing logic
try:
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
            response_input.clear()
            response_input.send_keys(text)
            time.sleep(1)
            verify_btn = driver.find_element(By.ID, "recaptcha-verify-button")
            verify_btn.click()
            print("Submitted audio response")
            
            driver.switch_to.default_content()
            print("Waiting for verification...")
            time.sleep(3)
        else:
            print("Could not find challenge iframe")
    else:
        print("Could not find captcha iframe")
    
    # Click login button
    login_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "login100-form-btn")))
    login_button.click()
    print("Clicked login button")
    time.sleep(3)
    
    # Check login success
    time.sleep(5)
    print(f"Current URL after login: {driver.current_url}")
    
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
        
        for row in rows[:5]:
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
                driver.refresh()
                time.sleep(5)
                
                if "login" in driver.current_url:
                    raise Exception("Session expired")
                
                show_report_btn = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "input#sbutton[value='Show Report']")))
                driver.execute_script("arguments[0].scrollIntoView(true);", show_report_btn)
                time.sleep(2)
                driver.execute_script("arguments[0].click();", show_report_btn)
                time.sleep(3)
                
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
                
                retry_count = 0
                time.sleep(10)
                
            except Exception as e:
                print(f"\nError during monitoring: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    print("Max retries reached. Exiting...")
                    break
                
                print(f"Retry attempt {retry_count}/{max_retries}")
                time.sleep(5)
                
                try:
                    driver.get(f"{BASE_URL}/ints/agent/SMSCDRReports")
                    time.sleep(3)
                except Exception:
                    pass
    else:
        print("Login failed. Please check the credentials and try again.")

except KeyboardInterrupt:
    print("\nStopping script by user request...")
except Exception as e:
    print(f"\nCritical error: {e}")
finally:
    print("\nClosing browser...")
    try:
        driver.quit()
    except:
        pass
