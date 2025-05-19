# Kandji Daily Checks

Scripts in this folder monitor device health and post results to Slack. They can be run manually or scheduled through GitHub Actions or another automation platform.

## Scripts

### `checkin24Hours.py`
Lists devices that have not checked in within the last day.

### `errorCheck.py`
Collects library item errors for each device.

### `hardDrive70.py`
Reports machines where the main volume is more than 70% full.

### `latestOScheck.py`
Fetches the latest macOS and iOS versions from [SOFA](https://sofa.macadmins.io/) and lists devices that are behind.

### `macosLocationByIP.py`
Uses the device's public IP to estimate its location via the ipify and IPInfo APIs, then writes the result to the device notes.

## Setup

Set the following environment variables for API access and Slack notifications:

- `DEVICE_CHECK_24`
- `KANDJI_BASE_URL`
- `KANDJI_NOTIFICATIONS_ID`
- `KANDJI_NOTIFICATIONS_WEBHOOK`

These scripts require Python 3 and network access to Kandji and Slack.
