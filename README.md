# YTSDownloader v2
Professional-grade automated movie downloading system for YTS torrents with real-time progress monitoring.

![Bot in Action!](working.gif)

## Features
- 🎬 **Global Command** - Run `TorrentGrabber "Movie Name"` from anywhere
- 🎨 **Beautiful UI** - Clean, professional interface with consistent formatting
- 📊 **Real-time Progress** - Live download monitoring with speed and ETA
- 🚀 **Full Automation** - One command → streaming library
- ⚙️ **Smart Configuration** - Persistent settings for downloads and qBittorrent
- 📁 **Jellyfin Integration** - Automatic media library updates
- 🎮 **Steam Deck Optimized** - Perfect for Bazzite Gaming Mode

## Quick Start

### 1. Initial Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
python3 -m pip install -r requirements.txt

# Create global command (recommended)
cat > ~/.local/bin/TorrentGrabber << 'EOF'
#!/bin/bash
cd ~/YTSDownloader
source venv/bin/activate
exec python3 TorrentGrabber.py "$@"
EOF
chmod +x ~/.local/bin/TorrentGrabber
```

### 2. Basic Usage
```bash
# Download any movie (headless by default)
TorrentGrabber "Inception"
TorrentGrabber "The Dark Knight"
TorrentGrabber "Interstellar"

# Show configuration
TorrentGrabber --show-config

# Set download directory
TorrentGrabber --set-download-dir ~/Movies
```

## Full Automation Setup

### 3. qBittorrent Web UI Configuration

#### Step 1: Enable Web UI
1. **Open qBittorrent** (via VNC or Desktop Mode)
2. **Go to:** Tools → Preferences → Web UI
3. **Enable:** "Web User Interface"
4. **Set:**
   - IP Address: `localhost` or `127.0.0.1`
   - Port: `8082` (or any available port like 8080, 8081)
   - Username: `admin`
   - Password: `111111` (or your choice)
5. **Apply and restart qBittorrent**

#### Step 2: Configure in YTSDownloader
```bash
# Set qBittorrent connection details
TorrentGrabber --set-qbt-host localhost
TorrentGrabber --set-qbt-port 8082
TorrentGrabber --set-qbt-username admin
TorrentGrabber --set-qbt-password 111111

# Verify settings
TorrentGrabber --show-config
```

### 4. Watch Folder Setup

#### Step 1: Create Watch Folder
```bash
# Create the watch folder
mkdir -p ~/TorrentWatch
chmod 777 ~/TorrentWatch
```

#### Step 2: Enable in qBittorrent
1. **Open qBittorrent** (via VNC or Desktop Mode)
2. **Go to:** Tools → Preferences → Downloads
3. **Enable:** "Automatically add torrents from:"
4. **Set path:** `/home/username/TorrentWatch` (replace username with your actual username)
5. **Set download location:** `/home/username/jellyfin/media/Movies` (for Jellyfin integration)
6. **Apply settings**

### 5. Jellyfin Media Server (Optional)

#### Setup Jellyfin:
```bash
# Create Jellyfin directories
mkdir -p ~/jellyfin/{config,cache,media/Movies}
sudo chmod -R 777 ~/jellyfin

# Run Jellyfin container
podman run -d --name jellyfin \
  -v ~/jellyfin/config:/config:Z \
  -v ~/jellyfin/cache:/cache:Z \
  -v ~/jellyfin/media:/media:Z \
  -p 8096:8096 \
  --restart unless-stopped \
  jellyfin/jellyfin:latest
```

#### Configure Jellyfin:
1. **Open:** `http://your-ip:8096`
2. **Complete initial setup** (create admin account)
3. **Add library:** Movies → `/media/Movies`
4. **Enable:** "Monitor folder for changes" and "Automatically refresh metadata"

### 6. VNC Remote Access (For GUI Configuration)

#### Connect to VNC:
- **URL:** `vnc://your-ip:5901`
- **Password:** Set during VNC setup

## Configuration Options

### Download Directory:
```bash
TorrentGrabber --set-download-dir ~/Movies
```

### qBittorrent Web UI:
```bash
TorrentGrabber --set-qbt-host localhost
TorrentGrabber --set-qbt-port 8082
TorrentGrabber --set-qbt-username admin
TorrentGrabber --set-qbt-password your-password
```

### View All Settings:
```bash
TorrentGrabber --show-config
```

## CLI Options

### Basic Commands:
- `TorrentGrabber "Movie Name"` - Download a movie
- `TorrentGrabber --show-config` - Show current configuration
- `TorrentGrabber -h` - Show help

### Configuration Commands:
- `--set-download-dir PATH` - Set download directory
- `--set-qbt-host HOST` - Set qBittorrent Web UI host
- `--set-qbt-port PORT` - Set qBittorrent Web UI port
- `--set-qbt-username USER` - Set qBittorrent Web UI username
- `--set-qbt-password PASS` - Set qBittorrent Web UI password

### Advanced Options:
- `--gui` - Run browser with GUI (default is headless mode)

## Troubleshooting

### "externally-managed-environment" Error:
This is normal on modern Linux distributions. Use the virtual environment setup above.

### qBittorrent Web UI Not Working:
1. Check if qBittorrent is running
2. Verify Web UI is enabled in qBittorrent preferences
3. Try different ports (8080, 8081, 8082)
4. Use `localhost` or `127.0.0.1` as the IP address
5. Check firewall settings

### Watch Folder Not Working:
1. Ensure watch folder is enabled in qBittorrent preferences
2. Check folder permissions: `chmod 777 ~/TorrentWatch`
3. Verify the exact path in qBittorrent matches your folder
4. Restart qBittorrent after enabling watch folder

### Progress Monitoring Not Working:
1. Ensure qBittorrent Web UI is properly configured
2. Check that the port matches your configuration
3. Verify username and password are correct
4. Use `TorrentGrabber --show-config` to check settings

### VNC Connection Issues:
1. Ensure VNC server is running: `vncserver :1`
2. Check firewall: `sudo firewall-cmd --add-port=5901/tcp`
3. Try IP address instead of hostname

## Requirements
- Python 3.x
- Virtual environment (recommended)
- qBittorrent with Web UI enabled
- Dependencies: pyppeteer, requests, tqdm, asyncio

## Purpose
For educational purposes 💯

## Architecture

### Complete Automation Pipeline:
1. **YTSDownloader** → Downloads torrent files to watch folder
2. **qBittorrent** → Processes watch folder → Downloads movies
3. **Jellyfin** → Scans media folder → Updates library
4. **Result** → Movies available for streaming

### File Structure:
```
~/YTSDownloader/          # Main project directory
├── TorrentGrabber.py     # Main script
├── requirements.txt      # Python dependencies
├── venv/                 # Virtual environment
└── README.md            # This file

~/TorrentWatch/           # qBittorrent watch folder
~/.local/bin/TorrentGrabber  # Global command script
~/.ytsdownloader_config.json # Configuration file
```

## Example Workflow

### Complete Setup Example:
```bash
# 1. Install YTSDownloader
git clone https://github.com/pineapplecus/YTSDownloaderv2.git
cd YTSDownloaderv2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Create global command
cat > ~/.local/bin/TorrentGrabber << 'EOF'
#!/bin/bash
cd ~/YTSDownloaderv2
source venv/bin/activate
exec python3 TorrentGrabber.py "$@"
EOF
chmod +x ~/.local/bin/TorrentGrabber

# 3. Configure qBittorrent (after setting up Web UI in GUI)
TorrentGrabber --set-qbt-port 8082
TorrentGrabber --set-qbt-username admin
TorrentGrabber --set-qbt-password 111111

# 4. Create watch folder
mkdir -p ~/TorrentWatch
chmod 777 ~/TorrentWatch

# 5. Download movies!
TorrentGrabber "Inception"
```

## Support
- **VNC Access:** For GUI configuration when needed
- **SSH Access:** For command-line operations
- **Web Interfaces:** qBittorrent (port 8082), Jellyfin (port 8096)
- **GitHub:** https://github.com/pineapplecus/YTSDownloaderv2
