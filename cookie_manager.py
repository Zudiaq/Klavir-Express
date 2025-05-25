import os
import base64
import logging
from yt_dlp import YoutubeDL

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def manage_cookies(cookies_secret_name, github_token, repo):
    """
    Manage YouTube cookies: decode, test, refresh, and update.
    """
    logging.info("Starting cookie management...")
    # Decode cookies
    cookies_path = '/home/runner/work/klavir-alpha/klavir-alpha/temp/spotdl_download/cookies.txt'
    with open(cookies_path, 'wb') as f:
        f.write(base64.b64decode(os.getenv(cookies_secret_name)))

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
        new_cookies_path = '/home/runner/work/klavir-alpha/klavir-alpha/temp/spotdl_download/new_cookies.txt'
        with YoutubeDL({'cookies_from_browser': 'chrome', 'cookiefile': new_cookies_path}) as ydl:
            ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)
        if os.path.exists(new_cookies_path) and os.path.getsize(new_cookies_path) > 0:
            logging.info("New cookies generated.")
            # Update secret
            with open(new_cookies_path, 'rb') as f:
                new_cookies_encoded = base64.b64encode(f.read()).decode()
            os.system(f"gh secret set {cookies_secret_name} --repo {repo} --body {new_cookies_encoded} --token {github_token}")
            logging.info("Cookies secret updated.")
        else:
            logging.error("Failed to generate new cookies.")

if __name__ == "__main__":
    manage_cookies("YOUTUBE_COOKIES", os.getenv("GH_PAT"), os.getenv("GITHUB_REPOSITORY"))
