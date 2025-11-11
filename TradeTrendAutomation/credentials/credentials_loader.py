#!/usr/bin/env python3
"""
Credentials Loader Utility
Centralized loading of all credentials for the application
"""

import os
import sys

def load_credentials():
    """
    Load all credentials from credential files
    Returns a dictionary with all credentials organized by service
    """
    # Add credentials directory to Python path
    credentials_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, credentials_dir)
    
    try:
        # Import credential modules
        import dingtalk_credentials
        import xflush_credentials
        
        # Organize credentials by service
        credentials = {
            'dingtalk': {
                'client_id': dingtalk_credentials.DINGTALK_CLIENT_ID,
                'client_secret': dingtalk_credentials.DINGTALK_CLIENT_SECRET,
                'agent_id': dingtalk_credentials.DINGTALK_AGENT_ID,
                'webhook_url': dingtalk_credentials.DINGTALK_WEBHOOK_URL,
                'webhook_secret': dingtalk_credentials.DINGTALK_WEBHOOK_SECRET,
                'token_url': dingtalk_credentials.DINGTALK_TOKEN_URL,
                'media_upload_url': dingtalk_credentials.DINGTALK_MEDIA_UPLOAD_URL,
                'send_message_url': dingtalk_credentials.DINGTALK_SEND_MESSAGE_URL
            },
            'xflush': {
                'username': xflush_credentials.XFLUSH_USERNAME,
                'password': xflush_credentials.XFLUSH_PASSWORD,
                'login_url': xflush_credentials.XFLUSH_LOGIN_URL,
                'trade_trends_url': xflush_credentials.XFLUSH_TRADE_TRENDS_URL,
                'tenant_name': xflush_credentials.XFLUSH_TENANT_NAME,
                'workspace_name': xflush_credentials.XFLUSH_WORKSPACE_NAME,
                'browser_window_size': xflush_credentials.BROWSER_WINDOW_SIZE,
                'browser_wait_timeout': xflush_credentials.BROWSER_WAIT_TIMEOUT,
                'screenshot_wait_time': xflush_credentials.SCREENSHOT_WAIT_TIME
            }
        }
        
        return credentials
        
    except ImportError as e:
        raise Exception(f"Failed to load credentials: {e}")
    except AttributeError as e:
        raise Exception(f"Missing credential attribute: {e}")

def get_dingtalk_credentials():
    """Get only DingTalk credentials"""
    return load_credentials()['dingtalk']

def get_xflush_credentials():
    """Get only XFlush credentials"""
    return load_credentials()['xflush']

# For testing purposes
if __name__ == "__main__":
    print("🔐 Testing Credential Loader...")
    try:
        creds = load_credentials()
        print("✅ DingTalk credentials loaded successfully")
        print("✅ XFlush credentials loaded successfully")
        print(f"🔑 DingTalk Client ID: {creds['dingtalk']['client_id']}")
        print(f"🔑 XFlush Username: {creds['xflush']['username']}")
        print("🎉 All credentials loaded successfully!")
    except Exception as e:
        print(f"❌ Credential loading failed: {e}")