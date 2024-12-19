import paramiko
import time

# SSH info for each sensor
sensors = {
    "sensor1": {
        "ip": "xxx.xxx.x.x", # change IP for each sensor
        "script": "fina.py",
        "username": "sensor1",
        "password": "sensor1"
    },
    "sensor2": {
        "ip": "xxx.xxx.x.x",
        "script": "BT_sensor2.py",
        "username": "sensor2",
        "password": "sensor2"
    },
    "sensor3": {
        "ip": "xxx.xxx.x.x",
        "script": "BT_sensor3.py",
        "username": "sensor3",
        "password": "sensor3"
    },
    "sensor4": {
        "ip": "xxx.xxx.x.x",
        "script": "BT_sensor4.py",
        "username": "sensor4",
        "password": "sensor4"
    }
}


# Start script
def start_script(ip, script, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        # Change directory and start the script
        command = f"cd Desktop/BT && python {script}"
        ssh.exec_command(command)
        print(f"Started {script} on {ip}")
        ssh.close()
    except Exception as e:
        print(f"Failed to start {script} on {ip}: {e}")


# Stop script
def stop_script(ip, script, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password)

        
        command = f"pkill -f {script}"
        ssh.exec_command(command)
        print(f"Stopped {script} on {ip}")
        ssh.close()
    except Exception as e:
        print(f"Failed to stop {script} on {ip}: {e}")


# Function to manage the start and stop process
def manage_sensors():
    # Start scripts on all sensors
    for sensor_name, details in sensors.items():
        start_script(details["ip"], details["script"], details["username"], details["password"])

    # Run script on pi for 3 minutes
    print("Scripts running for 3 minutes...")
    time.sleep(180)

    # Stop scripts on all sensors
    for sensor_name, details in sensors.items():
        stop_script(details["ip"], details["script"], details["username"], details["password"])


if __name__ == "__main__":
    manage_sensors()
