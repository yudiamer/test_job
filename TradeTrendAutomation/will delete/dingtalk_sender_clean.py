#!/usr/bin/env python3
"""
DingTalk Integration Module - Clean Version with Link Message Support
=====================================================================
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
from PIL import Image

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
        """Upload image to DingTalk and get media_id"""
        try:
            access_token = self.get_access_token()
            if not access_token:
                return None
            
            url = f"https://oapi.dingtalk.com/media/upload?access_token={access_token}&type=image"
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files)
            
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

    def get_media_static_url(self, media_id, image_path):
        """Generate static URL for uploaded media"""
        try:
            # Get image dimensions for URL
            with Image.open(image_path) as img:
                width, height = img.size
            
            # Clean media_id (remove @ if present)
            clean_media_id = media_id.lstrip('@')
            
            # Generate static URL
            static_url = f"https://static.dingtalk.com/media/{clean_media_id}_{width}_{height}.png"
            return static_url
            
        except Exception as e:
            print(f"❌ Error generating static URL: {e}")
            return None

    def send_webhook_message(self, message):
        """Send simple text message via webhook"""
        try:
            payload = {
                "msgtype": "text",
                "text": {"content": message}
            }
            
            response = requests.post(DINGTALK_WEBHOOK_URL, json=payload)
            result = response.json()
            
            if result.get('errcode') == 0:
                print("✅ Webhook message sent successfully!")
                return True
            else:
                print(f"❌ Webhook error: {result}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending webhook message: {e}")
            return False

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
                    "text": f"🕐 Time: {timestamp}\n🔧 {description}\n💡 Click to view detailed chart analysis",
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

if __name__ == "__main__":
    sender = DingTalkSender()
    print("✅ DingTalk Sender initialized!")