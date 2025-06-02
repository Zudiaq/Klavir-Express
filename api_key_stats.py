import os
import logging
import yaml
import requests
from dotenv import load_dotenv

load_dotenv()

YAML_KEYS_FILE = "youtube-mp3-api-stats.yaml"
GH_PAT = os.getenv("GH_PAT")
GITHUB_REPO = "Zudiaq/youtube-mp3-apis"  # Repository containing API keys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def pull_yaml_keys():
    """
    Pull the YAML file containing API keys from the private GitHub repository.
    Returns the content of the file as a Python dictionary.
    """
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{YAML_KEYS_FILE}"
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        with open(YAML_KEYS_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        # Load and return the YAML content
        with open(YAML_KEYS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to pull YAML keys file: {e}")
        return None

def format_api_key_stats(yaml_data):
    """
    Format the API key statistics into a clean, readable message.
    
    Args:
        yaml_data (dict): The YAML data containing API key information
        
    Returns:
        str: Formatted message with API key statistics
    """
    if not yaml_data:
        return "❌ Failed to retrieve API key statistics."
    
    message = "🔑 <b>API Key Usage Statistics</b>\n\n"
    
    # Process each service in the YAML file
    for service_name, keys in yaml_data.items():
        if not isinstance(keys, list):
            continue
            
        message += f"<b>Service:</b> {service_name}\n"
        
        # Sort keys by their index/number if available
        sorted_keys = sorted(keys, key=lambda k: k.get("index", 0) if isinstance(k.get("index"), int) else 0)
        
        for i, key_info in enumerate(sorted_keys, 1):
            # Mask the API key for security (show only first 4 and last 4 characters)
            key = key_info.get("key", "")
            masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "[Hidden]"
            
            usage = key_info.get("usage", 0)
            reset_day = key_info.get("reset_day", "N/A")
            last_reset = key_info.get("last_reset", "Never")
            
            # Add emoji indicators for usage status
            status_emoji = "🟢" if usage < 250 else "🟡" if usage < 300 else "🔴"
            
            message += f"{status_emoji} <b>Key {i}:</b> {masked_key}\n"
            message += f"   Usage: {usage}/300\n"
            message += f"   Reset Day: {reset_day}\n"
            message += f"   Last Reset: {last_reset}\n\n"
    
    return message

def get_api_key_stats():
    """
    Get formatted API key statistics.
    
    Returns:
        str: Formatted message with API key statistics
    """
    yaml_data = pull_yaml_keys()
    return format_api_key_stats(yaml_data)
