# Kandji Secrets

Helper scripts for managing API keys used by the other tools.

## Scripts

### `sendApiKey.py`
Stores a Kandji API key in the macOS System Keychain. If an existing entry is older than 30 days it is replaced. Update the `api_user`, `api_name` and `api_key` variables before running.
