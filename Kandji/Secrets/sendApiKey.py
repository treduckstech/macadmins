#!/usr/bin/env python3
# apollo-sync

import os
import subprocess
from datetime import datetime, timedelta


# Function to check if the API key is already in the Keychain and its creation date
def check_keychain(api_name):
    """
    Checks if an API key is already in the system keychain and returns its creation date.
    """
    result = subprocess.run(
        ["security", "find-generic-password", "-s", api_name],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        output = result.stdout
        for line in output.splitlines():
            if "cdat" in line:
                # Extract the hexadecimal part of the cdat value
                cdat_hex = line.split('=')[1].strip().split()[0]
                try:
                    # Convert the hex timestamp to bytes, then decode to a string
                    cdat_bytes = bytes.fromhex(cdat_hex[2:])
                    cdat_str = cdat_bytes.decode('ascii').strip('\x00')
                    creation_date = datetime.strptime(cdat_str, "%Y%m%d%H%M%SZ")
                    return creation_date
                except ValueError:
                    print(f"Invalid hexadecimal value for cdat: {cdat_hex}")
                    return None
    return None


# Function to delete an API key from the Keychain
def delete_keychain(api_name):
    """
    Deletes an API key from the system keychain.
    """
    subprocess.run(
        ["security", "delete-generic-password", "-s", api_name],
        capture_output=True,
        text=True
    )


# Function to write API key to the Keychain
def add_to_keychain(api_user, api_name, api_key):
    """
    Adds an API key to the system keychain if it doesn't already exist.
    """
    creation_date = check_keychain(api_name)
    if creation_date:
        if datetime.now() - creation_date > timedelta(days=30):
            print(f"API key for {api_name} is older than 30 days. Deleting and adding a new one.")
            delete_keychain(api_name)
        else:
            print(f"API key for {api_name} is up-to-date.")
            return
    else:
        # If creation_date is None, ensure the key is deleted before adding
        delete_keychain(api_name)
        
    print("Adding API key to the System Keychain")
    result = subprocess.run(
        ["security", "add-generic-password", "-a", api_user, "-s", api_name, "-w", api_key, "-A", "-T", "",
         "/Library/Keychains/System.keychain"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Failed to add API key to the keychain: {result.stderr}")
        exit(1)
    else:
        print(f"Successfully added API key for {api_name} to the keychain.")


# Variables
api_user = "your_api_user"  # Define your API user
api_name = "your_api_name"  # Define the name or label for the API key in the keychain
api_key = "your_api_key"  # Define your actual API key

# Execute the functions
add_to_keychain(api_user, api_name, api_key)
