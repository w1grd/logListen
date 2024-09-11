# logListen
# v0.2 11 Sep 2024
# Author: Perry W1GRD perry@w1grd.radio
# Listen for ADIF formatted messages via UDP from any
# logging program that supports it and send new QSO records
# to the QRZ XML API

import socket
import requests
import re
import logging
import os
import signal
import sys
import configparser  # Import configparser for reading config files
from retrying import retry

# Set up config parser
config = configparser.ConfigParser()

# Provide default values in case the config file is missing entries
defaults = {
    'LOG_FILE': 'udp_listener.log',  # Default log file
    'UDP_IP': '0.0.0.0',  # Listen on all interfaces
    'UDP_PORT': '2237'  # Default UDP port
}

# Read the config file (you can specify a path if needed)
config.read('config.ini')

# If any value is missing in the config file, fall back to the default
LOG_FILE = config.get('settings', 'LOG_FILE', fallback=defaults['LOG_FILE'])
UDP_IP = config.get('settings', 'UDP_IP', fallback=defaults['UDP_IP'])
UDP_PORT = int(config.get('settings', 'UDP_PORT', fallback=defaults['UDP_PORT']))
QRZ_API_KEY = config.get('settings', 'QRZ_API_KEY', fallback=None)

# Raise an error if the API key is not provided (no default for this one)
if QRZ_API_KEY is None:
    raise ValueError("QRZ_API_KEY must be set in the config file!")

QRZ_LOGBOOK_API_URL = 'https://logbook.qrz.com/api'

# Configure logging to write to a file
logging.basicConfig(
    filename=LOG_FILE,  # Log to this file
    level=logging.INFO,  # Set the logging level (INFO, DEBUG, etc.)
    format='%(asctime)s %(levelname)s: %(message)s',  # Log message format
    filemode='a'  # 'a' for append mode, 'w' for overwrite mode
)

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
        response = requests.post(QRZ_LOGBOOK_API_URL, data=post_data, timeout=10)
        response.raise_for_status()

        # Log response
        logging.info(f"Log response: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error logging to QRZ: {e}")
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

# Graceful shutdown on SIGINT or SIGTERM
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    start_udp_listener()
