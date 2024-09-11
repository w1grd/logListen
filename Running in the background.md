
# Running `logListen.py` in the Background

Here are different ways to run the `logListen.py` script in the background, depending on the environment and the level of control you need.

## 1. Using `nohup` (Linux/MacOS)

You can run the script in the background using `nohup`:

```bash
nohup python logListen.py > output.log 2>&1 &
```

- `nohup`: Prevents the process from being killed after logging out.
- `> output.log 2>&1`: Redirects both stdout and stderr to `output.log`.
- `&`: Puts the process in the background.

To view the running process:

```bash
ps aux | grep logListen.py
```

To kill the process, find its PID and run:

```bash
kill <PID>
```

## 2. Using `screen` (Linux/MacOS)

`screen` allows you to run the script in a separate terminal session and keep it running even after you disconnect.

1. Start a new screen session:

   ```bash
   screen -S logListen
   ```

2. Run the script:

   ```bash
   python logListen.py
   ```

3. Detach from the screen session (press `Ctrl+A` followed by `D`).

4. To reattach to the session:

   ```bash
   screen -r logListen
   ```

## 3. Using `tmux` (Linux/MacOS)

Similar to `screen`, `tmux` allows you to run persistent terminal sessions and manage multiple terminals.

1. Start a `tmux` session:

   ```bash
   tmux new -s logListen
   ```

2. Run the script:

   ```bash
   python logListen.py
   ```

3. Detach from the session by pressing `Ctrl+B`, then `D`.

4. To reattach:

   ```bash
   tmux attach -t logListen
   ```

## 4. Using `systemd` (Linux)

You can run the script as a background service using `systemd`:

1. Create a service file:

   ```bash
   sudo nano /etc/systemd/system/logListen.service
   ```

2. Add the following content:

   ```ini
   [Unit]
   Description=logListen Service
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your/logListen.py
   WorkingDirectory=/path/to/your/project
   StandardOutput=append:/path/to/log/output.log
   StandardError=append:/path/to/log/error.log
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl enable logListen.service
   sudo systemctl start logListen.service
   ```

4. Check the status:

   ```bash
   sudo systemctl status logListen.service
   ```

## 5. Using `launchd` (MacOS)

For MacOS, `launchd` is the equivalent of `systemd`. You can create a service that runs at startup or in the background.

1. Create a `.plist` file in `~/Library/LaunchAgents/`:

   ```bash
   nano ~/Library/LaunchAgents/com.w1grd.logListen.plist
   ```

2. Add the following content:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.w1grd.logListen</string>

       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/path/to/your/logListen.py</string>
       </array>

       <key>WorkingDirectory</key>
       <string>/path/to/your/project</string>

       <key>StandardOutPath</key>
       <string>/path/to/log/output.log</string>
       <key>StandardErrorPath</key>
       <string>/path/to/log/error.log</string>

       <key>RunAtLoad</key>
       <true/>
   </dict>
   </plist>
   ```

3. Load the service:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.w1grd.logListen.plist
   ```

4. To unload the service (stop it):

   ```bash
   launchctl unload ~/Library/LaunchAgents/com.w1grd.logListen.plist
   ```
