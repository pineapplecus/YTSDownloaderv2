# YTSDownloader
For Downloading torrents off yts.mx

## Setup:
1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

## Usage:
```bash
# Make sure virtual environment is activated first
source venv/bin/activate

# First time setup - set your download directory
python TorrentGrabber.py --set-download-dir ~/Downloads

# Basic usage
python TorrentGrabber.py "Inception"

# Multiple movies
python TorrentGrabber.py "Inception" "The Matrix" "Interstellar"

# For remote servers or headless environments
python TorrentGrabber.py --headless "Inception"

# Show current configuration
python TorrentGrabber.py --show-config

# Show help
python TorrentGrabber.py -h
```

### CLI Options:
- `movies`: Name(s) of movie(s) to search for
- `--headless`: Run browser in headless mode (useful for remote servers)
- `--set-download-dir PATH`: Set and save the download directory
- `--show-config`: Display current configuration settings
- `-h, --help`: Show help message

### Configuration:
The script automatically saves your download directory preference to `~/.ytsdownloader_config.json`. On first run, it will use `~/Downloads` as the default directory and create it if it doesn't exist.

![Bot in Action!](working.gif)

## Purpose:
for educational purposes 💯

## Requirements:
- Python 3.x
- Virtual environment (recommended)
- Dependencies listed in [`requirements.txt`](requirements.txt:1)
- [Qbittorrent CLI](https://github.com/fedarovich/qbittorrent-cli) - Used for opening and downloading torrent files

## Note for Linux Users:
If you encounter an "externally-managed-environment" error when installing packages, this is normal on modern Linux distributions. The virtual environment setup above resolves this issue by creating an isolated Python environment for the project.

