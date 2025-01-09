# Kandji Daily Checks

This directory contains Python scripts designed to monitor and report the status of devices managed by Kandji. These scripts are run daily using GitHub Actions and the results are sent to a Slack channel for easy monitoring.

## Scripts Overview

### `checkin24Hours.py`
Identifies devices that have not checked in within the last 24 hours and sends a list to Slack.

### `errorCheck.py`
Checks all macOS devices for errors listed in its record and sends a summary to Slack.

### `hardDrive70.py`
Monitors devices for hard drive usage over 70% and sends a list to Slack.

### `latestOScheck.py`
Compares the OS versions of devices with the latest available versions and sends a list of devices that are not up to date to Slack. Leverages [SOFA](https://sofa.macadmins.io/) to get the latest OS versions.
- Need to fix the zero day listing for iOS devices.

### `macosLocationByIP.py`
Updates device notes in Kandji with location information based on the public IP. Due to using the public IP of a device to find the location, it's not very accurate. I wrote this mainly so I could see if my devices had left the country. Leverages the [ipify](https://www.ipify.org/) API.

It's kinda a janky script so please use it with caution.
- Does not work if the user is not logged in - need to fix.
- I need to add a check to see if the device is connected to VPN.

## Setup and Configuration

1. **Environment Variables**: Ensure the following environment variables are set for API access and Slack integration:
   - `DEVICE_CHECK_24`
   - `KANDJI_BASE_URL`
   - `KANDJI_NOTIFICATIONS_ID`
   - `KANDJI_NOTIFICATIONS_WEBHOOK`

2. **GitHub Actions**: These scripts can be automated using GitHub Actions. Ensure that your repository is configured with the necessary secrets for API keys and Slack webhook URLs.

3. **Local Execution**: To run these scripts locally, ensure you have Python installed and the required dependencies and environment variables set.

Please use caution when using any of these scripts.
