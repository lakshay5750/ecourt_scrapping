import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import base64
import logging
from PIL import Image
import io
import threading

logger = logging.getLogger(__name__)

class ECourtsScraperEnhanced:
    def __init__(self, headless=False):  # Set to False for CAPTCHA solving
        self.base_url = "https://services.ecourts.gov.in/ecourtindia_v6/"
        self.headless = headless
        self.driver = None
        self.captcha_solved = False
        self.manual_mode = True  # Use manual CAPTCHA solving by default
    
    def setup_driver(self):
        """Setup Chrome driver for CAPTCHA handling"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Important for CAPTCHA handling
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--window-size=1200,800')
            
            # Automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(45)
            self.driver.set_script_timeout(30)
            
            return self.driver
            
        except Exception as e:
            logger.error(f"Failed to setup driver: {str(e)}")
            raise
    
    def detect_and_solve_captcha(self, max_attempts=3):
        """Enhanced CAPTCHA detection and solving"""
        for attempt in range(max_attempts):
            try:
                # Wait for CAPTCHA to appear
                captcha_image = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'captcha') or contains(@id, 'captcha')]"))
                )
                
                logger.info(f"CAPTCHA detected (attempt {attempt + 1}/{max_attempts})")
                
                if self.manual_mode:
                    success = self.solve_captcha_manual_enhanced(captcha_image)
                else:
                    success = self.solve_captcha_automated(captcha_image)
                
                if success:
                    self.captcha_solved = True
                    return True
                else:
                    # Try refreshing CAPTCHA
                    refresh_btn = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Refresh') or contains(@onclick, 'captcha')]")
                    if refresh_btn:
                        refresh_btn[0].click()
                        time.sleep(2)
                    
            except TimeoutException:
                logger.info("No CAPTCHA detected")
                return True
            except Exception as e:
                logger.error(f"CAPTCHA solving attempt {attempt + 1} failed: {str(e)}")
        
        return False
    
    def solve_captcha_manual_enhanced(self, captcha_element):
        """Enhanced manual CAPTCHA solving for web application"""
        try:
            # Save CAPTCHA image for display in web interface
            captcha_screenshot = captcha_element.screenshot_as_png
            captcha_filename = f"captcha_{int(time.time())}.png"
            captcha_path = os.path.join('static', 'captcha', captcha_filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(captcha_path), exist_ok=True)
            
            # Save CAPTCHA image
            with open(captcha_path, 'wb') as f:
                f.write(captcha_screenshot)
            
            logger.info(f"CAPTCHA image saved: {captcha_filename}")
            
            # For web application, we'll store the CAPTCHA info
            self.current_captcha = {
                'filename': captcha_filename,
                'path': captcha_path,
                'input_field': self.find_captcha_input_field(),
                'timestamp': time.time()
            }
            
            return False  # Return False to indicate manual solving needed
            
        except Exception as e:
            logger.error(f"Error in manual CAPTCHA solving: {str(e)}")
            return False
    
    def find_captcha_input_field(self):
        """Find the CAPTCHA input field"""
        try:
            # Look for common CAPTCHA input field selectors
            selectors = [
                "input[name='captcha']",
                "input[name='captcha_code']", 
                "input[name='captcha_text']",
                "input[name='code']",
                "input[type='text']",
                "input[id*='captcha']",
                "input[placeholder*='captcha']",
                "input[placeholder*='code']"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.is_displayed() and element.is_enabled():
                        return selector
                except:
                    continue
            
            # If no specific selector found, try to find any input near CAPTCHA image
            inputs = self.driver.find_elements(By.XPATH, "//input[@type='text']")
            for input_field in inputs:
                if input_field.is_displayed():
                    return "input[type='text']"
                    
            return None
            
        except Exception as e:
            logger.error(f"Error finding CAPTCHA input: {str(e)}")
            return None
    
    def submit_captcha_solution(self, captcha_text):
        """Submit the solved CAPTCHA"""
        try:
            if not hasattr(self, 'current_captcha'):
                logger.error("No current CAPTCHA to solve")
                return False
            
            # Find and fill CAPTCHA input field
            if self.current_captcha['input_field']:
                captcha_input = self.driver.find_element(By.CSS_SELECTOR, self.current_captcha['input_field'])
            else:
                # Fallback: find any text input
                captcha_input = self.driver.find_element(By.XPATH, "//input[@type='text']")
            
            captcha_input.clear()
            captcha_input.send_keys(captcha_text)
            
            # Find and click submit button
            submit_buttons = [
                "input[type='submit']",
                "button[type='submit']", 
                "input[value*='Submit']",
                "button[contains(text(), 'Submit')]",
                "input[value*='Search']",
                "button[contains(text(), 'Search')]"
            ]
            
            for selector in submit_buttons:
                try:
                    submit_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        break
                except:
                    continue
            
            # Wait for page to load and check if CAPTCHA was successful
            time.sleep(3)
            
            # Check if we're still on CAPTCHA page
            if self.is_captcha_page():
                logger.error("CAPTCHA solution rejected")
                return False
            else:
                logger.info("CAPTCHA solved successfully")
                self.captcha_solved = True
                
                # Clean up CAPTCHA image
                if os.path.exists(self.current_captcha['path']):
                    os.remove(self.current_captcha['path'])
                
                return True
                
        except Exception as e:
            logger.error(f"Error submitting CAPTCHA: {str(e)}")
            return False
    
    def is_captcha_page(self):
        """Check if we're still on a CAPTCHA page"""
        try:
            # Check for CAPTCHA image
            self.driver.find_element(By.XPATH, "//img[contains(@src, 'captcha')]")
            return True
        except:
            return False
    
    def solve_captcha_automated(self, captcha_element):
        """Attempt automated CAPTCHA solving (basic implementation)"""
        try:
            # This is a simplified version - in production, you'd use a CAPTCHA solving service
            logger.info("Attempting automated CAPTCHA solving...")
            
            # Get CAPTCHA image as base64
            captcha_screenshot = captcha_element.screenshot_as_png
            
            # Simple OCR attempt (this won't work for complex CAPTCHAs)
            # In real implementation, you'd use a service like 2captcha.com
            
            # For now, return False to fall back to manual solving
            return False
            
        except Exception as e:
            logger.error(f"Automated CAPTCHA solving failed: {str(e)}")
            return False
    
    def search_with_captcha_handling(self, search_function, *args, **kwargs):
        """Wrapper function to handle CAPTCHA during search"""
        try:
            if not self.driver:
                self.setup_driver()
            
            # Navigate to eCourts
            self.driver.get(self.base_url)
            time.sleep(3)
            
            # Handle CAPTCHA
            captcha_success = self.detect_and_solve_captcha()
            
            if not captcha_success and hasattr(self, 'current_captcha'):
                # CAPTCHA needs manual solving
                return {
                    'success': False,
                    'captcha_required': True,
                    'captcha_image': self.current_captcha['filename'],
                    'message': 'CAPTCHA solving required'
                }
            
            # Perform the actual search
            return search_function(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Search with CAPTCHA handling failed: {str(e)}")
            return {
                'success': False,
                'error': f'Search failed: {str(e)}'
            }
    
    def search_by_cnr_enhanced(self, cnr_number):
        """CNR search with enhanced CAPTCHA handling"""
        def actual_search():
            try:
                # Find CNR input field
                cnr_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "cnr_number"))
                )
                cnr_input.clear()
                cnr_input.send_keys(cnr_number)
                
                # Click search
                search_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                search_btn.click()
                
                # Wait for results
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                
                # Parse results
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                return self.parse_case_results(soup, cnr_number)
                
            except TimeoutException:
                return {'success': False, 'error': 'Timeout during search'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        return self.search_with_captcha_handling(actual_search)
    
    def close_driver(self):
        """Close the browser driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Update the Flask app to handle CAPTCHA
from flask import session
import secrets

def generate_captcha_session():
    """Generate a unique session ID for CAPTCHA solving"""
    return secrets.token_hex(16)

# Add these routes to your app.py
@app.route('/captcha/required', methods=['POST'])
def captcha_required():
    """Endpoint called when CAPTCHA is required"""
    data = request.json
    captcha_image = data.get('captcha_image')
    
    # Generate session for this CAPTCHA attempt
    session_id = generate_captcha_session()
    session[session_id] = {
        'captcha_image': captcha_image,
        'timestamp': time.time(),
        'solved': False
    }
    
    return jsonify({
        'captcha_required': True,
        'session_id': session_id,
        'captcha_image_url': f'/static/captcha/{captcha_image}'
    })

@app.route('/captcha/solve', methods=['POST'])
def solve_captcha():
    """Endpoint to submit CAPTCHA solution"""
    data = request.json
    session_id = data.get('session_id')
    captcha_text = data.get('captcha_text')
    
    if not session_id or not captcha_text:
        return jsonify({'success': False, 'error': 'Missing session ID or CAPTCHA text'})
    
    session_data = session.get(session_id)
    if not session_data:
        return jsonify({'success': False, 'error': 'Invalid session'})
    
    # Here you would typically use the scraper to submit the CAPTCHA
    # This is a simplified implementation
    try:
        # Update your scraper instance to use this CAPTCHA solution
        scraper = ECourtsScraperEnhanced()
        success = scraper.submit_captcha_solution(captcha_text)
        
        if success:
            session_data['solved'] = True
            return jsonify({'success': True, 'message': 'CAPTCHA solved successfully'})
        else:
            return jsonify({'success': False, 'error': 'CAPTCHA solution failed'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})