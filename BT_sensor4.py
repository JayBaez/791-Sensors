import argparse
import asyncio
import json
from datetime import datetime, timedelta
import time
from bleak import BleakScanner

# Define the paths for saving data
json_file_path = "BTbluetooth_scan_data_4.json"
txt_file_path = "BTbluetooth_scan_data_4.txt"

# Define function for RSSI to distance conversion
def rssi_to_distance(rssi):
    """ Convert RSSI value to distance (in meters) using a simple path-loss model """
    A = -60  # RSSI at 1 meter (for example)
    n = 2.6  # Path loss exponent (usually between 2 and 4 for most environments)
    distance = 10 ** ((A - rssi) / (10 * n))
    return distance

# Function to clear the files at the start
def clear_files():
    try:
        # Clear the JSON file by writing an empty array
        with open(json_file_path, "w") as json_file:
            json_file.write("[]")
        print("Old data cleared from JSON file.")

        # Clear the text file by writing an empty string
        with open(txt_file_path, "w") as txt_file:
            txt_file.write("")
        print("Old data cleared from text file.")

    except Exception as e:
        print(f"Error clearing files: {e}")

# Function to save devices to JSON and text files
def save_to_files(devices):
    try:
        # Load existing JSON data
        try:
            with open(json_file_path, "r") as json_file:
                existing_data = json.load(json_file)
        except json.JSONDecodeError:
            existing_data = []  # If file is empty or not valid JSON, start with an empty list

        # Append new devices to the existing data
        existing_data.extend(devices)

        # Save updated data back to JSON file
        with open(json_file_path, "w") as json_file:
            json.dump(existing_data, json_file, indent=4)
            print("Data saved to JSON file.")

        # Save to text file
        with open(txt_file_path, "a") as txt_file:
            for device in devices:
                # Write each device's info including ID and calculated distance
                device_info = f"{device['timestamp']}, {device['id']}, {device['name']}, {device['address']}, {device['rssi']}, {device['distance']}\n"
                txt_file.write(device_info)
            print("Data saved to text file.")

    except Exception as e:
        print(f"Error saving to files: {e}")

# Function to scan for Bluetooth devices and return data
async def scan_devices(args):
    devices_data = []
    try:
        devices = await BleakScanner.discover(
            return_adv=True,
            service_uuids=args.services,
            cb=dict(use_bdaddr=args.macos_use_bdaddr),
        )

        # Print the number of discovered devices
        print(f"Discovered {len(devices)} devices.")

        for d, a in devices.values():
            distance = rssi_to_distance(a.rssi)  # Convert RSSI to distance

            # Get the current time and round it to two decimal places
            timestamp = round(time.time(), 2)
            formatted_timestamp = datetime.fromtimestamp(timestamp).isoformat()

            device_info = {
                "timestamp": formatted_timestamp,
                "id": "sensor4",  # unique ID for each sensor
                "name": d.name if d.name else "Unknown",
                "address": d.address,
                "rssi": a.rssi,
                "distance": distance,  # Save calculated distance
            }
            devices_data.append(device_info)
            print(f"Device found: {device_info}")  # Debugging output for each device

    except Exception as e:
        print(f"Error scanning devices: {e}")

    return devices_data

# Function to wait until the next minute
async def wait_until_next_minute():
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_time = (next_minute - now).total_seconds()
    print(f"Waiting {wait_time:.2f} seconds until the next minute...")
    await asyncio.sleep(wait_time)

# Main loop to scan every 0.25 seconds and save results
async def main(args: argparse.Namespace):
    # Wait until the start of the next minute
    await wait_until_next_minute()

    while True:
        devices_data = await scan_devices(args)
        if devices_data:  # Only save if there are devices found
            print("Saving device data...")
            save_to_files(devices_data)
        else:
            print("No devices found to save.")
        await asyncio.sleep(0.25)  # Wait 0.25 seconds before the next scan

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--services", metavar="<uuid>", nargs="*", help="UUIDs of one or more services to filter for")
    parser.add_argument("--macos-use-bdaddr", action="store_true",
                        help="when true use Bluetooth address instead of UUID on macOS")
    args = parser.parse_args()

    clear_files()  # Clear the files before starting the main loop

    asyncio.run(main(args))
