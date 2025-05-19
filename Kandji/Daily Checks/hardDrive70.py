#!/usr/bin/env python3
"""
Reports machines where the main volume is more than 70% full using the Kandji
API and posts the results to Slack.

Author: Ben Rillie <ben@treducks.tech>
WARNING: Use at your own risk.
License: MIT
"""

import requests
import os
from datetime import datetime

# Load environment variables
base_url = os.getenv('KANDJI_BASE_URL')
api_token = os.getenv('DEVICE_CHECK_24')
slack_channel = os.getenv('KANDJI_NOTIFICATIONS_ID')
slack_webhook_url = os.getenv('KANDJI_NOTIFICATIONS_WEBHOOK')

# Set up headers for the API request
headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json'
}

# Function to get devices from Kandji API
def get_devices():
    """Fetch devices from the Kandji API"""
    api_url = f"{base_url}/api/v1/devices?limit=300"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching devices: {e}")
        return None

# Function to get hard drive capacity details from each device
def get_volumes_over_70_percent(devices):
    over_70_percent = []

    for device in devices:
        device_id = device.get('device_id')
        device_name = device.get('device_name', 'Unknown')
        serial_number = device.get('serial_number', 'Unknown')

        # Check if the device has the tag "exclude_hd70"
        if "exclude_hd70" in device.get('tags', []):
            print(f"Skipping device {device_id} due to 'exclude_hd70' tag.")
            continue

        device_details = get_device_details(device_id)
        if not device_details:
            continue

        # Debugging: Print device details to understand the structure
        print(f"Device Details for {device_id}: {device_details}")

        # Ensure 'general' is a dictionary
        general_info = device_details.get('general', {})
        assigned_user = 'Unknown User'
        if isinstance(general_info, dict):
            assigned_user_info = general_info.get('assigned_user', {})
            if isinstance(assigned_user_info, dict):
                assigned_user = assigned_user_info.get('name', 'Unknown User')

        volumes = device_details.get('volumes', [])

        for volume in volumes:
            # Only consider volumes named "Macintosh HD"
            if volume.get('name') == "Macintosh HD":
                percent_used = volume.get('percent_used', '0%')
                try:
                    percent_used = int(percent_used.rstrip('%'))
                except ValueError:
                    continue

                if percent_used > 69:
                    over_70_percent.append({
                        'device_name': device_name,
                        'serial_number': serial_number,
                        'assigned_user': assigned_user,
                        'volume_name': volume.get('name', 'Unknown'),
                        'capacity': volume.get('capacity', 'Unknown'),
                        'available': volume.get('available', 'Unknown'),
                        'percent_used': f"{percent_used}%"
                    })

    return over_70_percent

# Function to get detailed information for a specific device
def get_device_details(device_id):
    """Fetch detailed information for a specific device"""
    api_url = f"{base_url}/api/v1/devices/{device_id}/details"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching device details for {device_id}: {e}")
        return None

# Function to send messages to Slack
def send_to_slack(message):
    payload = {
        "channel": slack_channel,
        "text": message,
        "username": "Device Monitor",
        "icon_emoji": ":robot_face:"
    }
    try:
        response = requests.post(slack_webhook_url, json=payload)
        response.raise_for_status()
        print("Message sent to Slack successfully.")
    except requests.RequestException as e:
        print(f"Error sending message to Slack: {e}")

# Main function to pull the device info and filter based on disk usage
def main():
    devices = get_devices()
    if devices is None:
        print("Failed to fetch devices. Exiting.")
        return

    volumes_over_70 = get_volumes_over_70_percent(devices)
    if volumes_over_70:
        message = f"{len(volumes_over_70)} volumes found with over 70% usage:\n"
        for volume in volumes_over_70:
            message += (
                f"Device Name: {volume['device_name']}, Serial: {volume['serial_number']}, "
                f"Assigned User: {volume['assigned_user']}, Volume: {volume['volume_name']}, "
                f"Used: {volume['percent_used']}\n"
            )
    else:
        message = "No volumes found with over 70% usage."

    # Send the message to Slack
    send_to_slack(message)

if __name__ == '__main__':
    main()
