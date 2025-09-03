#!/usr/bin/env python3
"""
Script to install Chrome in Render environment
"""
import os
import subprocess
import sys

def install_chrome():
    """Install Chrome using webdriver-manager"""
    try:
        print("Installing Chrome...")
        
        # Use webdriver-manager to install Chrome
        from webdriver_manager.chrome import ChromeDriverManager
        from webdriver_manager.core.utils import ChromeType
        
        # This will download and setup Chrome
        chrome_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        print(f"Chrome installed at: {chrome_path}")
        
        return True
    except Exception as e:
        print(f"Error installing Chrome: {e}")
        return False

if __name__ == "__main__":
    success = install_chrome()
    sys.exit(0 if success else 1)
