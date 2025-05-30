import yaml
import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import time

# Load admin chat ID and GitHub token from secrets
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
GH_PAT = os.getenv("GH_PAT")

# GitHub repo and file details
REPO_URL = "https://github.com/Zudiaq/panel_user_data.git"
USER_DATA_FILE = "panel_user_data.yaml"

# Clone or pull the latest repo
def sync_repo():
    if not os.path.exists("repo"):
        subprocess.run(["git", "clone", f"https://{GH_PAT}@{REPO_URL}", "repo"], check=True)
    else:
        subprocess.run(["git", "-C", "repo", "pull"], check=True)

# Push changes to the repo
def push_changes():
    subprocess.run(["git", "-C", "repo", "add", USER_DATA_FILE], check=True)
    subprocess.run(["git", "-C", "repo", "commit", "-m", "Update user data"], check=True)
    subprocess.run(["git", "-C", "repo", "push"], check=True)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = {
        "chat_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    # Sync repo and load user data
    sync_repo()
    file_path = os.path.join("repo", USER_DATA_FILE)
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            yaml.dump([], file)

    with open(file_path, "r") as file:
        data = yaml.safe_load(file) or []

    data.append(user_data)

    with open(file_path, "w") as file:
        yaml.dump(data, file)

    # Push updated data to repo
    push_changes()

    # Notify admin silently
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"New user started the bot:\n{yaml.dump(user_data)}",
    )

# Admin menu handler
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    keyboard = [
        [InlineKeyboardButton("Send Message to Users", callback_data="send_message")],
        [InlineKeyboardButton("Refresh User Data", callback_data="refresh_data")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Admin Menu:", reply_markup=reply_markup)

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "send_message":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        for user in users:
            try:
                await context.bot.send_message(chat_id=user["chat_id"], text="Hello!")
            except Exception as e:
                print(f"Failed to send message to {user['chat_id']}: {e}")

    elif query.data == "refresh_data":
        sync_repo()
        await query.edit_message_text("User data refreshed successfully!")

# Main function
def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

    # Keep the bot running for 6 hours
    time.sleep(6 * 60 * 60)
    application.stop()

if __name__ == "__main__":
    main()
