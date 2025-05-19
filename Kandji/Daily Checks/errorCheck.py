#!/usr/bin/env python3
"""
Collects Kandji library item errors for each device and sends a summary to Slack.

Author: Ben Rillie <ben@treducks.tech>
WARNING: Use at your own risk.
License: MIT
"""

import requests
import os

# Load environment variables (GitHub Secrets)
api_key = os.getenv('DEVICE_CHECK_24')
base_url = os.getenv('KANDJI_BASE_URL')
slack_channel = os.getenv('KANDJI_NOTIFICATIONS_ID')
slack_webhook_url = os.getenv('KANDJI_NOTIFICATIONS_WEBHOOK')

# Function to send messages to Slack
def send_to_slack(message):
    payload = {
        "channel": slack_channel,
        "text": message,
        "username": "Device Monitor",  # Customize the bot's username
        "icon_emoji": ":robot_face:"  # Customize the bot's icon
    }
    requests.post(slack_webhook_url, json=payload)

# Complete API URL with path and query parameters
api_url = f"{base_url}/api/v1/devices?limit=300"

# Making the API request with the API key in headers for authentication
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(api_url, headers=headers)

if response.status_code == 200:
    devices = response.json()  # Parse JSON response
else:
    print("Failed to fetch devices. Status code:", response.status_code)
    devices = []

# Prepare the message for Slack
error_messages = []

# Iterate through each device to check for errors
for device in devices:
    device_id = device.get("device_id")
    device_name = device.get("device_name", "Unknown")

    # Query the device status
    status_url = f"{base_url}/api/v1/devices/{device_id}/status"
    status_response = requests.get(status_url, headers=headers)

    if status_response.status_code == 200:
        status_data = status_response.json()
        library_items = status_data.get("library_items", [])

        # Check for errors in the library items
        for item in library_items:
            if item.get("status") == "ERROR":
                error_log = item.get("log", "No log available")
                # Split the error log into lines and take the first two
                error_log_lines = error_log.splitlines()[:2]
                # Join the first two lines back into a string
                error_log_summary = "\n".join(error_log_lines)
                error_messages.append(
                    f"Device: {device_name}\n"
                    f"Item: {item.get('name')}\n"
                    f"Error Log: {error_log_summary}\n"
                )
    else:
        print(f"Failed to fetch status for device {device_id}. Status code:", status_response.status_code)

# Send the error messages to Slack
if error_messages:
    message = "Device Errors Detected:\n" + "\n".join(error_messages)
    send_to_slack(message)
else:
    send_to_slack("No device errors detected.")
