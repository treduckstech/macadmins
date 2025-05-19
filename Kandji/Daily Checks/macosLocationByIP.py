#!/usr/bin/env python3
"""
Estimates a Mac's location using its public IP address and updates the device
notes via the Kandji API.

Author: Ben Rillie <ben@treducks.tech>
WARNING: Use at your own risk.
License: MIT
"""

import subprocess
import sys
import importlib
import json

# Function to print Python and pip versions
def print_versions():
    # Print Python version
    python_version = sys.version
    print(f"Python version: {python_version}")

    # Check and print pip version
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
        pip_version = result.stdout
        print(f"pip version: {pip_version}")
    except subprocess.CalledProcessError as e:
        print(f"Error checking pip version: {e}")

# Function to get the current console user
def get_console_user():
    result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of current user'], capture_output=True, text=True)
    return result.stdout.strip()

# Function to check if a package is installed and install it if it isn't
def install_and_import(package, user):
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"{package} not found. Installing...")
        subprocess.check_call(["sudo", "-u", user, sys.executable, "-m", "pip", "install", package])
        importlib.invalidate_caches()
        globals()[package] = importlib.import_module(package)

# Ensure required packages are installed
console_user = get_console_user()
print(f"Running script as user: {console_user}")
print_versions()
install_and_import('requests', console_user)
install_and_import('getmac', console_user)

import requests
from getmac import get_mac_address

# Function to retrieve API key from macOS Keychain
def get_api_key(key_name):
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-w', '-s', key_name, '/Library/Keychains/System.keychain'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving password for {key_name}: {e}")
        return None

# Function to retrieve API URL from macOS Keychain
def get_api_url(url_name):
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-w', '-s', url_name, '/Library/Keychains/System.keychain'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving password for {url_name}: {e}")
        return None

# Function to retrieve IPInfo key from macOS Keychain
def get_ipinfo_key(ipinfo_key_name):
    try:
        result = subprocess.run(
            ['security', 'find-generic-password', '-w', '-s', ipinfo_key_name, '/Library/Keychains/System.keychain'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving password for {ipinfo_key_name}: {e}")
        return None

# Function to get the public IP address of the machine
def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    return response.json().get('ip')

# Function to get location information for an IP address using IPInfo API
def get_location_for_ip(ip, ipinfo_key):
    response = requests.get(f'https://ipinfo.io/{ip}?token={ipinfo_key}')
    return response.json()

# Function to get the serial number of the machine
def get_serial_number():
    result = subprocess.run(['system_profiler', 'SPHardwareDataType'], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if 'Serial Number' in line:
            return line.split(":")[1].strip()
    return 'Unknown'

# Function to get the Kandji device ID using the serial number
def get_kandji_device_id(serial_number, api_key, base_url):
    headers = {"Authorization": f"Bearer {api_key}"}
    api_url = f"{base_url}/api/v1/devices?serial_number={serial_number}"
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching device ID: {response.status_code} - {response.text}")
        return None

    try:
        device = response.json()
        print(f"Device response: {device}")
        return device[0]['device_id']
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Response content: {response.text}")

    return None

# Function to manage device notes in Kandji (delete old notes and create a new one)
def manage_device_notes(api_key, base_url, device_id, new_content):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # Step 1: Get the list of notes for the device
    url = f'{base_url}/api/v1/devices/{device_id}/notes'
    response = requests.get(url, headers=headers)
    try:
        notes_response = response.json()
        notes = notes_response.get('notes', [])
        print(f"Notes response: {notes_response}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        print(f"Response content: {response.text}")
        return

    # Ensure that notes is a list
    if not isinstance(notes, list):
        print(f"Unexpected response format: {notes}")
        return

    # Step 2: Find and delete notes that have "Location" in the content
    for note in notes:
        if 'Location' in note.get('content', ''):
            note_id = note['note_id']
            delete_url = f'{base_url}/api/v1/devices/{device_id}/notes/{note_id}'
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code in [204, 200]:
                print(f"Deleted note with note_id: {note_id}")
            else:
                print(
                    f"Failed to delete note with note_id: {note_id}, Status Code: {delete_response.status_code}, Response: {delete_response.text}")

    # Step 3: Create a new note with the new content
    new_note_content = {
        'author': 'Kandji API',
        'content': new_content,
        'device_id': device_id
    }
    create_url = f'{base_url}/api/v1/devices/{device_id}/notes'
    create_response = requests.post(create_url, headers=headers, json=new_note_content)
    if create_response.status_code == 201:
        print(f"Created new note with content: {new_note_content['content']}")
    else:
        print(
            f"Failed to create new note, Status Code: {create_response.status_code}, Response: {create_response.text}")

    print("Operation completed.")

def main():
    # Define key names for retrieving secrets
    key_name = "location_note_key"
    url_name = "api_url"
    ipinfo_key_name = "ipinfo_api_key_name"

    # Retrieve API key, base URL, and IPInfo key
    api_key = get_api_key(key_name)
    if not api_key:
        print("API key retrieval failed.")
        return

    base_url = get_api_url(url_name)
    if not base_url:
        print("API URL retrieval failed.")
        return

    ipinfo_key = get_ipinfo_key(ipinfo_key_name)
    if not ipinfo_key:
        print("IP info key retrieval failed.")
        return

    # Get public IP address
    public_ip = get_public_ip()
    print(f"Public IP: {public_ip}")

    # Get the serial number of the device
    device_serial = get_serial_number()
    print(f"Device serial: {device_serial}")

    # Get the Kandji device ID using the serial number
    device_id = get_kandji_device_id(device_serial, api_key, base_url)
    if not device_id:
        print("Could not fetch device ID.")
        return
    print(f"Device ID: {device_id}")

    # Get location information for the public IP address
    location = get_location_for_ip(public_ip, ipinfo_key)
    print(f"Location: {location}")
    if not location:
        print("Could not fetch location for IP.")
        return

    # Extract coordinates from the location data
    coordinates = location.get('loc', '').split(',')
    print(f"Coordinates: {coordinates}")
    if len(coordinates) != 2:
        print("Invalid coordinates received.")
        return

    latitude, longitude = coordinates
    google_maps_link = f'https://www.google.com/maps/search/?api=1&query={latitude},{longitude}'
    print(f"Google Maps: {google_maps_link}")

    # Create new content for the note
    new_content = f'Location: {latitude}, {longitude}, Google Maps: {google_maps_link}'

    # Manage device notes (delete old notes and create a new one)
    manage_device_notes(api_key, base_url, device_id, new_content)

if __name__ == '__main__':
    main()
