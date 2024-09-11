
# logListen

**Author:** Perry Donham, W1GRD (perry@w1grd.radio)
**Version:** 0.2 (September 11, 2024)

logListen is a Python utility that listens for ADIF-formatted messages via UDP from any compatible ham radio logging program and forwards new QSO records to the QRZ XML API for automatic logbook updates.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Logging](#logging)
- [Troubleshooting](#troubleshooting)
- [Running in the background](#background)
- [Contributing](#contributing)
- [License](#license)

## Features
- Listens for UDP broadcasted ADIF messages from logging programs.
- Parses ADIF data and forwards new QSO records to the QRZ.com logbook using their XML API.
- Configurable via a simple `config.ini` file.
- Includes logging for audit trails and troubleshooting.

## Requirements
- Python 3.7+
- A valid QRZ.com API key for the XML logbook service.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/w1grd/logListen.git
   cd logListen
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a configuration file (`config.ini`), described in the [Configuration](#configuration) section.

## Configuration

The configuration for `logListen` is done via a `config.ini` file in the same directory as the script. Below is an example `config.ini` file:

```ini
[settings]
LOG_FILE = /path/to/your/logfile.log
UDP_IP = 0.0.0.0
UDP_PORT = 2237
QRZ_API_KEY = your_qrz_api_key
```

### Configuration Parameters:
- **LOG_FILE**: The path to the log file where messages will be logged. If omitted, it defaults to `udp_listener.log` in the current directory.
- **UDP_IP**: The IP address to bind the UDP listener. By default, `0.0.0.0` listens on all available network interfaces.
- **UDP_PORT**: The port on which the UDP listener will receive ADIF messages. Default is `2237`.
- **QRZ_API_KEY**: **(Required)** Your QRZ XML Logbook API key. You must generate this key from your QRZ.com account.

> **Note:** The `QRZ_API_KEY` is required and does not have a default value. You must set this in the `config.ini` file.

## Usage

Once you have set up the configuration file and installed the necessary dependencies, you can start the listener:

1. Run the script:
   ```bash
   python logListen.py
   ```

2. The script will begin listening for UDP packets on the specified IP and port, parse the ADIF data, and send new QSO records to the QRZ logbook via their API.

3. To run the script in the background, 
## Logging

`logListen` will log key events, including received ADIF messages, API responses, and errors to a log file. By default, this log file is `udp_listener.log`, but you can specify a custom log file path in the `config.ini` file.

Log entries will include timestamps and information on success or failure when sending data to the QRZ API.

## Troubleshooting

### Common Issues:

#### 1. **Permission Denied (403) from QRZ API**
- Ensure that your QRZ API key is correct and properly set in the `config.ini` file.

#### 2. **Socket Error**
- Ensure the UDP IP and port in your `config.ini` file are correct and that the port is not blocked by a firewall.

#### 3. **Missing `config.ini` File**
- Make sure that the `config.ini` file exists in the same directory as `logListen.py`, and that the necessary settings, especially the QRZ API key, are properly configured.

#### 4. **No ADIF Messages Received**
- Ensure that the logging program you're using is broadcasting ADIF messages on the correct IP and port as specified in `config.ini`.

## Contributing

Feel free to submit issues or pull requests to improve this project! You can fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
