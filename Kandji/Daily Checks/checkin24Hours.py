#!/usr/bin/env python3
"""
Lists devices that have not checked in within the last day using the Kandji API
and posts the results to Slack.

Author: Ben Rillie <ben@treducks.tech>
WARNING: Use at your own risk.
License: MIT
"""

import requests
from datetime import datetime, timedelta, timezone
import os

# Load environment variables (GitHub Secrets)
api_key = os.getenv('DEVICE_CHECK_24')
base_url = os.getenv('KANDJI_BASE_URL')
slack_channel = os.getenv('KANDJI_NOTIFICATIONS_ID')
slack_webhook_url = os.getenv('KANDJI_NOTIFICATIONS_WEBHOOK')

# Check if all required environment variables are set
missing_vars = [var for var in ['DEVICE_CHECK_24', 'KANDJI_BASE_URL', 'KANDJI_NOTIFICATIONS_ID', 'KANDJI_NOTIFICATIONS_WEBHOOK'] if not os.getenv(var)]
if missing_vars:
    print(f"Missing environment variables: {', '.join(missing_vars)}")
    exit(1)

# Complete API URL with path and query parameters
api_url = f"{base_url}/api/v1/devices?limit=300"

# Making the API request with the API key in headers for authentication
headers = {"Authorization": f"Bearer {api_key}"}
try:
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    devices = response.json()  # Parse JSON response
except requests.RequestException as e:
    print(f"Error fetching devices: {e}")
    exit(2)

# Function to check if last check-in is more than 24 hours ago
def is_more_than_24_hours_ago(check_in_time):
    try:
        check_in_datetime = datetime.fromisoformat(check_in_time.rstrip("Z"))
        check_in_datetime = check_in_datetime.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - check_in_datetime > timedelta(hours=24)
    except ValueError as e:
        print(f"Error parsing check-in time: {e}")
        return False

# Filtering devices excluding those with the tag "exclude_24"
devices_over_24_hours = [
    device for device in devices
    if is_more_than_24_hours_ago(device.get("last_check_in", "")) and "exclude_24" not in device.get("tags", [])
]

# Function to send messages to Slack
def send_to_slack(message):
    payload = {
        "channel": slack_channel,
        "text": message,
        "username": "Device Monitor",  # Customize the bot's username
        "icon_emoji": ":robot_face:"  # Customize the bot's icon
    }
    try:
        response = requests.post(slack_webhook_url, json=payload)
        response.raise_for_status()
        print("Message sent to Slack successfully.")
    except requests.RequestException as e:
        print(f"Error sending message to Slack: {e}")
        exit(3)

# Preparing message
if devices_over_24_hours:
    message = "These devices have not checked in for more than 24 hours:\n"
    for device in devices_over_24_hours:
        platform = device.get("platform", "Unknown")
        user_field = device.get("user", "Unknown")
        user_name = user_field if isinstance(user_field, str) else user_field.get("name", "Unknown")
        message += (f"Device Name: {device['device_name']}\n"
                    f"Platform: {platform}\n"
                    f"User: {user_name}\n\n")
else:
    message = "All devices have checked in over the last 24 hours."

# Send the message to Slack
send_to_slack(message)
