#!/usr/bin/env python3
"""
Simplified Trade Trends Automation - Single Flow
Login -> Trade Trends -> Screenshot -> Statistics -> TPS Data -> Send to DingTalk
"""

import sys
import os
import time
import requests
import json
import base64
import hashlib
import hmac
import argparse
from urllib.parse import quote_plus
from datetime import datetime

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
automation_dir = os.path.join(project_root, "automation")
credentials_dir = os.path.join(project_root, "credentials")

sys.path.insert(0, automation_dir)
sys.path.insert(0, credentials_dir)

from trade_trends_final import TradeTrendsAutomation
from dingtalk_credentials import DINGTALK_WEBHOOK_URL, DINGTALK_WEBHOOK_SECRET, BROWSER_HEADLESS

def send_to_dingtalk(image_url, tps_data, time_range=None):
    """Send TPS report with image to DingTalk"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_default_time = False
    
    # Determine time range text for the report
    if time_range:
        if time_range.lower() == "today":
            today = datetime.now().strftime("%Y-%m-%d")
            time_range_text = f"{today} 00:00:00 to {today} 23:59:59"
        else:
            time_range_text = time_range.replace(',', ' to ')
    else:
        time_range_text = "Default (Current)"
        is_default_time = True
    
    # Format TPS data for message
    tps_text = ""
    if tps_data:
        for item in tps_data:
            metric = item.get('metric', 'Unknown')
            tps = item.get('tps', 0)
            max_val = item.get('max', 0)
            tps_text += f"TPS {metric}: {tps:.0f}  (Max: {max_val:.0f})\n\n"
    
    # Build payload
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": "Trade Trends Report",
            "text": (
                f"TRADE TRENDS REPORT\n"
                f"{'='*30}\n"
                f"{'🕐 Report Time: ' + current_time  if is_default_time else '📅 Data Range: ' + time_range_text } \n\n"
                f"![]({image_url})\n\n"
                f"📈 TPS CALCULATIONS:\n\n"
                f"{tps_text}\n\n\n"
                f"<font color=\"red\">**NOTE : IR Team please recheck again if there are anomalies.**</font>\n"
                f"@+62-82165825841\n"
                f"[For more details, click here](https://monitor.paas.dana.id/optimus/#/STZEYPCN/prod/business/product/cms/preview/354)."
            )
        },
        "at": {
            "isAtAll": False,
            "atMobiles": ["+62-82165825841"]
        }
    }
    
    # Send via webhook
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{DINGTALK_WEBHOOK_SECRET}"
    hmac_code = hmac.new(
        DINGTALK_WEBHOOK_SECRET.encode('utf-8'),
        string_to_sign.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sign = quote_plus(base64.b64encode(hmac_code))
    
    final_url = f"{DINGTALK_WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
    
    try:
        response = requests.post(final_url, json=payload)
        result = response.json()
        
        if result.get('errcode') == 0:
            print("✅ Message sent to DingTalk successfully!")
            return True
        else:
            print(f"❌ Failed to send message: {result}")
            return False
    except Exception as e:
        print(f"❌ Error sending to DingTalk: {e}")
        return False

def main(time_range=None):
    """Main automation flow"""
    print("🚀 Starting Trade Trends Automation...")
    print("=" * 50)
    
    if time_range:
        print(f"⏰ Time range: {time_range}")
    
    # Initialize automation with headless setting from credentials
    automation = TradeTrendsAutomation(headless=BROWSER_HEADLESS)
    
    try:
        # Step 1: Setup browser
        print("\n� Step 1: Setting up browser...")
        automation.setup_driver()
        
        # Step 2: Login
        print("🔐 Step 2: Login to XFlush...")
        if not automation.login_and_setup():
            print("❌ Login failed")
            return False
        
        # Step 3: Navigate to Trade Trends
        print("📊 Step 3: Navigating to Trade Trends...")
        if not automation.click_trade_trends():
            print("❌ Could not access Trade Trends")
            return False
        
        #time.sleep(3)  # Wait for page to load
        
        # Step 3.5: Set time range if provided
        if time_range:
            print(f"⏰ Step 3.5: Setting time range to '{time_range}'...")
            if not automation.set_time_range(time_range):
                print("❌ Failed to set time range")
                return False
            print("✅ Time range set successfully")
            #time.sleep(2)  # Wait for chart to update
        
        # Step 4: Capture chart screenshot
        print("📈 Step 4: Capturing Trade Trends chart...")
        chart_path = automation.capture_chart_only()
        if not chart_path:
            print("❌ Failed to capture chart")
            return False
        print(f"✅ Chart captured: {chart_path}")
        
        # Step 5: Capture statistics screenshot and extract TPS data
        print("📊 Step 5: Capturing statistics and extracting TPS data...")
        stats_capture = automation.capture_statistics_info()
        
        if not stats_capture:
            print("❌ Failed to capture statistics")
            return False
        
        # Handle return value (could be tuple or single value)
        if isinstance(stats_capture, tuple):
            stats_path, statistics_text = stats_capture
        else:
            stats_path = stats_capture
            statistics_text = None
        
        print(f"✅ Statistics captured: {stats_path}")
        
        # Extract TPS data
        tps_data = None
        if statistics_text:
            tps_data = automation.extract_statistics_and_calculate_tps(statistics_text)
            print(f"✅ TPS data extracted: {len(tps_data) if tps_data else 0} metrics")
        else:
            # Try loading from file as fallback
            tps_file = os.path.join(project_root, "tps_data.json")
            if os.path.exists(tps_file):
                try:
                    with open(tps_file, 'r') as f:
                        data = json.load(f)
                    if data:
                        tps_data = data[-1].get('tps_calculations', [])
                        print(f"✅ TPS data loaded from file: {len(tps_data)} metrics")
                except Exception as e:
                    print(f"⚠️ Could not load TPS data from file: {e}")
        
        # Step 6: Upload screenshot to DingTalk
        print("📤 Step 6: Uploading screenshot to DingTalk...")
        
        # Get access token
        url = "https://oapi.dingtalk.com/gettoken"
        params = {
            'appkey': 'dingih5yqjdxxw8ghaqe',
            'appsecret': 'oGhCniLiOI-pZL9kVlQ-c68Td_0BgncdUGtx3c8etIUkss7E0U3x4HRClnvuh0J6'
        }
        response = requests.get(url, params=params)
        result = response.json()
        
        if result.get('errcode') != 0:
            print(f"❌ Failed to get access token: {result}")
            return False
        
        access_token = result['access_token']
        
        # Upload image
        upload_url = "https://oapi.dingtalk.com/media/upload"
        upload_params = {'access_token': access_token, 'type': 'image'}
        
        with open(chart_path, 'rb') as f:
            file_data = f.read()
        
        boundary = '----WebKitFormBoundary' + str(int(time.time()))
        form_data = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="type"\r\n\r\n'
            f'image\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="media"; filename="chart.png"\r\n'
            f'Content-Type: image/png\r\n\r\n'
        ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
        
        headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
        response = requests.post(upload_url, params=upload_params, data=form_data, headers=headers)
        
        upload_result = response.json()
        if upload_result.get('errcode') != 0:
            print(f"❌ Upload failed: {upload_result}")
            return False
        
        media_id = upload_result['media_id']
        print(f"✅ Image uploaded! Media ID: {media_id}")
        
        # Step 7: Generate download URL and send to DingTalk
        print("📨 Step 7: Sending report to DingTalk...")
        download_url = f"https://oapi.dingtalk.com/media/downloadFile?access_token={access_token}&media_id={media_id}"
        
        success = send_to_dingtalk(download_url, tps_data, time_range)
        
        if success:
            # Delete screenshot files after successful send
            print("🗑️  Cleaning up screenshots...")
            try:
                if os.path.exists(chart_path):
                    os.remove(chart_path)
                    print(f"   ✅ Deleted: {os.path.basename(chart_path)}")
                
                if stats_path and os.path.exists(stats_path):
                    os.remove(stats_path)
                    print(f"   ✅ Deleted: {os.path.basename(stats_path)}")
            except Exception as e:
                print(f"   ⚠️  Failed to delete some files: {e}")
            
            print("\n" + "=" * 50)
            print("🎉 AUTOMATION COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"💥 Automation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Close browser
        try:
            if automation.driver:
                automation.driver.quit()
                print("🔄 Browser closed")
        except:
            pass

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Trade Trends Automation')
    parser.add_argument('--time-range', 
                        type=str, 
                        help='Time range for the report. Use "today" for current day (00:00:00 to 23:59:59), '
                             'or specify custom range as "YYYY-MM-DD HH:MM:SS,YYYY-MM-DD HH:MM:SS"')
    
    args = parser.parse_args()
    
    success = main(time_range=args.time_range)
    sys.exit(0 if success else 1)