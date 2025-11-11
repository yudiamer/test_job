#!/usr/bin/env python3
"""
DingTalk Credentials Configuration
Store all DingTalk-related credentials here
"""

# Enterprise Application Credentials
DINGTALK_CLIENT_ID = "dingih5yqjdxxw8ghaqe"
DINGTALK_CLIENT_SECRET = "oGhCniLiOI-pZL9kVlQ-c68Td_0BgncdUGtx3c8etIUkss7E0U3x4HRClnvuh0J6"
DINGTALK_AGENT_ID = "4077595685"

# Legacy variable names for compatibility
DINGTALK_APP_KEY = DINGTALK_CLIENT_ID
DINGTALK_APP_SECRET = DINGTALK_CLIENT_SECRET

# Group Robot Webhook Credentials
DINGTALK_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=5c1dab8b7961ac2bea8e34b97163b7e4dd3fdf7aa0c2d7b835b4761d5ca87aa8"
DINGTALK_WEBHOOK_SECRET = "SECf2758173f7b221078c66b5fb5a8d6059173f72bd55923cf6dcae9fdc43864955"

# API Endpoints
DINGTALK_TOKEN_URL = "https://oapi.dingtalk.com/gettoken"
DINGTALK_MEDIA_UPLOAD_URL = "https://oapi.dingtalk.com/media/upload"
DINGTALK_SEND_MESSAGE_URL = "https://oapi.dingtalk.com/topapi/message/corpconversation/asyncsend_v2"

# Browser Settings
BROWSER_HEADLESS = True  # Set to True for headless mode (no browser window), False to see browser