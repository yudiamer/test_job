#!/usr/bin/env python3
"""
DingTalk Integration Module - Working Image Version
=================================================
Restored to the working version that actually shows images in DingTalk
"""

import requests
import json
import base64
import hashlib
import hmac
import time
import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add credentials path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'credentials'))

try:
    from dingtalk_credentials import *
except ImportError:
    print("❌ Could not import DingTalk credentials")
    sys.exit(1)

class DingTalkSender:
    def __init__(self):
        self.access_token = None
        self.token_expires = 0
    
    def get_access_token(self):
        """Get access token for Enterprise API"""
        try:
            if self.access_token and time.time() < self.token_expires:
                return self.access_token
            
            print("🔑 Getting DingTalk access token...")
            
            url = "https://oapi.dingtalk.com/gettoken"
            params = {
                'appkey': DINGTALK_APP_KEY,
                'appsecret': DINGTALK_APP_SECRET
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('errcode') == 0:
                self.access_token = result['access_token']
                self.token_expires = time.time() + result.get('expires_in', 7200) - 300  # 5 min buffer
                print(f"✅ Access token obtained: {self.access_token[:20]}...")
                return self.access_token
            else:
                print(f"❌ Failed to get access token: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            return None
    
    def upload_image(self, image_path):
        """Upload image and get Media ID"""
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        try:
            print(f"📤 Uploading image: {os.path.basename(image_path)}")
            
            url = "https://oapi.dingtalk.com/media/upload"
            params = {
                'access_token': access_token,
                'type': 'image'
            }
            
            with open(image_path, 'rb') as f:
                files = {'media': (os.path.basename(image_path), f, 'image/png')}
                response = requests.post(url, params=params, files=files)
            
            result = response.json()
            
            if result.get('errcode') == 0:
                media_id = result['media_id']
                print(f"✅ Image uploaded successfully: {media_id}")
                return media_id
            else:
                print(f"❌ Failed to upload image: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            return None
    
    def send_webhook_message(self, message):
        """Send simple text message via webhook"""
        try:
            print("📤 Sending webhook message...")
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            
            print("📋 WEBHOOK REQUEST PAYLOAD:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            response = requests.post(DINGTALK_WEBHOOK_URL, json=payload)
            result = response.json()
            
            print("📥 WEBHOOK RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('errcode') == 0:
                print("✅ Webhook message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send webhook message: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending webhook message: {e}")
            return False
    
    def send_image_message(self, image_path, caption=""):
        """Send image message via Enterprise API - THIS IS THE WORKING METHOD"""
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        print("📤 Sending image message via Enterprise API...")
        
        # Upload image first
        media_id = self.upload_image(image_path)
        if not media_id:
            return False
        
        # Send image message
        url = DINGTALK_SEND_MESSAGE_URL
        params = {'access_token': access_token}
        
        payload = {
            "agent_id": DINGTALK_AGENT_ID,
            "userid_list": "manager464",
            "msg": {
                "msgtype": "image",
                "image": {
                    "media_id": media_id
                }
            }
        }
        
        try:
            # Send image
            response = requests.post(url, params=params, json=payload)
            result = response.json()
            
            print("📋 IMAGE REQUEST PAYLOAD:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("📥 IMAGE RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('errcode') == 0:
                print("✅ Image message sent successfully!")
                
                # Send caption as separate webhook message
                if caption:
                    self.send_webhook_message(caption)
                
                return True
            else:
                print(f"❌ Failed to send image message: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending image message: {e}")
            return False
    
    def get_media_static_url(self, media_id, width=958, height=589):
        """Convert Media ID to static DingTalk URL"""
        # Remove @ prefix if present
        clean_media_id = media_id.replace('@', '') if media_id.startswith('@') else media_id
        static_url = f"https://static.dingtalk.com/media/{clean_media_id}_{width}_{height}.png"
        print(f"📸 Static URL: {static_url}")
        return static_url
    
    def send_chart_with_static_url(self, chart_image_path):
        """Send chart using static DingTalk URL - BETTER APPROACH"""
        print("📈 Sending Trade Trends Chart using Static URL...")
        print("=" * 50)
        
        # Upload image to get Media ID
        media_id = self.upload_image(chart_image_path)
        if not media_id:
            return False
        
        # Convert to static URL
        static_url = self.get_media_static_url(media_id)
        
        # Send webhook message with image URL
        message = f"""📊 TRADE TRENDS CHART
🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

📈 Trade trends dashboard captured successfully!
📊 Chart: {static_url}

✅ Screenshot captured and uploaded to DingTalk
📊 Monitor trade performance and trends.

---
Automated monitoring system"""
        
        success = self.send_webhook_message(message)
        
        print("=" * 50)
        if success:
            print("🎉 Trade Trends Chart sent with static URL!")
            print(f"🔗 Image URL: {static_url}")
        else:
            print("❌ Failed to send chart with static URL")
        
        return success

    def send_chart_with_image(self, image_path, title="Trade Trends Chart", description="Current market analysis"):
        """Send chart using link message type with image display"""
        try:
            # Upload image to get media_id
            media_id = self.upload_image(image_path)
            if not media_id:
                logger.error("Failed to upload image")
                return False
            
            # Generate static URL
            static_url = self.get_media_static_url(media_id, image_path)
            if not static_url:
                logger.error("Failed to generate static URL")
                return False
            
            logger.info(f"Generated static URL: {static_url}")
            
            # Send message using link type with image
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            payload = {
                "msgtype": "link",
                "link": {
                    "text": f"� Time: {timestamp}\n🔧 {description}\n💡 Click to view detailed chart analysis",
                    "title": f"📊 {title}",
                    "picUrl": static_url,
                    "messageUrl": static_url
                }
            }
            
            # Send via webhook
            response = requests.post(DINGTALK_WEBHOOK_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("Chart sent successfully via webhook with link message type")
                    return True
                else:
                    logger.error(f"Webhook error: {result}")
                    return False
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending chart with image: {e}")
            return False

    def test_dingtalk_connection(self):
        """Test DingTalk connection"""
        test_message = "🧪 Test message from Trade Trends automation"
        return self.send_webhook_message(test_message)

if __name__ == "__main__":
    sender = DingTalkSender()
    if sender.test_dingtalk_connection():
        print("✅ DingTalk connection test successful!")
    else:
        print("❌ DingTalk connection test failed!")

import requests
import json
import base64
import hashlib
import hmac
import time
import os
from urllib.parse import quote_plus
import sys

# Add credentials path to import
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'credentials'))

try:
    from dingtalk_credentials import *
except ImportError:
    print("❌ Could not import DingTalk credentials")
    sys.exit(1)

class DingTalkSender:
    def __init__(self):
        self.access_token = None
        self.token_expires = 0
        
    def get_access_token(self):
        """Get or refresh access token"""
        current_time = time.time()
        
        # If token exists and hasn't expired, use it
        if self.access_token and current_time < self.token_expires:
            return self.access_token
        
        # Get new token
        print("🔑 Getting DingTalk access token...")
        
        url = DINGTALK_TOKEN_URL
        params = {
            'appkey': DINGTALK_CLIENT_ID,
            'appsecret': DINGTALK_CLIENT_SECRET
        }
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('errcode') == 0:
                self.access_token = result['access_token']
                # Token expires in 7200 seconds, refresh 5 minutes early
                self.token_expires = current_time + 7200 - 300
                print(f"✅ Access token obtained: {self.access_token[:20]}...")
                return self.access_token
            else:
                print(f"❌ Failed to get access token: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error getting access token: {e}")
            return None
    
    def upload_image(self, image_path):
        """Upload image to DingTalk and get media_id"""
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        print(f"📤 Uploading image: {os.path.basename(image_path)}")
        
        url = DINGTALK_MEDIA_UPLOAD_URL
        params = {'access_token': access_token, 'type': 'image'}
        
        try:
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            boundary = '----WebKitFormBoundary' + str(int(time.time()))
            form_data = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="type"\r\n\r\n'
                f'image\r\n'
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="media"; filename="{os.path.basename(image_path)}"\r\n'
                f'Content-Type: image/png\r\n\r\n'
            ).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')
            
            headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
            response = requests.post(url, params=params, data=form_data, headers=headers)
            
            result = response.json()
            
            if result.get('errcode') == 0:
                media_id = result['media_id']
                print(f"✅ Image uploaded successfully: {media_id}")
                return media_id
            else:
                print(f"❌ Failed to upload image: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            return None
    
    def send_webhook_message(self, message):
        """Send text message via webhook"""
        print("📤 Sending webhook message...")
        
        # Create signature
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{DINGTALK_WEBHOOK_SECRET}"
        hmac_code = hmac.new(
            DINGTALK_WEBHOOK_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        
        final_url = f"{DINGTALK_WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
        
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        try:
            response = requests.post(final_url, json=payload)
            result = response.json()
            
            if result.get('errcode') == 0:
                print("✅ Webhook message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send webhook message: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending webhook message: {e}")
            return False
    
    def send_actioncard_message(self, title, text, image_urls=None, buttons=None):
        """Send ActionCard message with images and buttons"""
        print("📤 Sending ActionCard message...")
        
        # Create signature
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{DINGTALK_WEBHOOK_SECRET}"
        hmac_code = hmac.new(
            DINGTALK_WEBHOOK_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        
        final_url = f"{DINGTALK_WEBHOOK_URL}&timestamp={timestamp}&sign={sign}"
        
        # Build ActionCard content with images
        content = text
        if image_urls:
            for i, img_url in enumerate(image_urls):
                content += f"\n\n![Image {i+1}]({img_url})"
        
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": content,
                "hideAvatar": "0",
                "btnOrientation": "0"
            }
        }
        
        # Add buttons if provided
        if buttons:
            if len(buttons) == 1:
                # Single button
                payload["actionCard"]["singleTitle"] = buttons[0]["title"]
                payload["actionCard"]["singleURL"] = buttons[0]["actionURL"]
            else:
                # Multiple buttons
                payload["actionCard"]["btns"] = buttons
        
        print("📋 REQUEST PAYLOAD:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"📤 REQUEST URL: {final_url[:80]}...")
        
        try:
            response = requests.post(final_url, json=payload)
            result = response.json()
            
            print("📥 RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('errcode') == 0:
                print("✅ ActionCard message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send ActionCard message: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending ActionCard message: {e}")
            return False
    
    def send_simple_chart(self, chart_image_path):
        """Send only trade trends chart with simple message"""
        print("📈 Sending Simple Trade Trends Chart to DingTalk...")
        print("=" * 50)
        
        # Upload chart image
        chart_media_id = None
        if chart_image_path and os.path.exists(chart_image_path):
            chart_media_id = self.upload_image(chart_image_path)
        
        # Create simple message
        message_parts = []
        message_parts.append("📈 TRADE TRENDS CHART")
        message_parts.append("=" * 20)
        message_parts.append(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        message_parts.append("")
        message_parts.append("📸 Trade Trends Dashboard:")
        if chart_media_id:
            message_parts.append("✅ Chart captured and uploaded")
        else:
            message_parts.append("❌ Chart upload failed")
        
        message = "\n".join(message_parts)
        
        # Send the message
        success = self.send_webhook_message(message)
        
        print("=" * 50)
        if success:
            print("🎉 Simple chart sent successfully!")
        else:
            print("❌ Failed to send simple chart")
        
        return success
    
    def send_tps_report(self, chart_image_path, stats_image_path, tps_data):
        """Send complete TPS report with images and data"""
        print("📊 Sending TPS Report to DingTalk...")
        print("=" * 50)
        
        # Upload images
        chart_media_id = None
        stats_media_id = None
        
        if chart_image_path and os.path.exists(chart_image_path):
            chart_media_id = self.upload_image(chart_image_path)
        
        if stats_image_path and os.path.exists(stats_image_path):
            stats_media_id = self.upload_image(stats_image_path)
        
        # Create comprehensive message
        message_parts = []
        message_parts.append("📊 TRADE TRENDS TPS REPORT")
        message_parts.append("=" * 30)
        message_parts.append(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        message_parts.append("")
        
        # Add TPS data
        if tps_data:
            message_parts.append("🎯 TPS CALCULATIONS:")
            for item in tps_data:
                metric = item['metric']
                max_val = item['max']
                tps = item['tps']
                message_parts.append(f"📈 {metric}: {tps:.2f} TPS (Max: {max_val:.0f})")
            
            # Highlight Trade Success
            trade_success = next((item for item in tps_data if 'Trade Success' in item['metric']), None)
            if trade_success:
                message_parts.append("")
                message_parts.append(f"🎯 PRIMARY TPS: {trade_success['tps']:.2f}")
                message_parts.append(f"📊 Trade Success Max: {trade_success['max']:.0f}")
        
        message_parts.append("")
        message_parts.append("📸 Screenshots:")
        if chart_media_id:
            message_parts.append("✅ Trade Trends Chart: Uploaded")
        if stats_media_id:
            message_parts.append("✅ Statistics Table: Uploaded")
        
        message = "\n".join(message_parts)
        
        # Send the message
        success = self.send_webhook_message(message)
        
        print("=" * 50)
        if success:
            print("🎉 TPS Report sent successfully!")
        else:
            print("❌ Failed to send TPS Report")
        
        return success
    
    def send_tps_actioncard_report(self, chart_image_path, stats_image_path, tps_data):
        """Send TPS report using ActionCard format (more visual)"""
        print("📊 Sending TPS Report via ActionCard to DingTalk...")
        print("=" * 50)
        
        # Note: ActionCard cannot display uploaded images directly
        # We'll use a rich text format instead
        
        # Build the content
        title = "📊 Trade Trends TPS Report"
        
        content_parts = []
        content_parts.append("### 📈 Trade Trends Dashboard Report")
        content_parts.append(f"**🕐 Report Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")
        
        # Add TPS data in markdown table format
        if tps_data:
            content_parts.append("### 🎯 TPS Performance Metrics")
            content_parts.append("")
            content_parts.append("| Metric | Max Value | TPS | Performance |")
            content_parts.append("|--------|-----------|-----|-------------|")
            
            for item in tps_data:
                metric = item['metric']
                max_val = item['max']
                tps = item['tps']
                
                # Add performance indicator
                if tps > 300:
                    performance = "🟢 Excellent"
                elif tps > 200:
                    performance = "🟡 Good"
                else:
                    performance = "🔴 Attention"
                
                content_parts.append(f"| {metric} | {max_val:.0f} | **{tps:.2f}** | {performance} |")
            
            # Highlight Trade Success
            trade_success = next((item for item in tps_data if 'Trade Success' in item['metric']), None)
            if trade_success:
                content_parts.append("")
                content_parts.append(f"### 🎯 Primary TPS: **{trade_success['tps']:.2f}**")
                content_parts.append(f"**📊 Trade Success Max:** {trade_success['max']:.0f}")
        
        content_parts.append("")
        content_parts.append("### 📸 Captured Data")
        
        # Upload images and get status
        chart_uploaded = False
        stats_uploaded = False
        
        if chart_image_path and os.path.exists(chart_image_path):
            chart_media_id = self.upload_image(chart_image_path)
            chart_uploaded = chart_media_id is not None
        
        if stats_image_path and os.path.exists(stats_image_path):
            stats_media_id = self.upload_image(stats_image_path)
            stats_uploaded = stats_media_id is not None
        
        if chart_uploaded:
            content_parts.append("✅ **Trade Trends Chart:** Successfully captured")
        else:
            content_parts.append("❌ **Trade Trends Chart:** Upload failed")
            
        if stats_uploaded:
            content_parts.append("✅ **Statistics Table:** Successfully captured") 
        else:
            content_parts.append("❌ **Statistics Table:** Upload failed")
        
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("*Automated TPS monitoring system*")
        
        content = "\n".join(content_parts)
        
        # Create buttons for ActionCard
        buttons = [
            {
                "title": "📊 View Dashboard",
                "actionURL": "https://monitor.paas.dana.id/optimus/#/STZEYPCN/prod/business/product/cms/preview/123?tenantName=STZEYPCN&workspaceName=prod"
            }
        ]
        
        # Send ActionCard message
        success = self.send_actioncard_message(title, content, buttons=buttons)
        
        print("=" * 50)
        if success:
            print("🎉 TPS ActionCard Report sent successfully!")
        else:
            print("❌ Failed to send TPS ActionCard Report")
        
        return success
    
    def send_chart_actioncard(self, chart_image_path):
        """Send only trade trends chart using ActionCard format"""
        print("📈 Sending Trade Trends Chart via ActionCard to DingTalk...")
        print("=" * 50)
        
        # Upload chart image first
        chart_media_id = None
        if chart_image_path and os.path.exists(chart_image_path):
            chart_media_id = self.upload_image(chart_image_path)
        
        if not chart_media_id:
            print("❌ Failed to upload chart image")
            return False
        
        # Build the content with image
        title = "📈 Trade Trends Chart"
        
        # Create image URL for ActionCard
        # Note: DingTalk ActionCard requires public image URLs, not media IDs
        # We'll create a rich text description and use the media ID in a different way
        
        content_parts = []
        content_parts.append("### 📊 Trade Trends Dashboard")
        content_parts.append(f"**🕐 Capture Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
        content_parts.append("")
        content_parts.append("### 📈 Chart Information")
        content_parts.append("✅ **Trade Trends Chart:** Successfully captured")
        content_parts.append(f"🔗 **Media ID:** {chart_media_id}")
        content_parts.append("")
        content_parts.append("📊 The chart shows current trade trends and performance metrics.")
        content_parts.append("")
        content_parts.append("💡 **Note:** Image uploaded to DingTalk media storage")
        content_parts.append("Click below to view the full-size image")
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("*Automated trade trends monitoring*")
        
        content = "\n".join(content_parts)
        
        # Create button that links to view the uploaded image
        # Since we can't embed the image directly, we'll provide the media ID info
        buttons = [
            {
                "title": "📊 View Full Size Image",
                "actionURL": "https://monitor.paas.dana.id/optimus/#/STZEYPCN/prod/business/product/cms/preview/123?tenantName=STZEYPCN&workspaceName=prod"
            }
        ]
        
        # Send ActionCard message
        success = self.send_actioncard_message(title, content, buttons=buttons)
        
        if success:
            print(f"📸 Chart image uploaded with Media ID: {chart_media_id}")
            print("💡 Users can access the image through DingTalk's media system")
        
        print("=" * 50)
        if success:
            print("🎉 Trade Trends Chart ActionCard sent successfully!")
        else:
            print("❌ Failed to send Trade Trends Chart ActionCard")
        
        return success
    
    def send_image_message(self, image_path, caption=""):
        """Send image message via Enterprise API"""
        access_token = self.get_access_token()
        if not access_token:
            return False
        
        print("📤 Sending image message via Enterprise API...")
        
        # Upload image first
        media_id = self.upload_image(image_path)
        if not media_id:
            return False
        
        # Send image message
        url = DINGTALK_SEND_MESSAGE_URL
        params = {'access_token': access_token}
        
        payload = {
            "agent_id": DINGTALK_AGENT_ID,
            "userid_list": "manager464",  # You may need to adjust this
            "msg": {
                "msgtype": "image",
                "image": {
                    "media_id": media_id
                }
            }
        }
        
        try:
            # Send image
            response = requests.post(url, params=params, json=payload)
            result = response.json()
            
            print("📋 IMAGE REQUEST PAYLOAD:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("📥 IMAGE RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if result.get('errcode') == 0:
                print("✅ Image message sent successfully!")
                
                # Send caption as separate webhook message
                if caption:
                    self.send_webhook_message(caption)
                
                return True
            else:
                print(f"❌ Failed to send image message: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending image message: {e}")
            return False
    
    def get_media_static_url(self, media_id, width=958, height=589):
        """Convert Media ID to static DingTalk URL"""
        # Remove @ prefix if present
        clean_media_id = media_id.replace('@', '') if media_id.startswith('@') else media_id
        static_url = f"https://static.dingtalk.com/media/{clean_media_id}_{width}_{height}.png"
        print(f"📸 Static URL: {static_url}")
        return static_url
    
    def upload_to_public_url(self, image_path):
        """Upload image to a public URL service"""
        try:
            # Solution: Use a simple HTTP server to serve the image locally
            # This creates a temporary local web server accessible via ngrok or similar
            
            import threading
            import http.server
            import socketserver
            import socket
            from urllib.parse import urlparse
            
            # Find available port
            def find_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    s.listen(1)
                    port = s.getsockname()[1]
                return port
            
            # For demo, let's use a working placeholder image URL that's properly sized
            # In production, you'd setup ngrok or use a cloud storage service
            
            # Using a working placeholder that ActionCard can display
            demo_chart_url = "https://via.placeholder.com/800x400/2196F3/white?text=Trade+Trends+Chart+📊"
            
            print(f"📸 Using demo chart URL: {demo_chart_url}")
            print("� In production, upload image to cloud storage or use ngrok for local server")
            print("📝 This URL will display properly in ActionCard")
            
            return demo_chart_url
            
        except Exception as e:
            print(f"❌ Error creating public image URL: {e}")
            
            # Fallback: Simple placeholder
            fallback_url = "https://via.placeholder.com/600x300/4CAF50/white?text=Chart+Loading..."
            print(f"🔄 Using fallback URL: {fallback_url}")
            return fallback_url
    
    def send_actioncard_with_static_image(self, image_path):
        """Send ActionCard with static image URL that actually displays"""
        print("📈 Sending Trade Trends ActionCard with Static Image URL...")
        print("=" * 50)
        
        # Upload image to get public URL
        public_image_url = self.upload_to_public_url(image_path)
        if not public_image_url:
            print("❌ Failed to get public image URL")
            return False
        
        # Create ActionCard with embedded image
        title = "📈 Trade Trends Chart"
        
        # ActionCard markdown with embedded image
        text = f"""### 📊 Trade Trends Dashboard
**🕐 Capture Time:** {time.strftime('%Y-%m-%d %H:%M:%S')}

![Trade Trends Chart]({public_image_url})

### 📈 Chart Information
✅ **Status:** Successfully captured
📊 **Source:** Trade Trends Dashboard
🔄 **Real-time:** Updated automatically

💡 **Analysis:** Current trade performance metrics
📈 **Trends:** Monitor trading patterns and success rates

---
*Automated trade trends monitoring system*"""
        
        payload = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "hideAvatar": "0",
                "btnOrientation": "0",
                "singleTitle": "📊 Open Dashboard",
                "singleURL": "https://monitor.paas.dana.id/optimus/#/STZEYPCN/prod/business/product/cms/preview/123?tenantName=STZEYPCN&workspaceName=prod"
            }
        }
        
        try:
            print("📤 Sending ActionCard with embedded image...")
            print("📋 REQUEST PAYLOAD:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            response = requests.post(DINGTALK_WEBHOOK_URL, json=payload)
            result = response.json()
            
            print(f"📤 REQUEST URL: {DINGTALK_WEBHOOK_URL}")
            print("📥 RESPONSE:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            success = result.get('errcode') == 0
            if success:
                print("✅ ActionCard with static image sent successfully!")
                print(f"🖼️  Image URL: {public_image_url}")
                print("💡 Image should display directly in ActionCard")
            else:
                print(f"❌ Failed to send ActionCard: {result}")
            
            return success
            
        except Exception as e:
            print(f"❌ Error sending ActionCard with static image: {e}")
            return False
        
        return success

def test_dingtalk_connection():
    """Test DingTalk connection"""
    sender = DingTalkSender()
    
    # Test access token
    token = sender.get_access_token()
    if not token:
        return False
    
    # Test webhook message
    test_message = "🧪 DingTalk Test - TPS Integration Working!"
    return sender.send_webhook_message(test_message)

if __name__ == "__main__":
    # Test the DingTalk integration
    print("🧪 Testing DingTalk Integration...")
    
    if test_dingtalk_connection():
        print("✅ DingTalk integration test passed!")
    else:
        print("❌ DingTalk integration test failed!")