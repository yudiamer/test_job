#!/usr/bin/env python3

import time
import argparse
import os
import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add credentials directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
credentials_dir = os.path.join(project_root, "credentials")
sys.path.insert(0, credentials_dir)

from credentials_loader import get_xflush_credentials

class TradeTrendsAutomation:
    def __init__(self, headless=False, credentials=None):
        self.driver = None
        self.headless = headless
        
        # Load XFlush credentials from file
        if credentials is None:
            credentials = get_xflush_credentials()
        
        self.username = credentials['username']
        self.password = credentials['password']
        self.login_url = credentials['login_url']
        self.trade_trends_url = credentials['trade_trends_url']
        self.window_size = credentials['browser_window_size']
        self.wait_timeout = credentials['browser_wait_timeout']
        self.screenshot_wait = credentials['screenshot_wait_time']
        
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        chrome_options = Options()
        chrome_options.add_argument(f'--window-size={self.window_size}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            chrome_options.add_argument('--headless')
            print("🚀 Starting Chrome browser (headless mode)...")
        else:
            print("🚀 Starting Chrome browser (visible mode)...")
            
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
     
        
    def login_and_setup(self):
        """Complete login and language setup process"""
        # Navigate to login page
        print("🌐 Navigating to login page...")
        self.driver.get(self.login_url)
        time.sleep(1)  # Reduced from 3 to 1
        
        # Login with credentials
        print("🔐 Logging in...")
        username_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
        password_field = self.driver.find_element(By.NAME, "password")
        login_button = self.driver.find_element(By.XPATH, "//span[contains(text(), '登录')]/parent::button")
        
        username_field.send_keys(self.username)
        password_field.send_keys(self.password)
        login_button.click()
        
        # Wait for dashboard to load
        print("⏳ Waiting for dashboard to load...")
        time.sleep(5)  # Reduced from 10 to 5
        
        # Change language to English
        print("🌐 Changing language to English...")
        try:
            location_icons = self.driver.find_elements(By.CSS_SELECTOR, "i.anticon.anticon-environment-o")
            if location_icons:
                location_icons[0].click()
                time.sleep(1)  # Reduced from 2 to 1
                
                english_elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'English')]")
                if english_elements:
                    english_elements[0].click()
                    time.sleep(1)  # Reduced from 3 to 1
                    print("✅ Language changed to English")
                else:
                    print("⚠️  English option not found, continuing...")
            else:
                print("⚠️  Location icon not found, continuing...")
        except Exception as e:
            print(f"⚠️  Language change had issues: {e}, continuing...")
        
        # Navigate to Trade Trends dashboard
        print(f"🎯 Navigating to Trade Trends dashboard...")
        self.driver.get(self.trade_trends_url)
        time.sleep(2)  # Reduced from 3 to 2
        
        print(f"📍 Current URL: {self.driver.current_url}")
        print(f"📄 Page Title: {self.driver.title}")
        
        return True
    
    def click_trade_trends(self):
        """Find and click on Trade Trends element"""
        print("🔍 Looking for Trade Trends...")
        
        trade_trends_selectors = [
            "//span[contains(text(), 'Trade Trends')]",
            "//div[contains(text(), 'Trade Trends')]",
            "//*[contains(text(), 'Trade Trends')]",
        ]
        
        for selector in trade_trends_selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        element_text = element.text.strip()
                        print(f"✅ Found element: '{element_text}'")
                        
                        if 'trade trends' in element_text.lower():
                            print(f"🎯 Clicking on Trade Trends: '{element_text}'")
                            
                            # Scroll to element and click
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.5)  # Reduced from 1 to 0.5
                            element.click()
                            time.sleep(2)  # Reduced from 3 to 2
                            
                            print("✅ Clicked Trade Trends successfully!")
                            return True
                            
            except Exception as e:
                print(f"❌ Error with selector {selector}: {e}")
                continue
        
        print("❌ Trade Trends not found")
        return False
    
    def set_time_range(self, time_range_str):
        """Set the time range for Trade Trends based on input string"""
        from datetime import datetime
        
        if not time_range_str:
            print("⏰ No time range specified, using default")
            return True
        
        try:
            # Parse time range input
            if time_range_str.lower() == "today":
                # Use today's date from 00:00:00 to 23:59:59
                today = datetime.now()
                start_date = today.strftime("%Y-%m-%d")
                start_time = "00:00:00"
                end_date = today.strftime("%Y-%m-%d")
                end_time = "23:59:59"
                print(f"⏰ Using today's range: {start_date} {start_time} to {end_date} {end_time}")
            else:
                # Parse custom range: "2025-11-05 00:00:00,2025-11-05 23:59:59"
                parts = time_range_str.split(',')
                if len(parts) != 2:
                    print("❌ Invalid time range format. Use: '2025-11-05 00:00:00,2025-11-05 23:59:59'")
                    return False
                
                start_datetime_str = parts[0].strip()
                end_datetime_str = parts[1].strip()
                
                # Parse start datetime
                start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
                start_date = start_dt.strftime("%Y-%m-%d")
                start_time = start_dt.strftime("%H:%M:%S")
                
                # Parse end datetime
                end_dt = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M:%S")
                end_date = end_dt.strftime("%Y-%m-%d")
                end_time = end_dt.strftime("%H:%M:%S")
                
                # Validate: end must be after start
                if end_dt <= start_dt:
                    print("❌ End time must be after start time")
                    return False
                
                print(f"⏰ Using custom range: {start_date} {start_time} to {end_date} {end_time}")
            
            # Wait for page to load
            time.sleep(1)  # Reduced from 3 to 1
            
            # Set start date
            try:
                start_date_input = self.driver.find_element(By.XPATH, 
                    "//input[contains(@ng-model, 'timeInputs.startTime') and contains(@date-format, 'yyyy-MM-dd')]")
                start_date_input.clear()
                start_date_input.send_keys(start_date)
                print(f"  ✅ Set start date: {start_date}")
            except Exception as e:
                print(f"  ⚠️ Could not set start date: {e}")
            
            # Set start time
            try:
                start_time_input = self.driver.find_element(By.XPATH,
                    "//input[contains(@ng-model, 'timeInputs.startTime') and contains(@time-format, 'HH:mm:ss')]")
                start_time_input.clear()
                start_time_input.send_keys(start_time)
                print(f"  ✅ Set start time: {start_time}")
            except Exception as e:
                print(f"  ⚠️ Could not set start time: {e}")
            
            # Set end date
            try:
                end_date_input = self.driver.find_element(By.XPATH,
                    "//input[contains(@ng-model, 'timeInputs.endTime') and contains(@date-format, 'yyyy-MM-dd')]")
                end_date_input.clear()
                end_date_input.send_keys(end_date)
                print(f"  ✅ Set end date: {end_date}")
            except Exception as e:
                print(f"  ⚠️ Could not set end date: {e}")
            
            # Set end time
            try:
                end_time_input = self.driver.find_element(By.XPATH,
                    "//input[contains(@ng-model, 'timeInputs.endTime') and contains(@time-format, 'HH:mm:ss')]")
                end_time_input.clear()
                end_time_input.send_keys(end_time)
                print(f"  ✅ Set end time: {end_time}")
            except Exception as e:
                print(f"  ⚠️ Could not set end time: {e}")
            
            # Click Query button to apply the time range
            try:
                query_button = self.driver.find_element(By.XPATH, 
                    "//button[@ng-click='query()']")
                query_button.click()
                print("  ✅ Clicked Query button")
                time.sleep(2)  # Reduced from 3 to 2 - Wait for chart to update
            except Exception as e:
                print(f"  ⚠️ Could not click Query button: {e}")
            
            return True
            
        except ValueError as e:
            print(f"❌ Invalid date/time format: {e}")
            print("   Use format: YYYY-MM-DD HH:MM:SS")
            return False
        except Exception as e:
            print(f"❌ Error setting time range: {e}")
            return False
    
    def capture_chart_only(self):
        """Capture Trade Trends chart with time range form"""
        print("📸 Capturing Trade Trends chart with time range...")
        
        time.sleep(2)  # Reduced from 3 to 2 - Wait for chart to load
        
        # Find the container that includes both the time range form and chart
        try:
            # Try to find the parent container that includes the form and chart
            try:
                # Find the container that has both the form and chart
                container_element = self.driver.find_element(By.XPATH, 
                    "//div[contains(@class, 'xf-pop-up-container')]")
                print("  ✅ Found full container (form + chart)")
            except:
                # Fallback to just the chart if the form container isn't found
                container_element = self.driver.find_element(By.XPATH, 
                    "//div[@class='jr xf-chart' and @chart-title='Trade Trends']")
                print("  ℹ️ Using chart only (form container not found)")
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"trade_trends_chart_{timestamp}.png"
            # Use absolute path to screenshots directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            filepath = os.path.join(project_root, "screenshots", filename)
            
            # Scroll to element and capture
            self.driver.execute_script("arguments[0].scrollIntoView(true);", container_element)
            time.sleep(1)  # Reduced from 2 to 1
            container_element.screenshot(filepath)
            
            print(f"✅ Chart captured: {filename}")
            print(f"📐 Captured area: {container_element.size['width']}x{container_element.size['height']}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ Chart capture failed: {e}")
            return None
    
    
    def capture_statistics_info(self):
        """Capture the Statistics Info table specifically"""
        print("📊 Looking for Statistics Info icon to click...")
        
        try:
            # Wait a bit for the interface to load completely
            time.sleep(2)  # Reduced from 3 to 2
            
            # First, try to click the Statistics Info icon to open the popup
            statistics_icon_clicked = False
            
            # Selectors for the statistics icon (ordered by proven reliability from test results)
            icon_selectors = [
                # PRIMARY WORKING SELECTOR (confirmed in terminal output - Direct click succeeded + popup appeared)
                "(//div[@class='jr xf-chart']//i[contains(@class, 'xf-cms-icon-sangang')])[1]",
                
                # Backup selectors (in case page structure changes)
                "(//i[contains(@class, 'xf-cms-icon-sangang')])[1]",
                "(//a[contains(@class,'line-chart-stat')]//i)[1]",
            ]
            
            for selector in icon_selectors:
                try:
                    print(f"🔍 Trying icon selector: {selector}")
                    
                    # Use WebDriverWait to find element reliably
                    try:
                        icon_elements = WebDriverWait(self.driver, 3).until(
                            EC.presence_of_all_elements_located((By.XPATH, selector))
                        )
                    except TimeoutException:
                        print(f"⚠️ Timeout finding elements with: {selector}")
                        icon_elements = []
                    
                    print(f"   Found {len(icon_elements)} elements with this selector")
                    
                    for i, icon in enumerate(icon_elements):
                        if icon.is_displayed():
                            # Try to click this icon
                            try:
                                print(f"   Trying to click icon {i+1}...")
                                
                                # Scroll to element
                                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", icon)
                                time.sleep(1)  # Reduced from 2 to 1
                                
                                # Try different click methods
                                click_success = False
                                
                                # Method 1: Direct click
                                try:
                                    icon.click()
                                    print(f"   ✅ Direct click succeeded on icon {i+1}")
                                    click_success = True
                                except Exception as e:
                                    print(f"   ❌ Direct click failed: {e}")
                                
                                # Method 2: JavaScript click
                                if not click_success:
                                    try:
                                        self.driver.execute_script("arguments[0].click();", icon)
                                        print(f"   ✅ JavaScript click succeeded on icon {i+1}")
                                        click_success = True
                                    except Exception as e:
                                        print(f"   ❌ JavaScript click failed: {e}")
                                
                                # Method 3: Click parent element
                                if not click_success:
                                    try:
                                        parent = icon.find_element(By.XPATH, "..")
                                        parent.click()
                                        print(f"   ✅ Parent click succeeded on icon {i+1}")
                                        click_success = True
                                    except Exception as e:
                                        print(f"   ❌ Parent click failed: {e}")
                                
                                if click_success:
                                    statistics_icon_clicked = True
                                    
                                    # Wait for popup to appear
                                    print("⏳ Waiting for statistics popup to appear...")
                                    time.sleep(3)  # Reduced from 8 to 3
                                    
                                    # Check if popup appeared by looking for the table
                                    popup_check = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'xf-line-chart-stat-wrapper')]")
                                    if popup_check and popup_check[0].is_displayed():
                                        print(f"✅ Statistics popup appeared after clicking icon {i+1}!")
                                        break
                                    else:
                                        print(f"❌ No popup appeared after clicking icon {i+1}, trying next...")
                                        statistics_icon_clicked = False
                                        continue
                                        
                            except Exception as e:
                                print(f"   ❌ Failed to click icon {i+1}: {e}")
                                continue
                    
                    if statistics_icon_clicked:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Selector failed: {e}")
                    continue
            
            # If no icon was clicked successfully, return None
            if not statistics_icon_clicked:
                print("❌ Could not click any statistics icon!")
                return None
            
            # Now try to find the statistics popup that should have appeared
            print("🔍 Looking for Statistics Info popup...")
            
            # Try different selectors to find the statistics popup
            statistics_selectors = [
                "//div[contains(@class, 'xf-line-chart-stat-wrapper')]",
                "//div[contains(@class, 'stat-wrapper')]",
                "//div[contains(text(), 'Statistics Info')]",
                "//h3[contains(text(), 'Statistics Info')]", 
                "//span[contains(text(), 'Statistics Info')]",
                "//*[contains(text(), 'Statistics Info')]",
                "//table[contains(@class, 'xf-table')]",
                "//div[contains(@class, 'xf-pop-up')]//table",
                "//div[@class='table-responsive']//table",
                "//div[contains(@class, 'statistics')]//table",
            ]
            
            statistics_element = None
            
            for selector in statistics_selectors:
                try:
                    print(f"🔍 Trying statistics selector: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            element_text = element.text.strip()
                            print(f"✅ Found element with text: '{element_text[:100]}...'")
                            
                            # Check if this looks like statistics info
                            if any(keyword in element_text.lower() for keyword in 
                                  ['statistics', 'column', 'max', 'min', 'average', 'total', 'count',
                                   'create order', 'payment apply', 'cashier consult', 'trade success']):
                                print(f"🎯 Found Statistics Info element!")
                                statistics_element = element
                                break
                                
                    if statistics_element:
                        break
                        
                except Exception as e:
                    print(f"⚠️ Selector {selector} failed: {e}")
                    continue

            if not statistics_element:
                print("❌ Statistics Info section not found, trying to find any table...")
                # Fallback: look for any table
                try:
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for table in tables:
                        if table.is_displayed() and table.size['height'] > 100:
                            statistics_element = table
                            print("✅ Found table element as fallback")
                            break
                except Exception as e:
                    print(f"❌ Table fallback failed: {e}")

            if statistics_element:
                # Extract and parse statistics data first
                try:
                    print("📊 Extracting statistics data...")
                    statistics_text = statistics_element.text
                    print(f"📝 Raw statistics text:\n{statistics_text}")
                    
                    # Parse the statistics data and calculate TPS
                    tps_data = self.extract_statistics_and_calculate_tps(statistics_text)
                    if tps_data:
                        print("📈 TPS Calculation Results:")
                        for item in tps_data:
                            print(f"   📊 {item['metric']}: Max={item['max']}, TPS={item['tps']:.2f}")
                        
                        # Save TPS data to file
                        self.save_tps_data(tps_data)
                    else:
                        print("⚠️ No TPS data could be extracted")
                except Exception as e:
                    print(f"⚠️ Data extraction failed: {e}")
                
                # Scroll to the element to ensure it's visible
                self.driver.execute_script("arguments[0].scrollIntoView(true);", statistics_element)
                time.sleep(1)  # Reduced from 2 to 1

                # Generate filename for statistics screenshot
                timestamp = int(time.time())
                filename = f"statistics_info_{timestamp}.png"
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                filepath = os.path.join(project_root, "screenshots", filename)

                # Take screenshot of the statistics element
                statistics_element.screenshot(filepath)

                print(f"✅ Statistics Info captured: {filename}")
                print(f"📐 Captured area: {statistics_element.size['width']}x{statistics_element.size['height']}")

                return filepath,statistics_text
            else:
                print("❌ Could not find Statistics Info section")
                return None

        except Exception as e:
            print(f"❌ Statistics Info capture failed: {e}")
            return None
    
    def extract_statistics_and_calculate_tps(self, statistics_text):
        """
        Extract statistics data from the popup text and calculate TPS
        TPS = Max Trade Success / 60
        """
        try:
            import re
            
            # Split the text into lines and process
            lines = statistics_text.strip().split('\n')
            tps_data = []
            
            print("🔍 Parsing statistics data:")
            for line in lines:
                print(f"   📝 Line: {line}")
            
            # Look for data patterns - the format appears to be:
            # Column Max Min Average Total Count
            # metric_name max_value min_value avg_value total_value count_value
            
            data_started = False
            for i, line in enumerate(lines):
                # Skip header lines until we find actual data
                if 'Column' in line and 'Max' in line and 'Min' in line:
                    print(f"   📊 Found header at line {i}: {line}")
                    data_started = True
                    continue
                    
                if data_started and line.strip():
                    # Enhanced parsing for multi-word metrics
                    # Pattern: "Metric Name number.nn number.nn number.nn number.nn number"
                    # Use regex to capture metric name and numbers
                    pattern = r'^(.+?)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+)$'
                    match = re.match(pattern, line.strip())
                    
                    if match:
                        metric_name = match.group(1).strip()
                        max_value = float(match.group(2))
                        min_value = float(match.group(3))
                        avg_value = float(match.group(4))
                        total_value = float(match.group(5))
                        count_value = int(match.group(6))
                        
                        # Calculate TPS: max / 60
                        tps = max_value / 60
                        
                        result = {
                            'metric': metric_name,
                            'max': max_value,
                            'min': min_value,
                            'average': avg_value,
                            'total': total_value,
                            'count': count_value,
                            'tps': tps,
                            'raw_data': line.strip()
                        }
                        tps_data.append(result)
                        
                        print(f"   ✅ Parsed {metric_name}: Max={max_value}, TPS={tps:.2f}")
                    else:
                        print(f"   ⚠️ Could not parse line pattern: {line}")
            
            # Special handling for "Trade Success" metric for primary TPS calculation
            trade_success_tps = None
            for item in tps_data:
                if 'Trade Success' in item['metric']:
                    trade_success_tps = item['tps']
                    print(f"🎯 Primary TPS (Trade Success): {trade_success_tps:.2f}")
                    break
            
            return tps_data if tps_data else None
            
        except Exception as e:
            print(f"❌ TPS calculation failed: {e}")
            return None
    
    def save_tps_data(self, tps_data):
        """Save TPS data to a JSON file with timestamp"""
        try:
            import json
            from datetime import datetime
            
            # Create data structure with timestamp
            timestamp = datetime.now().isoformat()
            data_to_save = {
                'timestamp': timestamp,
                'capture_time': timestamp,
                'tps_calculations': tps_data
            }
            
            # Save to TPS data file
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            tps_file = os.path.join(project_root, "tps_data.json")
            
            # Load existing data if file exists
            existing_data = []
            if os.path.exists(tps_file):
                try:
                    with open(tps_file, 'r') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []
            
            # Append new data
            existing_data.append(data_to_save)
            
            # Keep only last 100 entries to prevent file from getting too large
            if len(existing_data) > 100:
                existing_data = existing_data[-100:]
            
            # Save updated data
            with open(tps_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            print(f"💾 TPS data saved to: {tps_file}")
            print(f"📊 Total TPS records: {len(existing_data)}")
            
        except Exception as e:
            print(f"❌ Failed to save TPS data: {e}")
    
    def capture_full_interface(self):
        """Capture Trade Trends chart with time range controls"""
        print("📸 Capturing Trade Trends with time range controls...")
        
        time.sleep(3)  # Wait for interface to load
        
        # Find the popup container with both time controls and chart
        try:
            container_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'xf-pop-up-container')]")
            
            # Verify it has the components we want
            has_date_inputs = len(container_element.find_elements(By.XPATH, ".//input[@placeholder='Date']")) > 0
            has_trade_trends = len(container_element.find_elements(By.XPATH, ".//span[contains(text(), 'Trade Trends')]")) > 0
            
            if has_date_inputs and has_trade_trends:
                # Generate filename
                timestamp = int(time.time())
                filename = f"trade_trends_with_timerange_{timestamp}.png"
                # Use absolute path to screenshots directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                filepath = os.path.join(project_root, "screenshots", filename)
                
                # Scroll to element and capture
                self.driver.execute_script("arguments[0].scrollIntoView(true);", container_element)
                time.sleep(2)
                container_element.screenshot(filepath)
                
                print(f"✅ Full interface captured: {filename}")
                print(f"📐 Captured area: {container_element.size['width']}x{container_element.size['height']}")
                
                return filepath
            else:
                print("⚠️  Container doesn't have expected components")
                return None
                
        except Exception as e:
            print(f"❌ Full interface capture failed: {e}")
            return None
    
    def run_automation(self, chart_only=False, statistics_only=False):
        """Execute the complete automation workflow"""
        try:
            print("📊 Trade Trends Dashboard Automation")
            print("=" * 50)
            
            # Setup browser
            self.setup_driver()
            
            # Login and setup
            if not self.login_and_setup():
                print("❌ Login failed")
                return None
            
            print("✅ Login and setup successful")
            
            # Click Trade Trends
            if not self.click_trade_trends():
                print("❌ Could not access Trade Trends")
                return None
                
            print("✅ Trade Trends accessed successfully")
            
            # Capture based on user preference
            if statistics_only:
                screenshot_path = self.capture_statistics_info()
                capture_type = "Statistics Info table"
            elif chart_only:
                screenshot_path = self.capture_chart_only()
                capture_type = "chart only"
            else:
                screenshot_path = self.capture_full_interface()
                capture_type = "full interface with time range"
                
            if screenshot_path:
                print(f"\n🎉 SUCCESS!")
                print(f"📸 Trade Trends {capture_type} captured successfully!")
                print(f"📁 File: {screenshot_path}")
                return screenshot_path
            else:
                print(f"❌ {capture_type} capture failed")
                return None
                
        except Exception as e:
            print(f"❌ Automation failed: {e}")
            return None
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Close browser and cleanup"""
        if self.driver:
            self.driver.quit()
            print("🔄 Browser closed")

def main():
    """Main execution function with command line arguments"""
    parser = argparse.ArgumentParser(description='Trade Trends Dashboard Automation')
    parser.add_argument('--chart-only', action='store_true', 
                       help='Capture only the chart (default: full interface)')
    parser.add_argument('--statistics-only', action='store_true',
                       help='Capture only the Statistics Info table')
    parser.add_argument('--tps-report', action='store_true',
                       help='Capture chart + statistics and send TPS report to DingTalk')
    parser.add_argument('--tps-actioncard', action='store_true',
                       help='Send TPS report using ActionCard format (rich visual)')
    parser.add_argument('--chart-actioncard', action='store_true',
                       help='Send only trade trends chart using ActionCard format')
    parser.add_argument('--chart-image', action='store_true',
                       help='Send trade trends chart as actual image via Enterprise API')
    parser.add_argument('--chart-static', action='store_true',
                       help='Send ActionCard with static image URL that displays inline')
    parser.add_argument('--headless', action='store_true', 
                       help='Run browser in background (default: visible)')
    parser.add_argument('--time-range', type=str, default=None,
                       help='Time range: "today" for current day, or "2025-11-05 00:00:00,2025-11-05 23:59:59" for specific range')
    
    args = parser.parse_args()
    
    # Create automation instance
    automation = TradeTrendsAutomation(headless=args.headless)
    
    if args.tps_report:
        # Complete TPS reporting workflow
        print("🚀 Starting Complete TPS Reporting...")
        print("=" * 50)
        
        # Initialize driver ONCE and keep it open for both captures
        automation.setup_driver()
        
        try:
            if not automation.login_and_setup():
                print("❌ Login failed")
                return
            
            if not automation.click_trade_trends():
                print("❌ Could not access Trade Trends")
                return
            
            # Set time range if provided
            if args.time_range:
                if not automation.set_time_range(args.time_range):
                    print("❌ Failed to set time range")
                    return
            
            # Step 1: Capture trade trends chart
            print("📈 Step 1: Capturing Trade Trends chart...")
            chart_result = automation.capture_chart_only()
            
            if not chart_result:
                print("❌ Failed to capture trade trends chart")
                return
            
            print(f"✅ Chart captured: {chart_result}")
            
            # Step 2: Capture statistics and calculate TPS (same browser session)
            print("\n📊 Step 2: Capturing Statistics and calculating TPS...")
            
            # Instead of complex clicking, just reload the page and get statistics directly
            # Or better: use run_automation with statistics_only to properly capture
            stats_result = automation.run_automation(chart_only=False, statistics_only=True)
            
            if not stats_result:
                print("❌ Failed to capture statistics")
                return
            
            # Handle both tuple and non-tuple returns
            if isinstance(stats_result, tuple):
                stats_result, statistics_text = stats_result
            else:
                stats_result = stats_result
                statistics_text = None
                
            print(f"✅ Statistics captured: {stats_result}")
            
            # Step 3: Load TPS data
            print("\n📈 Step 3: Loading TPS data...")
            tps_data = None
            tps_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tps_data.json")
            
            if os.path.exists(tps_file):
                try:
                    with open(tps_file, 'r') as f:
                        data = json.load(f)
                    if data:
                        tps_data = data[-1]['tps_calculations']  # Get latest TPS data
                        print(f"✅ TPS data loaded: {len(tps_data)} metrics")
                except Exception as e:
                    print(f"⚠️ Could not load TPS data: {e}")
            
            # Step 4: Send to DingTalk
            print("\n📤 Step 4: Sending TPS report to DingTalk...")
            try:
                # Import DingTalk sender
                sys.path.append(os.path.dirname(__file__))
                from dingtalk_sender import DingTalkSender
                
                sender = DingTalkSender()
                success = sender.send_tps_report(chart_result, stats_result, tps_data)
                
                if success:
                    print("🎉 Complete TPS Report sent to DingTalk successfully!")
                else:
                    print("❌ Failed to send TPS Report to DingTalk")
                    
            except ImportError as e:
                print(f"❌ Could not import DingTalk sender: {e}")
            except Exception as e:
                print(f"❌ Error sending to DingTalk: {e}")
            
            print("🔄 Automation completed")
            
        finally:
            # Close browser properly
            if automation.driver:
                automation.driver.quit()
                print("🔄 Browser closed")
        
    elif args.tps_actioncard:
        # ActionCard TPS reporting workflow
        print("🚀 Starting ActionCard TPS Reporting...")
        print("=" * 50)
        
        # Step 1: Capture trade trends chart
        print("📈 Step 1: Capturing Trade Trends chart...")
        chart_result = automation.run_automation(chart_only=False, statistics_only=False)
        
        if not chart_result:
            print("❌ Failed to capture trade trends chart")
            return
        
        print(f"✅ Chart captured: {chart_result}")
        
        # Step 2: Capture statistics and calculate TPS  
        print("\n📊 Step 2: Capturing Statistics and calculating TPS...")
        stats_result = automation.run_automation(chart_only=False, statistics_only=True)
        
        if not stats_result:
            print("❌ Failed to capture statistics")
            return
            
        print(f"✅ Statistics captured: {stats_result}")
        
        # Step 3: Load TPS data
        print("\n📈 Step 3: Loading TPS data...")
        tps_data = None
        tps_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tps_data.json")
        
        if os.path.exists(tps_file):
            try:
                with open(tps_file, 'r') as f:
                    data = json.load(f)
                if data:
                    tps_data = data[-1]['tps_calculations']  # Get latest TPS data
                    print(f"✅ TPS data loaded: {len(tps_data)} metrics")
            except Exception as e:
                print(f"⚠️ Could not load TPS data: {e}")
        
        # Step 4: Send ActionCard to DingTalk
        print("\n📤 Step 4: Sending ActionCard TPS report to DingTalk...")
        try:
            # Import DingTalk sender
            sys.path.append(os.path.dirname(__file__))
            from dingtalk_sender import DingTalkSender
            
            sender = DingTalkSender()
            success = sender.send_tps_actioncard_report(chart_result, stats_result, tps_data)
            
            if success:
                print("🎉 ActionCard TPS Report sent to DingTalk successfully!")
            else:
                print("❌ Failed to send ActionCard TPS Report to DingTalk")
                
        except ImportError as e:
            print(f"❌ Could not import DingTalk sender: {e}")
        except Exception as e:
            print(f"❌ Error sending ActionCard to DingTalk: {e}")
        
        print("🔄 ActionCard automation completed")
        
    elif args.chart_actioncard:
        # Chart-only ActionCard workflow
        print("🚀 Starting Chart-only ActionCard...")
        print("=" * 50)
        
        # Capture trade trends chart
        print("📈 Capturing Trade Trends chart...")
        chart_result = automation.run_automation(chart_only=False, statistics_only=False)
        
        if not chart_result:
            print("❌ Failed to capture trade trends chart")
            return
        
        print(f"✅ Chart captured: {chart_result}")
        
        # Send Chart ActionCard to DingTalk
        print("\n📤 Sending Chart ActionCard to DingTalk...")
        try:
            # Import DingTalk sender
            sys.path.append(os.path.dirname(__file__))
            from dingtalk_sender import DingTalkSender
            
            sender = DingTalkSender()
            success = sender.send_chart_actioncard(chart_result)
            
            if success:
                print("🎉 Chart ActionCard sent to DingTalk successfully!")
            else:
                print("❌ Failed to send Chart ActionCard to DingTalk")
                
        except ImportError as e:
            print(f"❌ Could not import DingTalk sender: {e}")
        except Exception as e:
            print(f"❌ Error sending Chart ActionCard to DingTalk: {e}")
        
        print("🔄 Chart ActionCard automation completed")
        
    elif args.chart_image:
        # Chart as actual image workflow
        print("🚀 Starting Chart Image Upload...")
        print("=" * 50)
        
        # Capture trade trends chart
        print("📈 Capturing Trade Trends chart...")
        chart_result = automation.run_automation(chart_only=False, statistics_only=False)
        
        if not chart_result:
            print("❌ Failed to capture trade trends chart")
            return
        
        print(f"✅ Chart captured: {chart_result}")
        
        # Send Chart as Image to DingTalk
        print("\n📤 Sending Chart as Image to DingTalk...")
        try:
            # Import DingTalk sender
            sys.path.append(os.path.dirname(__file__))
            from dingtalk_sender import DingTalkSender
            
            sender = DingTalkSender()
            success = sender.send_chart_with_image(chart_result)
            
            if success:
                print("🎉 Chart Image sent to DingTalk successfully!")
            else:
                print("❌ Failed to send Chart Image to DingTalk")
                
        except ImportError as e:
            print(f"❌ Could not import DingTalk sender: {e}")
        except Exception as e:
            print(f"❌ Error sending Chart Image to DingTalk: {e}")
        
        print("🔄 Chart Image automation completed")
        
    elif args.chart_static:
        # Chart with static image URL in ActionCard workflow
        print("🚀 Starting Chart Static Image ActionCard...")
        print("=" * 50)
        
        # Capture trade trends chart
        print("📈 Capturing Trade Trends chart...")
        chart_result = automation.run_automation(chart_only=False, statistics_only=False)
        
        if not chart_result:
            print("❌ Failed to capture trade trends chart")
            return
        
        print(f"✅ Chart captured: {chart_result}")
        
        # Send Chart with Static Image URL to DingTalk
        print("\n📤 Sending ActionCard with Static Image URL to DingTalk...")
        try:
            # Import DingTalk sender
            sys.path.append(os.path.dirname(__file__))
            from dingtalk_sender import DingTalkSender
            
            sender = DingTalkSender()
            success = sender.send_actioncard_with_static_image(chart_result)
            
            if success:
                print("🎉 ActionCard with Static Image sent to DingTalk successfully!")
            else:
                print("❌ Failed to send ActionCard with Static Image to DingTalk")
                
        except ImportError as e:
            print(f"❌ Could not import DingTalk sender: {e}")
        except Exception as e:
            print(f"❌ Error sending ActionCard with Static Image to DingTalk: {e}")
        
        print("🔄 Chart Static Image ActionCard automation completed")
        
    else:
        # Original single capture workflow
        result = automation.run_automation(chart_only=args.chart_only, statistics_only=args.statistics_only)
        
        if result:
            if args.statistics_only:
                capture_type = "Statistics Info table"
            elif args.chart_only:
                capture_type = "chart"
            else:
                capture_type = "full interface"
            print(f"\n✅ Success! Trade Trends {capture_type} captured at: {result}")
        else:
            print("\n❌ Failed to capture Trade Trends dashboard")

if __name__ == "__main__":
    main()