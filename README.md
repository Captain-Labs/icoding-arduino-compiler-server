# High-Performance Arduino Compilation Backend Server

A lightweight, robust, and production-ready Python compilation server that exposes a REST API wrapping `arduino-cli`. It is designed to safely and efficiently compile Arduino block/code sketches, return compiled Intel Hex files, manage external libraries, cache repeated sketches, and handle high-concurrency requests using thread-safe compilation queues.

This package is designed to run locally on your system, allowing you or other devices on your local network (LAN) to compile Arduino code without needing a public internet connection.

---

## Key Features

1. **Local Network Ready**: Automatically binds to all network interfaces (`0.0.0.0`), allowing any computer, phone, or tablet on your local Wi-Fi to use the compiler.
2. **Lightweight API**: Clean Flask endpoints for compilation, stats, health checks, and library management.
3. **Thread-Safe Compilation Queue**: Prevents CPU spikes by queuing compilation requests and running them through managed workers.
4. **Intelligent Caching**: Skips compiling identical code structures by storing hashes and hexes in a disk cache (`hex_cache.json`), delivering compiles in `0ms`.
5. **Auto-Library & Core Installer**: Automatically installs standard AVR cores and any missing library dependencies on startup.
6. **Security Hardening**: Limits payload size, checks source code against blocked dangerous keywords, and runs compiles inside isolated, self-purging directories.

---

## File Structure

```text
open-source-server/
├── server.py              # Main Flask router & startup orchestration sequence
├── compiler.py            # Code compilation wrapper, syntax check, and path manager
├── config.py              # Global server settings, limits, security lists, and common cache pre-fills
├── prod_server.py         # Waitress production server bootstrap entrypoint
├── queue_manager.py       # Thread-safe queue processor for safe compilation sequencing
├── scheduler.py           # Background cron task managing periodic index updates
├── library_manager.py     # Wrapper to install, list, search, and uninstall Arduino libraries
├── cache.py               # Memory and disk caching implementation for hex output
├── requirements.txt       # Python environment dependencies
├── install.sh             # Optional one-click VPS deployment script
├── arduino-cli.yaml       # Template configuration file mapping relative library directories
└── .gitignore             # Git exclusion rules
```

---

## Setup & Running Locally

Follow these steps to run the server on your local machine:

### 1. Prerequisites
* **Python**: Version `3.10` or higher.
* **Arduino CLI**: Must be installed and added to your system's path.
  * **macOS/Linux**:
    ```bash
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sudo BINDIR=/usr/local/bin sh
    ```
  * **Windows**: Download the installer from the [Arduino CLI Releases page](https://github.com/arduino/arduino-cli/releases) and add the installation folder to your system Environment Variables (`PATH`).
  * Verify installation by running: `arduino-cli version`

### 2. Setup the Virtual Environment
Navigate to the directory in your terminal and run:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
# .\venv\Scripts\activate.bat

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Run the Server
Start the production-ready server using `prod_server.py`:
```bash
python prod_server.py
```
The server will boot up, verify `arduino-cli` is present, auto-install the `arduino:avr` core, download pre-configured libraries, and begin listening on:
`http://localhost:5000` (accessible on your own machine) and `http://0.0.0.0:5000` (listening on all local network interfaces).

---

## Connecting Devices on your Local Network (LAN)

Because the server binds to `0.0.0.0`, any device connected to the same Wi-Fi or local network can use your computer as their compile server.

### Step 1: Find your Local IP Address
Open a terminal/command prompt on the server machine:
* **macOS/Linux**: Run `ifconfig` or `ip a` (look for your Wi-Fi interface IP, e.g., `192.168.1.15` or `10.0.0.5`).
* **Windows**: Run `ipconfig` (look for the IPv4 Address under Wireless LAN adapter or Ethernet, e.g., `192.168.1.20`).

### Step 2: Configure the Client IDE
1. On the client device, open your block coding IDE.
2. Go to the **COMPILER SERVER** panel in settings.
3. Select **Custom Server**.
4. Enter your server URL using the local IP:
   `http://<YOUR_LOCAL_IP>:5000` (e.g., `http://192.168.1.15:5000`).
5. Click **Test Connection**. It should connect and show a green **Connected** status!

> [!IMPORTANT]
> **Mixed Content Web Security Rule**:
> To connect client browsers to your local network server, you **MUST** serve/load the IDE page over **`http://`** (not secure `https://`). Secure HTTPS browser tabs block requests to local HTTP networks by default.

---

## Advanced: Deploying to a Cloud VPS (Oracle Cloud, AWS, DigitalOcean)

If you want to host this server permanently in the cloud on an Ubuntu VPS, you can use the automated one-click installer or set it up manually.

### One-Click Cloud Installation
Connect to your fresh Ubuntu VPS via SSH and run:

```bash
curl -fsSL https://raw.githubusercontent.com/yourrepo/arduino-server/main/install.sh | sudo bash
```
*(Make sure to replace `yourrepo` with your actual GitHub username/repository).*

### Manual Cloud Setup
1. **Firewalls**: Open port `5000` (TCP) in your cloud provider's console security list and inside your VPS OS (`sudo iptables -I INPUT 5 -p tcp --dport 5000 -m state --state NEW,ESTABLISHED -j ACCEPT && sudo netfilter-persistent save`).
2. **Setup**: Clone the repo to `/opt/arduino-server`, set up a virtual environment, install requirements, and run index updates.
3. **Daemonize (systemd)**: Create `/etc/systemd/system/arduino-server.service`:
   ```ini
   [Unit]
   Description=Arduino Compilation Server
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/opt/arduino-server
   ExecStart=/opt/arduino-server/venv/bin/python prod_server.py
   Restart=always
   RestartSec=3
   Environment=PATH=/usr/local/bin:/usr/bin:/bin
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```
4. Start the service: `sudo systemctl daemon-reload && sudo systemctl enable --now arduino-server.service`.

---

## API Reference

* `POST /compile` — Compiles code and returns Hex output.
* `GET /health` — Returns status, uptime, worker count, and cache stats.
* `GET /stats` — Returns overall compiler hit/miss statistics.
* `GET /libraries/installed` — Lists installed libraries.

---

## License

This project is licensed under the MIT License. Contributions are welcome!
