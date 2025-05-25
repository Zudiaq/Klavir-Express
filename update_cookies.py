import os
import base64
import logging
from yt_dlp import YoutubeDL

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def update_cookies(cookies_secret_name, github_token, repo):
    """
    Update YouTube cookies: decode, test, refresh, and update.
    """
    logging.info("Starting cookie update...")
    # Decode cookies
    cookies_path = os.path.join(os.getenv('USERPROFILE'), '.cache', 'yt-dlp', 'youtube', 'cookies.txt')
    with open(cookies_path, 'rb') as f:
        cookies_data = f.read()
    cookies_encoded = base64.b64encode(cookies_data).decode()

    # Test cookies
    try:
        ydl_opts = {
            'quiet': True,
            'cookiefile': cookies_path,
            'skip_download': True,
            'get_title': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)
        logging.info("Cookies are valid.")
    except Exception as e:
        logging.warning(f"Cookies expired: {e}")
        # Refresh cookies
        new_cookies_path = os.path.join(os.getenv('USERPROFILE'), '.cache', 'yt-dlp', 'youtube', 'new_cookies.txt')
        with YoutubeDL({'cookies_from_browser': 'chrome', 'cookiefile': new_cookies_path}) as ydl:
            ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)
        if os.path.exists(new_cookies_path) and os.path.getsize(new_cookies_path) > 0:
            logging.info("New cookies generated.")
            with open(new_cookies_path, 'rb') as f:
                new_cookies_encoded = base64.b64encode(f.read()).decode()
            cookies_encoded = new_cookies_encoded
        else:
            logging.error("Failed to generate new cookies.")

    # Update secret
    os.system(f"gh secret set {cookies_secret_name} --body {cookies_encoded} --token {github_token}")
    logging.info("Cookies secret updated.")

if __name__ == "__main__":
    update_cookies(os.getenv("YOUTUBE_COOKIES"), os.getenv("GH_PAT"), os.getenv("GITHUB_REPOSITORY", ""))
