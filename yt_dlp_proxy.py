import os
import re
import json
import random
import logging
import requests
import subprocess
import importlib
import inspect
import time
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Constants
SPEEDTEST_URL = "http://212.183.159.230/5MB.zip"
PROXY_FILE = os.path.join(os.path.dirname(__file__), "proxy.json")

def is_valid_proxy(proxy):
    """Check if the proxy is valid."""
    return proxy.get("host") is not None and proxy.get("country") != "Russia" and proxy.get("country") != "RU"


def construct_proxy_string(proxy):
    """Construct a proxy string from the proxy dictionary."""
    if proxy.get("username"):
        return f'{proxy["username"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}'
    return f'{proxy["host"]}:{proxy["port"]}'


def test_proxy(proxy):
    """Test the proxy by measuring the download time and reliability."""
    proxy_str = construct_proxy_string(proxy)
    start_time = time.perf_counter()
    try:
        # First test: Basic connectivity with shorter timeout
        requests.get(
            "http://www.google.com",
            proxies={"http": f"http://{proxy_str}"},
            timeout=3,
        ).raise_for_status()
        
        # Second test: Download speed test with stricter timeout
        response = requests.get(
            SPEEDTEST_URL,
            stream=True,
            proxies={"http": f"http://{proxy_str}"},
            timeout=4,  # Reduced timeout for faster testing
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses

        total_length = response.headers.get("content-length")
        if total_length is None or int(total_length) != 5242880:
            return None

        with io.BytesIO() as f:
            download_time, downloaded_bytes = download_with_progress(
                response, f, total_length, start_time
            )
            
            # More stringent speed requirements
            if download_time == float("inf") or download_time > 4.0:
                return None
                
            # Calculate speed in KB/s
            speed = downloaded_bytes / download_time / 1024
            if speed < 100:  # Require at least 100 KB/s
                return None
                
            return {"time": download_time, "speed": speed, **proxy}  # Include speed and original proxy info
    except requests.RequestException:
        return None


def download_with_progress(response, f, total_length, start_time):
    """Download content from the response with progress tracking."""
    downloaded_bytes = 0
    chunk_count = 0
    last_speed_check = start_time
    speeds = []
    
    for chunk in response.iter_content(1024):
        downloaded_bytes += len(chunk)
        f.write(chunk)
        chunk_count += 1
        
        # Calculate progress percentage (out of 30)
        done = int(30 * downloaded_bytes / int(total_length))
        
        # Check speed consistency every 5 chunks
        current_time = time.perf_counter()
        if chunk_count % 5 == 0:
            chunk_speed = 5 * 1024 / (current_time - last_speed_check) / 1024  # KB/s
            speeds.append(chunk_speed)
            last_speed_check = current_time
            
            # If we have at least 3 speed measurements, check for consistency
            if len(speeds) >= 3:
                avg_speed = sum(speeds) / len(speeds)
                # If any speed measurement is less than 50% of average, proxy is unstable
                if any(s < avg_speed * 0.5 for s in speeds):
                    return float("inf"), downloaded_bytes
        
        # Break early after downloading enough to evaluate speed
        if done >= 8:  # Increased from 6 to 8 for better evaluation
            break
            
        # Fail fast for very slow proxies
        if done > 3 and (downloaded_bytes // (time.perf_counter() - start_time) / 100000) < 1.5:  # Increased threshold
            return float("inf"), downloaded_bytes
            
    return round(time.perf_counter() - start_time, 2), downloaded_bytes


def save_proxies_to_file(proxies, filename=PROXY_FILE):
    """Save the best proxies to a JSON file."""
    with open(filename, "w") as f:
        json.dump(proxies, f, indent=4)


def get_best_proxies(providers):
    """Return the top five proxies based on speed from all providers."""
    all_proxies = []
    proxies = None
    for provider in providers:
        try:
            logging.info(f"Fetching proxies from {provider.__class__.__name__}")
            proxies = provider.fetch_proxies()
            all_proxies.extend([proxy for proxy in proxies if is_valid_proxy(proxy)])
        except Exception as e:
            logging.error(f"Failed to fetch proxies from {provider.__class__.__name__}: {e}")

    best_proxies = []
    with ThreadPoolExecutor(max_workers=8) as executor:  # Increased from 2 to 8 for faster testing
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in all_proxies}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Testing proxies", 
                          bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_noinv_fmt}]", 
                          unit=' proxies', unit_scale=True, ncols=80):
            result = future.result()
            if result is not None:
                best_proxies.append(result)
    
    # Sort by speed first, then by time
    if best_proxies:
        return sorted(best_proxies, key=lambda x: (x.get("time", float("inf"))))[:(min(5, len(best_proxies)))]
    return []


def update_proxies():
    """Update the proxies list and save the best ones."""
    try:
        # Import proxy providers dynamically
        from proxy_providers import ProxyProvider
        providers = []
        proxy_providers_dir = os.path.join(os.path.dirname(__file__), "yt_dlp_proxy", "proxy_providers")
        
        if not os.path.exists(proxy_providers_dir):
            logging.error(f"Proxy providers directory not found: {proxy_providers_dir}")
            return False
            
        for filename in os.listdir(proxy_providers_dir):
            # Check if the file is a Python module
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]  # Remove the '.py' suffix
                module_path = f'yt_dlp_proxy.proxy_providers.{module_name}'
                try:
                    module = importlib.import_module(module_path)
                    classes = inspect.getmembers(module, inspect.isclass)
                    provider_classes = [cls for name, cls in classes if name != "ProxyProvider" and issubclass(cls, ProxyProvider)]
                    if provider_classes:
                        providers.append(provider_classes[0]())
                        logging.info(f"Successfully loaded proxy provider: {provider_classes[0].__name__}")
                except Exception as e:
                    logging.error(f"Error loading proxy provider {module_name}: {e}")
        
        if not providers:
            logging.error("No proxy providers found")
            return False
            
        logging.info(f"Found {len(providers)} proxy providers")
        best_proxies = get_best_proxies(providers)
        if best_proxies:
            save_proxies_to_file(best_proxies)
            logging.info(f"Proxy list updated successfully with {len(best_proxies)} proxies")
            return True
        else:
            logging.error("No valid proxies found")
            return False
    except Exception as e:
        logging.error(f"Failed to update proxies: {e}")
        return False


def get_proxy():
    """Get a random proxy from the proxy file, update if needed."""
    try:
        if not os.path.exists(PROXY_FILE):
            logging.info("Proxy file not found, updating proxies...")
            if not update_proxies():
                return None
                
        with open(PROXY_FILE, "r") as f:
            proxies = json.load(f)
            if not proxies:
                logging.info("Proxy file is empty, updating proxies...")
                if not update_proxies():
                    return None
                with open(PROXY_FILE, "r") as f:
                    proxies = json.load(f)
            
            return random.choice(proxies)
    except Exception as e:
        logging.error(f"Error getting proxy: {e}")
        return None


def search_and_download_youtube_mp3(track_name, artist_name, album_name=None, duration_limit=600):
    """
    Search YouTube for the specified track and download as MP3 using a proxy.
    Args:
        track_name (str): Name of the track
        artist_name (str): Name of the artist
        album_name (str, optional): Name of the album
        duration_limit (int): Maximum allowed duration in seconds (default 10 minutes)
    Returns:
        str: Path to the downloaded MP3 file, or None if not found
    """
    from yt_dlp import YoutubeDL
    
    query = f"{track_name} {artist_name} official audio"
    if album_name:
        query += f" {album_name}"
    
    # Try up to 3 different proxies if needed
    for attempt in range(3):
        try:
            proxy = get_proxy()
            if not proxy:
                logging.error("Failed to get a valid proxy, updating proxies and trying again")
                # Try to update proxies instead of falling back to no proxy
                if update_proxies():
                    proxy = get_proxy()
                    if not proxy:
                        logging.error("Still failed to get a valid proxy after update")
                        return None
                else:
                    logging.error("Failed to update proxies")
                    return None
                
            proxy_str = construct_proxy_string(proxy)
            logging.info(f"Using proxy from {proxy.get('city', 'Unknown')}, {proxy.get('country', 'Unknown')}")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'default_search': 'ytsearch5',
                'outtmpl': '%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'extract_flat': False,
                'nocheckcertificate': True,
                'proxy': f'http://{proxy_str}',
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(query, download=False)['entries']
                for entry in search_results:
                    if entry is None:
                        continue
                    duration = entry.get('duration')
                    title = entry.get('title', '').lower()
                    if duration and duration > duration_limit:
                        continue
                    # Require both track and artist name in title, avoid live/concert/cover/remix/karaoke
                    if track_name.lower() in title and artist_name.lower() in title:
                        if re.search(r'(live|concert|cover|remix|karaoke)', title):
                            continue
                        info = ydl.extract_info(entry['webpage_url'], download=True)
                        filename = ydl.prepare_filename(info)
                        mp3_path = re.sub(r'\.[^.]+$', '.mp3', filename)
                        if os.path.exists(mp3_path):
                            return mp3_path
                # If no strict match, try the first short enough result
                for entry in search_results:
                    if entry is None:
                        continue
                    duration = entry.get('duration')
                    if duration and duration > duration_limit:
                        continue
                    info = ydl.extract_info(entry['webpage_url'], download=True)
                    filename = ydl.prepare_filename(info)
                    mp3_path = re.sub(r'\.[^.]+$', '.mp3', filename)
                    if os.path.exists(mp3_path):
                        return mp3_path
        except Exception as e:
            error_msg = str(e).lower()
            logging.error(f"YouTube download failed with proxy: {e}")
            
            # Check for proxy-related errors
            if "sign in to" in error_msg or "403" in error_msg or "forbidden" in error_msg or "proxy" in error_msg:
                logging.info(f"Proxy error detected, updating proxies and trying again (attempt {attempt+1}/3)")
                if attempt == 2:  # Last attempt, try updating proxies
                    update_proxies()
            else:
                # For non-proxy errors, still try with a different proxy
                logging.info(f"Non-proxy error detected, trying with a different proxy (attempt {attempt+1}/3)")
                if attempt == 2:  # Last attempt, try updating proxies
                    update_proxies()
    
    # If all proxy attempts failed, return None
    logging.info("All proxy attempts failed, could not download the track")
    return None


# Removed fallback_download function as we never want to download without a proxy
