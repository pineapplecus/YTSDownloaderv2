import sys
import os
import asyncio
import argparse
import json
import requests
import time
from pathlib import Path
from pyppeteer import launch
from tqdm import tqdm


# Using Qbittorrent CLI to automate: https://github.com/fedarovich/qbittorrent-cli/releases/tag/v1.7.21116.1

CONFIG_FILE = Path.home() / ".ytsdownloader_config.json"
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
DEFAULT_QBITTORRENT_CONFIG = {
    "host": "localhost",
    "port": 8082,
    "username": "admin",
    "password": "111111"
}


def get_qbittorrent_config():
    """Get qBittorrent Web UI configuration"""
    config = load_config()
    qbt_config = config.get("qbittorrent", DEFAULT_QBITTORRENT_CONFIG.copy())
    
    # Ensure all required keys exist
    for key, default_value in DEFAULT_QBITTORRENT_CONFIG.items():
        if key not in qbt_config:
            qbt_config[key] = default_value
    
    return qbt_config

def save_qbittorrent_config(qbt_config):
    """Save qBittorrent Web UI configuration"""
    config = load_config()
    config["qbittorrent"] = qbt_config
    return save_config(config)

async def wait_for_watch_folder_processing(torrent_filename, torrent_hash):
    """Wait for qBittorrent to process the torrent file from watch folder"""
    watch_folder = os.path.expanduser("~/TorrentWatch")
    torrent_path = os.path.join(watch_folder, torrent_filename)
    
    print("⏳ Waiting for qBittorrent to process torrent...")
    
    # Wait for file to be processed (disappear from watch folder)
    for attempt in range(30):  # Wait up to 60 seconds
        if not os.path.exists(torrent_path):
            print("✅ Download started!")
            break
        await asyncio.sleep(2)
    else:
        print("⚠️  Torrent not processed - check qBittorrent watch folder settings")
        return False
    
    # Now look for the download in qBittorrent
    return await monitor_qbittorrent_download(torrent_hash)

async def monitor_qbittorrent_download(torrent_hash, movie_name_shown=False):
    """Monitor qBittorrent download progress with real-time updates"""
    # Get qBittorrent configuration
    qbt_config = get_qbittorrent_config()
    host = qbt_config["host"]
    primary_port = qbt_config["port"]
    username = qbt_config["username"]
    password = qbt_config["password"]
    
    # Try primary port first, then fallback ports
    ports_to_try = [primary_port, 8082, 50583, 8080, 8081]
    # Remove duplicates while preserving order
    ports_to_try = list(dict.fromkeys(ports_to_try))
    
    last_line_length = 0
    
    for attempt in range(60):  # Try for 2 minutes
        for port in ports_to_try:
            try:
                session = requests.Session()
                login_data = {'username': username, 'password': password}
                login_response = session.post(f"http://{host}:{port}/api/v2/auth/login", data=login_data, timeout=3)
                
                if login_response.status_code == 200:
                    torrents_response = session.get(f"http://localhost:{port}/api/v2/torrents/info", timeout=3)
                    if torrents_response.status_code == 200:
                        torrents = torrents_response.json()
                        
                        # Find our torrent
                        for torrent in torrents:
                            if torrent_hash.lower() in torrent.get('hash', '').lower():
                                name = torrent.get('name', 'Unknown Movie')
                                progress = torrent.get('progress', 0)
                                state = torrent.get('state', 'unknown')
                                eta = torrent.get('eta', 0)
                                dlspeed = torrent.get('dlspeed', 0)
                                
                                # Show movie name once
                                if not movie_name_shown:
                                    print(f"🎬 {name}")
                                    movie_name_shown = True
                                
                                # Clear previous line
                                if last_line_length > 0:
                                    print('\r' + ' ' * last_line_length + '\r', end='')
                                
                                if state == 'downloading':
                                    progress_percent = int(progress * 100)
                                    bar_length = 40
                                    filled_length = int(bar_length * progress)
                                    bar = '█' * filled_length + '░' * (bar_length - filled_length)
                                    
                                    # Format ETA
                                    if eta > 0:
                                        hours = eta // 3600
                                        minutes = (eta % 3600) // 60
                                        seconds = eta % 60
                                        if hours > 0:
                                            eta_str = f"{hours}h {minutes}m"
                                        elif minutes > 0:
                                            eta_str = f"{minutes}m {seconds}s"
                                        else:
                                            eta_str = f"{seconds}s"
                                    else:
                                        eta_str = "Unknown"
                                    
                                    # Format speed
                                    if dlspeed > 1024*1024:
                                        speed_str = f"{dlspeed/(1024*1024):.1f} MB/s"
                                    elif dlspeed > 1024:
                                        speed_str = f"{dlspeed/1024:.1f} KB/s"
                                    else:
                                        speed_str = f"{dlspeed} B/s"
                                    
                                    # Print progress on new line (clean and readable)
                                    print(f"📊 [{bar}] {progress_percent}% | {speed_str} | ETA: {eta_str}")
                                    
                                    if progress >= 1.0:
                                        print("\n✅ Download completed!")
                                        return True
                                    
                                elif state == 'uploading':
                                    print("\n✅ Download completed! (Now seeding)")
                                    return True
                                elif state == 'queuedDL':
                                    print("⏳ Queued for download...")
                                elif state == 'stalledDL':
                                    print("🔍 Finding peers...")
                                elif state == 'pausedDL':
                                    print("⏸️  Download paused")
                                elif state == 'checkingResumeData':
                                    print("🔄 Checking files...")
                                elif state == 'stalledUP':
                                    print("✅ Download completed! (Seeding stalled)")
                                    return True
                                else:
                                    print(f"📊 Status: {state}")
                                
                                await asyncio.sleep(3)
                                return await monitor_qbittorrent_download(torrent_hash, True)
                        
                        break
            except:
                continue
        
        await asyncio.sleep(2)
    
    print("\n⚠️  Could not find download in qBittorrent")
    return False

async def add_torrent_to_qbittorrent_clean(magnet_link, torrent_hash):
    """Add torrent to qBittorrent via Web API with clean UI"""
    try:
        # Find qBittorrent Web API port
        ports_to_try = [50583, 8080, 8081]
        qbt_url = None
        
        for port in ports_to_try:
            try:
                test_url = f"http://localhost:{port}"
                test_response = requests.get(f"{test_url}/api/v2/app/version", timeout=3)
                if test_response.status_code == 200:
                    qbt_url = test_url
                    break
            except:
                continue
        
        if not qbt_url:
            return False
        
        # Login to qBittorrent Web API
        login_data = {'username': 'admin', 'password': '111111'}
        session = requests.Session()
        login_response = session.post(f"{qbt_url}/api/v2/auth/login", data=login_data, timeout=5)
        
        if login_response.status_code != 200:
            return False
        
        # Add magnet link
        add_data = {
            'urls': magnet_link,
            'autoTMM': 'false',
            'savepath': get_download_dir()
        }
        
        add_response = session.post(f"{qbt_url}/api/v2/torrents/add", data=add_data, timeout=5)
        
        if add_response.status_code == 200:
            print("✅ Added to qBittorrent")
            # Monitor download progress
            await monitor_qbittorrent_download(torrent_hash)
            return True
        else:
            return False
            
    except:
        return False

async def grabTorrent(page):
    ## Grab all torrent links with quality
    all = []
    qualities = ['BluRay', 'WEB']
    for quality in qualities:
        possible = await page.Jx(f"//a[contains(., '{quality}')]")
        for element in possible:
            if await page.evaluate("(element) => $(element).is(':visible')", element) == True:
                all.append(element)
    
    quality = {}
    for button in all:
        text = await page.evaluate('(element) => element.textContent', button)
        link = await page.evaluate('(element) => element.getAttribute("href")', button)
        rel = await page.evaluate('(element) => element.getAttribute("rel")', button)
        if any(typeOfMovie in text for typeOfMovie in qualities) and rel == "nofollow":
            quality[link] = button

    ## Make a map for all buttons
    buttons = {}
    print("\n" + "="*50)
    print("Available Qualities:")
    print("="*50)
    for i, link in enumerate(quality):
        button = quality[link]
        QualityAsText = await page.evaluate('(element) => element.textContent', button)
        print(f"  {i}: {QualityAsText}")
        buttons[i] = button
    print("="*50)
    
    ## Grab user input to get what quality they want
    answer = int(input("Choose quality [0-{}]: ".format(len(quality)-1)))
    while answer not in list(range(len(quality))):
        answer = int(input("Invalid choice. Please select 0-{}: ".format(len(quality)-1)))

    # Get the torrent download link and extract hash
    torrent_link = await page.evaluate('(element) => element.getAttribute("href")', buttons[answer])
    torrent_hash = torrent_link.split('/')[-1]
    
    # Create magnet link
    magnet_link = f"magnet:?xt=urn:btih:{torrent_hash}&dn=YTS+Movie&tr=udp://open.demonii.com:1337/announce&tr=udp://tracker.openbittorrent.com:80&tr=udp://tracker.coppersurfer.tk:6969&tr=udp://glotorrents.pw:6969/announce&tr=udp://tracker.opentrackr.org:1337/announce&tr=udp://torrent.gresille.org:80/announce&tr=udp://p4p.arenabg.com:1337&tr=udp://tracker.leechers-paradise.org:6969"
    
    print("\nProcessing download...")
    
    # Try to add magnet link via qBittorrent Web API
    success = await add_torrent_to_qbittorrent_clean(magnet_link, torrent_hash)
    
    if not success:
        # Try watch folder automation
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
            }
            
            torrent_download_url = f"https://yts.mx/torrent/download/{torrent_hash}"
            response = requests.get(torrent_download_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save to watch folder
            watch_folder = os.path.expanduser("~/TorrentWatch")
            movie_title = await page.evaluate('document.title')
            safe_title = "".join(c for c in movie_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            torrent_filename = f"{safe_title}_{torrent_hash[:8]}.torrent"
            torrent_path = os.path.join(watch_folder, torrent_filename)
            
            with open(torrent_path, 'wb') as f:
                f.write(response.content)
            
            print("✅ Torrent added to download queue")
            
            # Wait for watch folder processing and monitor download
            success = await wait_for_watch_folder_processing(torrent_filename, torrent_hash)
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print(f"📋 Magnet link: {magnet_link}")
    
    return magnet_link


async def main(movie_title, headless=False):
    # Browser launch arguments for better compatibility
    launch_args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu"
    ]
    
    if not headless:
        launch_args.append("--window-position=0,0")
    
    try:
        browser = await launch(
            headless=headless,
            args=launch_args,
            executablePath=None,  # Let pyppeteer find the browser
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False
        )
        page = await browser.newPage()
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36')
        await page.goto(f'https://yts.mx/browse-movies/{movie_title}')
        await asyncio.sleep(1)  # Fixed: use await with asyncio.sleep
        movies = await page.querySelectorAll(".browse-movie-title")
        options = {}

        if len(movies) == 0:
            print(f"No movies found for '{movie_title}'")
            await browser.close()
            return
        elif len(movies) == 1:
            movie_link = await page.evaluate('(element) => element.getAttribute("href")', movies[0])
            await page.goto(f'{movie_link}')
            await grabTorrent(page)
        else:
            print("\n" + "="*60)
            print("Search Results:")
            print("="*60)
            for i in range(len(movies)):
                url = await page.evaluate('(element) => element.getAttribute("href")', movies[i])
                title = await page.evaluate('(element) => element.textContent', movies[i])
                year = url.split('-')[-1]
                options[i] = url
                print(f"  {i}: {title} ({year})")
            print("="*60)
            
            answer = int(input("Choose movie [0-{}]: ".format(len(movies)-1)))
            while answer not in list(range(len(movies))):
                answer = int(input("Invalid choice. Please select 0-{}: ".format(len(movies)-1)))
            
            await page.goto(options[answer])
            await grabTorrent(page)
        
        await browser.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

def load_config():
    """Load configuration from file or create default config"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Return default config
    return {"download_dir": DEFAULT_DOWNLOAD_DIR}

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        print(f"Warning: Could not save config to {CONFIG_FILE}")
        return False

def get_download_dir():
    """Get download directory from config or prompt user to set it"""
    config = load_config()
    download_dir = config.get("download_dir", DEFAULT_DOWNLOAD_DIR)
    
    # Check if directory exists
    if not os.path.exists(download_dir):
        print(f"Download directory '{download_dir}' does not exist.")
        download_dir = input(f"Enter download directory (default: {DEFAULT_DOWNLOAD_DIR}): ").strip()
        if not download_dir:
            download_dir = DEFAULT_DOWNLOAD_DIR
        
        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        # Save new directory to config
        config["download_dir"] = download_dir
        save_config(config)
        print(f"Download directory set to: {download_dir}")
    
    return download_dir

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='YTSDownloader - Download torrents from yts.mx',
        epilog='Example: TorrentGrabber "Inception" "The Matrix"'
    )
    parser.add_argument(
        'movies',
        nargs='*',
        help='Name(s) of movie(s) to search for'
    )
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Run browser with GUI (default is headless mode)'
    )
    parser.add_argument(
        '--set-download-dir',
        metavar='PATH',
        help='Set the download directory and save it to config'
    )
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show current configuration'
    )
    parser.add_argument(
        '--set-qbt-host',
        metavar='HOST',
        help='Set qBittorrent Web UI host (default: localhost)'
    )
    parser.add_argument(
        '--set-qbt-port',
        metavar='PORT',
        type=int,
        help='Set qBittorrent Web UI port (default: 8082)'
    )
    parser.add_argument(
        '--set-qbt-username',
        metavar='USERNAME',
        help='Set qBittorrent Web UI username (default: admin)'
    )
    parser.add_argument(
        '--set-qbt-password',
        metavar='PASSWORD',
        help='Set qBittorrent Web UI password'
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    # Handle qBittorrent configuration commands
    if args.set_qbt_host or args.set_qbt_port or args.set_qbt_username or args.set_qbt_password:
        config = load_config()
        qbt_config = config.get("qbittorrent", DEFAULT_QBITTORRENT_CONFIG.copy())
        
        if args.set_qbt_host:
            qbt_config["host"] = args.set_qbt_host
            print(f"qBittorrent host set to: {args.set_qbt_host}")
        
        if args.set_qbt_port:
            qbt_config["port"] = args.set_qbt_port
            print(f"qBittorrent port set to: {args.set_qbt_port}")
        
        if args.set_qbt_username:
            qbt_config["username"] = args.set_qbt_username
            print(f"qBittorrent username set to: {args.set_qbt_username}")
        
        if args.set_qbt_password:
            qbt_config["password"] = args.set_qbt_password
            print("qBittorrent password updated")
        
        config["qbittorrent"] = qbt_config
        if save_config(config):
            print("qBittorrent configuration saved")
        else:
            print("Failed to save qBittorrent configuration")
        sys.exit(0)
    
    # Handle configuration commands
    if args.set_download_dir:
        config = load_config()
        download_dir = os.path.expanduser(args.set_download_dir)
        os.makedirs(download_dir, exist_ok=True)
        config["download_dir"] = download_dir
        if save_config(config):
            print(f"Download directory set to: {download_dir}")
        else:
            print("Failed to save configuration")
        sys.exit(0)
    
    if args.show_config:
        config = load_config()
        qbt_config = config.get("qbittorrent", DEFAULT_QBITTORRENT_CONFIG)
        print("Current configuration:")
        print(f"  Download directory: {config.get('download_dir', DEFAULT_DOWNLOAD_DIR)}")
        print(f"  qBittorrent host: {qbt_config.get('host', 'localhost')}")
        print(f"  qBittorrent port: {qbt_config.get('port', 8082)}")
        print(f"  qBittorrent username: {qbt_config.get('username', 'admin')}")
        print(f"  Config file: {CONFIG_FILE}")
        sys.exit(0)
    
    # Require movies if not showing config or setting download dir
    if not args.movies:
        print("Error: No movies specified. Use -h for help.")
        sys.exit(1)
    
    # Fixed deprecation warning by using asyncio.run() instead of get_event_loop()
    for movie in args.movies:
        try:
            # Default to headless mode unless --gui is specified
            headless_mode = not args.gui
            asyncio.run(main(movie, headless=headless_mode))
        except Exception as e:
            print(f"Error processing movie '{movie}': {e}")
            continue

    
