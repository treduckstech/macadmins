# MacAdmins Python Scripts

This repository contains Python utilities for managing macOS devices via the Kandji API. The scripts are grouped by purpose and can be run manually or scheduled through automation tools.

## Directory overview

- `Kandji/Daily Checks/` – Monitoring scripts that report device status to Slack.
- `Kandji/Self Service/` – Utilities that can be offered to users through Kandji Self Service.
- `Kandji/Secrets/` – Helper for storing API keys in the macOS Keychain.

Each folder provides a README with details about the included scripts.

## Requirements

- Python 3.8 or later on macOS
- Access to the Kandji API
- Slack webhook for notifications

Set these environment variables before running the monitoring scripts:

- `DEVICE_CHECK_24` – Kandji API token
- `KANDJI_BASE_URL` – URL of your Kandji tenant
- `KANDJI_NOTIFICATIONS_ID` – Slack channel ID
- `KANDJI_NOTIFICATIONS_WEBHOOK` – Slack webhook URL

## License

This project is licensed under the MIT License. See `LICENSE` for the full text.
