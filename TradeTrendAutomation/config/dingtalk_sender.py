import requests
import base64
import hashlib
import hmac
import time
import os
import sys

# Add credentials path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'credentials'))
try:
    from dingtalk_credentials import *
except ImportError:
    print("❌ Could not import DingTalk credentials")
    sys.exit(1)

class DingTalkSender:
    def send_webhook_message(self, message):
        """Send a simple text message to DingTalk via webhook"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{DINGTALK_WEBHOOK_SECRET}"
        hmac_code = hmac.new(
            DINGTALK_WEBHOOK_SECRET.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code)
        final_url = f"{DINGTALK_WEBHOOK_URL}&timestamp={timestamp}&sign={sign.decode()}"
        clean_media_id = media_id.replace('@', '') if media_id.startswith('@') else media_id
        static_url = f"https://static.dingtalk.com/media/{clean_media_id}_{width}_{height}.png"
        
        payload = {
            "msgtype": "markdown",
            "text": {
                "📊 TRADE TRENDS TPS REPORT\n==============================\n🕐 Time: 2025-11-03 14:00:00\n\n🎯 TPS CALCULATIONS:\n📈 Trade Success: 250.00 TPS (Max: 15000)\n📈 Payment Apply: 180.00 TPS (Max: 10800)\n📈 Cashier Consult: 120.00 TPS (Max: 7200)\n\n🎯 PRIMARY TPS: 250.00\n📊 Trade Success Max: 15000\n\n📸 Screenshots:\n✅ Trade Trends Chart: Uploaded\n✅ Statistics Table: Uploaded" +
                f"![]({static_url})\n"
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