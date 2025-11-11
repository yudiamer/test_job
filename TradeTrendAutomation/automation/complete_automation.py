#!/usr/bin/env python3


import requests
import json
import base64
import hashlib
import hmac
import time
from urllib.parse import quote_plus
import argparse
import os
import subprocess
import sys
from datetime import datetime
from trade_trends_final import TradeTrendsAutomation


# Add credentials directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
credentials_dir = os.path.join(project_root, "credentials")
sys.path.insert(0, credentials_dir)

from credentials_loader import get_dingtalk_credentials

class XFlushCompleteAutomation:
    def __init__(self, credentials=None):
        # Load DingTalk credentials from file
        if credentials is None:
            credentials = get_dingtalk_credentials()
        
        self.client_id = credentials['client_id']
        self.client_secret = credentials['client_secret']
        self.webhook_url = credentials['webhook_url']
        self.webhook_secret = credentials['webhook_secret']
        
        # Set screenshots directory relative to project root
        self.screenshots_dir = os.path.join(project_root, "screenshots")
        
        # Ensure screenshots directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def get_access_token(self):
        """Get enterprise access token"""
        url = "https://oapi.dingtalk.com/gettoken"
        params = {
            'appkey': self.client_id,
            'appsecret': self.client_secret
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result.get('errcode') == 0:
            return result['access_token']
        else:
            raise Exception(f"Failed to get access token: {result}")
    
    def capture_screenshot(self, capture_type="full", headless=False):
        """Capture Trade Trends screenshot with specified type, using unique filename for parallel runs"""
        import uuid
        try:
            command = ['python3', 'trade_trends_final.py']
            
            if capture_type == "statistics":
                print("📊 Capturing Trade Trends Statistics Info...")
                command.append('--statistics-only')
                pattern = "statistics_info_"
            elif capture_type == "chart":
                print("📈 Capturing Trade Trends chart...")
                command.append('--chart-only')
                pattern = "trade_trends_chart_"
            else:
                print("📸 Capturing Trade Trends full interface...")
                pattern = "trade_trends_with_timerange_"
            
            # Add unique id to filename via env var
            unique_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
            os.environ["TRADE_TRENDS_SCREENSHOT_ID"] = unique_id
            
            if headless:
                command.append('--headless')
                print("🖥️  Running in headless mode")
            else:
                print("🖥️  Running in visible mode")
            
            # Run the working trade trends automation
            result = subprocess.run(command, capture_output=True, text=True, 
                                  cwd=os.path.dirname(os.path.abspath(__file__)))
            
            # Screenshot filename with unique id
            expected_filename = f"{pattern}{unique_id}.png"
            expected_path = os.path.join(self.screenshots_dir, expected_filename)
            if result.returncode == 0 and os.path.exists(expected_path):
                print(f"✅ Screenshot captured: {expected_path}")
                return expected_path
            else:
                # Fallback: find most recent matching file
                screenshot_files = [f for f in os.listdir(self.screenshots_dir) 
                                  if f.startswith(pattern) and f.endswith('.png')]
                if screenshot_files:
                    screenshot_files.sort(key=lambda x: os.path.getctime(os.path.join(self.screenshots_dir, x)), reverse=True)
                    latest_screenshot = os.path.join(self.screenshots_dir, screenshot_files[0])
                    print(f"📁 Latest screenshot: {latest_screenshot}")
                    return latest_screenshot
                print("❌ Screenshot file not found!")
                print(f"Error: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Screenshot capture error: {e}")
            return None
    
    def upload_media(self, image_path, access_token):
        """Upload image to DingTalk media API"""
        url = "https://oapi.dingtalk.com/media/upload"
        params = {'access_token': access_token, 'type': 'image'}
        
        with open(image_path, 'rb') as f:
            file_data = f.read()
        
        filename = os.path.basename(image_path)
        boundary = '----WebKitFormBoundary' + str(int(time.time()))
        
        form_data = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="type"\r\n\r\n'
            f'image\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="media"; filename="{filename}"\r\n'
            f'Content-Type: image/png\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
        response = requests.post(url, params=params, data=form_data, headers=headers)
        
        result = response.json()
        
        if result.get('errcode') == 0:
            media_id = result['media_id']
            print(f"✅ Image uploaded! Media ID: {media_id}")
            return media_id
        else:
            raise Exception(f"Upload failed: {result}")
    
    def delete_media(self, media_id, access_token):
        """Delete image from DingTalk media storage"""
        try:
            print(f"🗑️ Cleaning up media storage...")
            
            # DingTalk media delete API
            url = "https://oapi.dingtalk.com/media/delete"
            params = {
                'access_token': access_token,
                'media_id': media_id
            }
            
            response = requests.post(url, params=params)
            result = response.json()
            
            if result.get('errcode') == 0:
                print(f"✅ Media {media_id} deleted from DingTalk storage")
                return True
            else:
                print(f"⚠️ Media deletion warning: {result}")
                # Don't fail the whole process if deletion fails
                return False
                
        except Exception as e:
            print(f"⚠️ Media deletion error: {e}")
            # Don't fail the whole process if deletion fails
            return False
    
    def send_webhook_message(self, payload):
        """Send message via webhook"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{self.webhook_secret}"
        hmac_code = hmac.new(
            self.webhook_secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        
        final_url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
        
        response = requests.post(final_url, json=payload)
        return response.json()
    
    def send_clean_image(self, image_path, access_token, media_id):
        """Send image with clean display (no buttons)"""
        try:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            download_url = f"https://oapi.dingtalk.com/media/downloadFile?access_token={access_token}&media_id={media_id}"
            
            # Clean ActionCard with no click functionality - just displays image beautifully
            payload = {
            "msgtype": "markdown",
            "markdown": {
            "title": "Project Update",
            "text": f"TRADE TRENDS REPORT\n==============================\n🕐 Time: {current_time}\n\n" +
            f"![]({download_url})\n" +
            "TPS CALCULATIONS:\n\n Trade Success: 250.00 \n\nTPS (Max: 15000)\n\n Payment Apply: 180.00 \n\nTPS (Max: 10800)\n\n Cashier Consult: 120.00 \n\nTPS (Max: 7200)\n\n PRIMARY TPS: 250.00\n\n Trade Success Max: 15000\n\n"+
            "<font color=\"red\">**NOTE : IR Team please recheck again if there are anomalies.**</font>" +
            "\n\n\nFor more details, click [here](https://www.google.com)."
            },
             "at": {
             "atUserIds": ["6282165825841"],
             "isAtAll": False
          }
           
        }
            
            print("📨 Sending clean image display...")
            result = self.send_webhook_message(payload)
            
            if result.get('errcode') == 0:
                print("✅ Image sent successfully!")
                return True
            else:
                print(f"❌ Failed to send image: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Send image error: {e}")
            return False
    
    def run_complete_automation(self, cleanup_media=True, capture_type="full", headless=False):
        """Run the complete automation with optional media cleanup and capture type"""
        try:
            if capture_type == "statistics":
                print("🚀 Starting Complete XFlush Statistics Automation...")
            else:
                print("🚀 Starting Complete XFlush Automation...")
            print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Capture type: {capture_type}")
            print(f"🖥️  Browser mode: {'Headless' if headless else 'Visible'}")
            print(f"🗑️ Media cleanup: {'Enabled' if cleanup_media else 'Disabled'}")
            print("-" * 50)
            
            # Step 1: Capture screenshot with specified type
            screenshot_path = self.capture_screenshot(capture_type, headless)
            if not screenshot_path:
                print("💥 Automation failed at screenshot capture step")
                return False
            
            print("-" * 30)

            automation = TradeTrendsAutomation(headless=headless)

            # Add this step:
            statistics_screenshot_path = automation.capture_statistics_info()
            if statistics_screenshot_path:
                # After capturing, extract statistics text from the element
                # You may need to modify capture_statistics_info to also return statistics_text
                # For example:
                # statistics_screenshot_path, statistics_text = automation.capture_statistics_info()
                # Then:
                # tps_data = automation.extract_statistics_and_calculate_tps(statistics_text)

                print(f"✅ Statistics screenshot saved at: {statistics_screenshot_path}")
            else:
                print("❌ Failed to capture statistics info")

            statistics_screenshot_path, statistics_text = automation.capture_statistics_info()
            tps_data = automation.extract_statistics_and_calculate_tps(statistics_text)
            print(tps_data)


            
            # Step 2: Get access token and upload image
            access_token = self.get_access_token()
            media_id = self.upload_media(screenshot_path, access_token)
            
            # Step 3: Send to DingTalk
            success = self.send_clean_image(screenshot_path, access_token, media_id)
            if not success:
                print("💥 Automation failed at DingTalk sending step")
                return False
            
            print("-" * 30)
            
            # Step 4: Optional media cleanup
            if cleanup_media:
                # Wait a bit to ensure message is delivered before deleting
                print("⏳ Waiting 5 seconds before cleanup...")
                #time.sleep(3)
                self.delete_media(media_id, access_token)
            else:
                print("ℹ️ Media cleanup skipped - image remains in DingTalk storage")
            
            print("-" * 50)
            print("🎉 COMPLETE AUTOMATION SUCCESS!")
            print("📱 Check your DingTalk group chat:")
            print("   👀 You'll see the clean Trade Trends image")
            print("   🖼️ Perfect display with no buttons or clutter")
            if cleanup_media:
                print("   🗑️ Media automatically cleaned up from DingTalk storage")
            
            return True
            
        except Exception as e:
            print(f"💥 Complete automation error: {e}")
            return False
    
    def run_statistics_automation(self, cleanup_media=True, headless=False):
        """Run the statistics automation workflow"""
        return self.run_complete_automation(cleanup_media=cleanup_media, capture_type="statistics", headless=headless)

def main():
    parser = argparse.ArgumentParser(description="Complete XFlush Trade Trends Automation with Media Cleanup")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't delete media from DingTalk storage")
    parser.add_argument("--test", help="Test mode - use existing screenshot file")
    
    args = parser.parse_args()
    
    automation = XFlushCompleteAutomation(
        'dingih5yqjdxxw8ghaqe',
        'oGhCniLiOI-pZL9kVlQ-c68Td_0BgncdUGtx3c8etIUkss7E0U3x4HRClnvuh0J6'
    )
    
    if args.test:
        # Test mode with existing screenshot
        print("🧪 Running in test mode...")
        try:
            access_token = automation.get_access_token()
            media_id = automation.upload_media(args.test, access_token)
            success = automation.send_clean_image(args.test, access_token, media_id)
            
            if success and not args.no_cleanup:
                #time.sleep(3)
                automation.delete_media(media_id, access_token)
                
            print("✅ Test completed!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        # Full automation
        success = automation.run_complete_automation(cleanup_media=not args.no_cleanup)
        if success:
            print("\n✨ Automation completed successfully!")
        else:
            print("\n💥 Automation failed!")

if __name__ == "__main__":
    main()