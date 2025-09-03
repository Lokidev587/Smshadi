import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def get_chrome_options():
    """Configure Chrome options for Render"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Set Chrome binary location for Render
    if os.environ.get('RENDER'):
        # Use the Chrome that comes with webdriver-manager
        chrome_options.binary_location = "/opt/render/project/.render/chrome/linux-64/chrome"
    
    return chrome_options

def get_chrome_driver():
    """Get Chrome driver configured for Render"""
    chrome_options = get_chrome_options()
    
    # Use webdriver-manager to handle ChromeDriver
    service = Service(ChromeDriverManager().install())
    
    return webdriver.Chrome(service=service, options=chrome_options)
