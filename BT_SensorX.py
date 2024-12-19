import asyncio
import json
import os
from datetime import datetime, timedelta
from bleak import BleakScanner
import paramiko

# Define file paths
local_save_dir = "/home/sensorX/Desktop/BT/"  # Local directory on Raspberry Pi to save JSON files temporarily
os.makedirs(local_save_dir, exist_ok=True)  # Ensure the directory exists

# SSH info for the laptop(server)
laptop_ip = "xxx.xxx.x.x"  # Replace with your laptop's IP address
laptop_username = "username"  # Replace with your laptop username
laptop_password = "password"  # Replace with your laptop password
laptop_directory = "C:/path/to/file"  # Directory on your laptop where files will be saved

# RSSI to distance conversion
def rssi_to_distance(rssi):
    """Convert RSSI value to distance (in meters) using a simple path-loss model."""
    A = -60  # RSSI at 1 meter (calibrated value)
    n = 2.6  # Path loss exponent
    return 10 ** ((A - rssi) / (10 * n))

# Save device data to JSON
def save_to_file(devices, timestamp):
    """Save detected devices to a JSON file and transfer it via SCP."""
    try:
        # Save to JSON
        json_filename = f"{local_save_dir}BTbluetooth1_scan_data{timestamp}.json"
        with open(json_filename, "w") as json_file:
            json.dump(devices, json_file, indent=4)
        print(f"Saved {len(devices)} devices to {json_filename}.")

        # Transfer the file to the laptop and delete it after transfer
        ssh_and_transfer(json_filename)

    except Exception as e:
        print(f"Error saving to file: {e}")

# SSH and transfer file
def ssh_and_transfer(json_filename):
    """Transfer the JSON file to the laptop using SSH and delete it afterward."""
    try:
        #SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(laptop_ip, username=laptop_username, password=laptop_password)


        sftp = ssh.open_sftp()

        # Define remote path on the laptop
        remote_path = os.path.join(laptop_directory, os.path.basename(json_filename))

        # Transfer the file
        sftp.put(json_filename, remote_path)
        print(f"Transferred {json_filename} to {remote_path}")

        # Remove the file from Pi
        os.remove(json_filename)
        print(f"Deleted {json_filename} after transfer.")

        #close connections
        sftp.close()
        ssh.close()

    except Exception as e:
        print(f"Failed to transfer or delete {json_filename}: {e}")

# Continuous scanning and pushing to the queue
async def continuous_scan(queue):
    """Continuously scan for BLE devices and add them to the queue."""
    def detection_callback(device, advertisement_data):
        # Create device data dictionary
        timestamp = datetime.now().isoformat()
        device_info = {
            "timestamp": timestamp,
            "id": "sensorX",  # Identifier for this scanner(change for each sensor)
            "name": device.name if device.name else "Unknown",
            "address": device.address,
            "rssi": advertisement_data.rssi,
            "distance": rssi_to_distance(advertisement_data.rssi),
        }
        asyncio.create_task(queue.put(device_info))  # Add device to the queue
        print(f"Detected: {device_info}")

    scanner = BleakScanner(detection_callback)
    async with scanner:
        await asyncio.Future()  # Run the scanner indefinitely

# Save data from the queue at regular intervals
async def save_data(queue, interval):
    """Save data from the queue at fixed intervals."""
    while True:
        devices_to_save = []
        try:
            # Retrieve all devices currently in the queue
            while not queue.empty():
                devices_to_save.append(await queue.get())
            # Save devices if any are found
            if devices_to_save:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_to_file(devices_to_save, timestamp)
            else:
                print("No new data to save.")
        except Exception as e:
            print(f"Error processing data: {e}")
        # Wait for the next save interval
        await asyncio.sleep(interval)

# Wait until the next minute for starting code (helps with delay with other sensors starting)
async def wait_until_next_minute():
    """Wait until the start of the next minute."""
    now = datetime.now()
    next_minute = (now + timedelta(minutes=1)).replace(second=0, microsecond=0)
    wait_time = (next_minute - now).total_seconds()
    print(f"Waiting {wait_time:.2f} seconds until the next minute...")
    await asyncio.sleep(wait_time)
    print(f"Started at {next_minute}")


async def main():
    """Main function to handle scanning and saving."""

    await wait_until_next_minute()

    # Create an asyncio queue for device data
    queue = asyncio.Queue()

    # Interval for saving data (in seconds)
    save_interval = .25  # Save data every .25-.75 seconds for real time collection

    # Start scanning and saving tasks
    scanner_task = asyncio.create_task(continuous_scan(queue))
    saver_task = asyncio.create_task(save_data(queue, save_interval))

    # Run tasks indefinitely
    await asyncio.gather(scanner_task, saver_task)

if __name__ == "__main__":
    asyncio.run(main())
