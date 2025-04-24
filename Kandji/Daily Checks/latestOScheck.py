#!/usr/bin/env python3

import requests
import os
from packaging import version
from datetime import datetime, timezone

# Load environment variables (GitHub Secrets)
api_key = os.getenv('DEVICE_CHECK_24')
base_url = os.getenv('KANDJI_BASE_URL')
slack_channel = os.getenv('KANDJI_NOTIFICATIONS_ID')
slack_webhook_url = os.getenv('KANDJI_NOTIFICATIONS_WEBHOOK')

# URLs to fetch the latest iOS and macOS versions
ios_json_url = "https://sofafeed.macadmins.io/v1/ios_data_feed.json"
macos_json_url = "https://sofafeed.macadmins.io/v1/macos_data_feed.json"

# Function to get the latest versions from a JSON file
def get_latest_versions_from_json(json_url):
    response = requests.get(json_url)
    response.raise_for_status()
    data = response.json()

    latest_info = data['OSVersions'][0]['Latest']
    latest_version = latest_info['ProductVersion']
    latest_build = latest_info['Build']
    latest_release_date = datetime.fromisoformat(latest_info['ReleaseDate'].replace("Z", "+00:00"))
    formatted_release_date = latest_release_date.strftime('%B %d, %Y')
    zero_day_exploits = latest_info.get('ActivelyExploitedCVEs', [])

    return latest_version, latest_build, formatted_release_date, zero_day_exploits, latest_release_date

# Fetch the latest iOS and macOS versions
latest_ios_version, latest_ios_build, latest_ios_release_date, ios_zero_days, ios_release_datetime = get_latest_versions_from_json(ios_json_url)
latest_macos_version, latest_macos_build, latest_macos_release_date, macos_zero_days, macos_release_datetime = get_latest_versions_from_json(macos_json_url)

# Calculate days since release
current_date = datetime.now(timezone.utc)
ios_days_since_release = (current_date - ios_release_datetime).days
macos_days_since_release = (current_date - macos_release_datetime).days

print("Latest OS Versions:")
print("macOS:")
print(f"  Version: {latest_macos_version}")
print(f"  Build: {latest_macos_build}")
print(f"  Release Date: {latest_macos_release_date}")
print(f"  Days Since Release: {macos_days_since_release}")
print(f"  Zero Day Exploits: {'None' if not macos_zero_days else ', '.join(macos_zero_days)}\n")

print("iOS:")
print(f"  Version: {latest_ios_version}")
print(f"  Build: {latest_ios_build}")
print(f"  Release Date: {latest_ios_release_date}")
print(f"  Days Since Release: {ios_days_since_release}")
print(f"  Zero Day Exploits: {'None' if not ios_zero_days else ', '.join(ios_zero_days)}\n")

# Complete API URL with path and query parameters
api_url = f"{base_url}/api/v1/devices?limit=300"

# Making the API request with the API key in headers for authentication
headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get(api_url, headers=headers)

if response.status_code == 200:
    try:
        devices = response.json()  # Parse JSON response
    except ValueError as e:
        print("Error parsing JSON response:", e)
        devices = []
else:
    print("Failed to fetch devices. Status code:", response.status_code)
    devices = []

# Debug: Print the structure of the devices
print("Devices response structure:", devices)

# Compare device OS versions with the latest versions and prepare the message
outdated_devices = []
for device in devices:
    if isinstance(device, dict):  # Ensure device is a dictionary
        tags = device.get("tags", [])

        # Skip devices with the "exclude_os_check" tag
        if "exclude_os_check" in tags:
            continue

        os_version = device.get("os_version", "").strip()
        platform = device.get("platform", "").lower()
        device_name = device.get("device_name", "Unknown")

        # Check if user is a dictionary
        user_info = device.get("user", {})
        if isinstance(user_info, dict):
            device_user = user_info.get("name", "Unknown User")
        else:
            device_user = "Unknown User"

        # Grouping iPad and iPhone under iOS, ignore AppleTV
        if platform in ["ipad", "iphone"]:
            latest_version = latest_ios_version
            platform_name = "iPad" if platform == "ipad" else "iPhone"
        elif platform == "mac":
            latest_version = latest_macos_version
            platform_name = "Mac"
        else:
            continue

        # Compare versions and check if the device is outdated
        if os_version and version.parse(os_version) < version.parse(latest_version):
            outdated_devices.append(f"{device_name} ({platform_name}, User: {device_user}): {os_version} (Latest: {latest_version})")

# Prepare the message for Slack
message = (
    "Latest OS Versions:\n"
    f"macOS:\n  Version: {latest_macos_version}\n  Build: {latest_macos_build}\n  Release Date: {latest_macos_release_date}\n"
    f"  Days Since Release: {macos_days_since_release}\n"
    f"  Zero Day Exploits: {'None' if not macos_zero_days else ', '.join(macos_zero_days)}\n\n"
    f"iOS:\n  Version: {latest_ios_version}\n  Build: {latest_ios_build}\n  Release Date: {latest_ios_release_date}\n"
    f"  Days Since Release: {ios_days_since_release}\n"
    f"  Zero Day Exploits: {'None' if not ios_zero_days else ', '.join(ios_zero_days)}\n\n"
    "Devices not running the latest OS:\n"
)

if outdated_devices:
    message += "\n".join(outdated_devices)
else:
    message += "All devices are up to date with the latest OS versions."

# Function to send messages to Slack
def send_to_slack(message):
    payload = {
        "channel": slack_channel,
        "text": message,
        "username": "Device Monitor",  # Customize the bot's username
        "icon_emoji": ":robot_face:"  # Customize the bot's icon
    }
    requests.post(slack_webhook_url, json=payload)

# Send the message to Slack
send_to_slack(message)