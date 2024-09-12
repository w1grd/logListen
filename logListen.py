import socket
import requests
import re
import logging
import os
import signal
import sys
import time
import json
import threading
import configparser
from retrying import retry

# Set up config parser
config = configparser.ConfigParser()

# Provide default values in case the config file is missing entries
defaults = {
    'LOG_FILE': 'udp_listener.log',  # Default log file
    'UDP_IP': '0.0.0.0',  # Listen on all interfaces
    'UDP_PORT': '2237',  # Default UDP port
    'QUEUE_RETRY_INTERVAL': '300'  # Default retry interval is 5 minutes (300 seconds)
}

# Read the config file (you can specify a path if needed)
config.read('config.ini')

# If any value is missing in the config file, fall back to the default
LOG_FILE = config.get('settings', 'LOG_FILE', fallback=defaults['LOG_FILE'])
UDP_IP = config.get('settings', 'UDP_IP', fallback=defaults['UDP_IP'])
UDP_PORT = int(config.get('settings', 'UDP_PORT', fallback=defaults['UDP_PORT']))
QUEUE_RETRY_INTERVAL = int(config.get('settings', 'QUEUE_RETRY_INTERVAL', fallback=defaults['QUEUE_RETRY_INTERVAL']))
QRZ_API_KEY = config.get('settings', 'QRZ_API_KEY', fallback=None)

# Raise an error if the API key is not provided (no default for this one)
if QRZ_API_KEY is None:
    raise ValueError("QRZ_API_KEY must be set in the config file!")

QRZ_LOGBOOK_API_URL = 'https://logbook.qrz.com/api'
QUEUE_FILE = 'queue.json'  # File to store queued ADIF records
EXCEPTION_FILE = 'exceptions.json'  # File to store exceptions

# Configure logging to write to a file
logging.basicConfig(
    filename=LOG_FILE,  # Log to this file
    level=logging.INFO,  # Set the logging level (INFO, DEBUG, etc.)
    format='%(asctime)s %(levelname)s: %(message)s',  # Log message format
    filemode='a'  # 'a' for append mode, 'w' for overwrite mode
)


def load_queue():
    """Load the queue of failed messages from a file."""
    if os.path.exists(QUEUE_FILE):
        logging.info("Loading queued records")
        with open(QUEUE_FILE, 'r') as file:
            return json.load(file)
    return []


def save_queue(queue):
    """Save the queue to a file."""
    with open(QUEUE_FILE, 'w') as file:
        json.dump(queue, file)


def move_to_exception(adif_message):
    """Move a failed message to the exception file."""
    if os.path.exists(EXCEPTION_FILE):
        with open(EXCEPTION_FILE, 'r') as file:
            exceptions = json.load(file)
    else:
        exceptions = []

    exceptions.append(adif_message)
    with open(EXCEPTION_FILE, 'w') as file:
        json.dump(exceptions, file)
    logging.info(f"Moved message to exception file: {adif_message}")


def queue_adif_message(adif_message):
    """Add an ADIF message to the queue and save it only if it doesn't already exist."""
    queue = load_queue()

    # Check if the message is already in the queue
    if adif_message not in queue:
        queue.append(adif_message)
        save_queue(queue)
        logging.info(f"Queued failed message: {adif_message}")
    else:
        logging.info(f"Message already in queue, skipping: {adif_message}")


def retry_queue():
    """Attempt to resend messages from the queue immediately on startup, then periodically retry."""
    queue = load_queue()
    total_records = len(queue)
    successfully_sent = 0

    if queue:
        logging.info(f"Retrying {total_records} messages in the queue on startup...")
        for adif_message in queue[:]:
            try:
                log_to_qrz(adif_message)  # Attempt to resend
                queue.remove(adif_message)  # Remove on success
                successfully_sent += 1
                save_queue(queue)
                logging.info("Successfully retried message on startup")
                time.sleep(1)  # Wait 1 second between messages
            except requests.exceptions.RequestException:
                logging.error(f"Retry failed for message: {adif_message}")
                continue  # Keep in queue if still failing

    logging.info(f"Total records: {total_records}, Successfully sent: {successfully_sent}")

    # After initial retry, periodically retry the queue
    while True:
        time.sleep(QUEUE_RETRY_INTERVAL)  # Wait for the retry interval (default 5 minutes)
        queue = load_queue()
        total_records = len(queue)
        successfully_sent = 0

        if queue:
            logging.info(f"Retrying {total_records} messages in the queue...")
            for adif_message in queue[:]:
                try:
                    log_to_qrz(adif_message)  # Attempt to resend
                    queue.remove(adif_message)  # Remove on success
                    successfully_sent += 1
                    save_queue(queue)
                    logging.info("Successfully retried message")
                    time.sleep(1)  # Wait 1 second between messages
                except requests.exceptions.RequestException:
                    logging.error(f"Retry failed for message: {adif_message}")
                    continue  # Keep in queue if still failing

        logging.info(f"Total records: {total_records}, Successfully sent: {successfully_sent}")


# Function to log contact data to QRZ.com
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def log_to_qrz(adif_message):
    try:
        # Ensure <eor> is added to the end of the ADIF message
        if not adif_message.endswith('<eor>'):
            adif_message += '<eor>'

        # Create the POST data
        post_data = {
            'KEY': QRZ_API_KEY,
            'ACTION': 'INSERT',
            'ADIF': adif_message
        }

        # Send the POST request to the QRZ API
        logging.info(f"Sending message to QRZ: {adif_message}")
        response = requests.post(QRZ_LOGBOOK_API_URL, data=post_data, timeout=10)
        response.raise_for_status()

        # Check if the result is not OK, move to exception
        if "RESULT=OK" not in response.text:
            logging.error(f"QRZ API returned an error: {response.text}")
            move_to_exception(adif_message)
        else:
            logging.info(f"Log response: {response.status_code}, {response.text}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error logging to QRZ: {e}")
        queue_adif_message(adif_message)  # Queue message if it fails
        raise


# Parse ADIF fields from the message
def parse_adif(adif_message):
    adif_data = {}
    fields = re.findall(r'<([^:]+):(\d+)>([^<]+)', adif_message)
    for field in fields:
        key, length, value = field
        adif_data[key] = value
    return adif_data


def signal_handler(sig, frame):
    logging.info("Shutting down gracefully...")
    sock.close()
    sys.exit(0)


# Set up the UDP listener
def start_udp_listener():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((UDP_IP, UDP_PORT))
        logging.info(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}...")

        while True:
            data, addr = sock.recvfrom(1024)  # Buffer size of 1024 bytes
            message = data.decode('utf-8', errors='ignore')
            logging.info(f"Received message: {message}")

            # Extract the ADIF data part from the message
            if '<EOH>' in message:
                adif_message = message.split('<EOH>')[1]  # Only the ADIF part
                parsed_data = parse_adif(adif_message)

                # Build the ADIF string to send to QRZ
                adif_to_send = ''.join([f"<{key}:{len(value)}>{value}" for key, value in parsed_data.items()])

                # Log the data to QRZ
                log_to_qrz(adif_to_send)

    except socket.error as e:
        logging.error(f"Socket error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        sock.close()


# Start queue retry thread
queue_thread = threading.Thread(target=retry_queue, daemon=True)
queue_thread.start()

# Graceful shutdown on SIGINT or SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    logging.info("Starting logListen service")
    start_udp_listener()
    queue_thread.join()
