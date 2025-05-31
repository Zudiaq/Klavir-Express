import os
import time
import requests
from telegram import Bot

def trigger_panel_workflow():
    """
    Triggers the 'panel.yml' workflow on GitHub.
    """
    github_token = os.getenv("GH_PAT")  # GitHub Personal Access Token
    repo = "Zudiaq/Klavir-Express"  # Repository name 
    workflow = "panel.yml"  # Workflow file name

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {"Authorization": f"Bearer {github_token}"}
    data = {"ref": "main"}  # Branch to trigger the workflow on

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        print("Successfully triggered the 'panel.yml' workflow.")
        return True
    else:
        print(f"Failed to trigger the workflow: {response.status_code}, {response.text}")
        return False

def send_telegram_alert():
    """
    Sends an alert to the admin(s) via Telegram in case of failure.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_chat_ids = os.getenv("ADMIN_CHAT_ID", "").split(",")  # Support multiple admin IDs
    bot = Bot(token=bot_token)

    message = "⚠️ Failed to trigger the 'panel.yml' workflow. Please check the system."
    for chat_id in admin_chat_ids:
        try:
            bot.send_message(chat_id=chat_id.strip(), text=message)
        except Exception as e:
            print(f"Failed to send alert to admin {chat_id}: {e}")

if __name__ == "__main__":
    time.sleep(60)  # Wait for 1 minute before triggering
    if not trigger_panel_workflow():
        send_telegram_alert()
    print("Restart script finished.")
