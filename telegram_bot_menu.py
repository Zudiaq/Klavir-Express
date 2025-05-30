import yaml
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Load admin chat ID from GitHub secret
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# File to store user data
USER_DATA_FILE = "user_data.yaml"

# Start command handler
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_data = {
        "chat_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }

    # Save user data to YAML file
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "w") as file:
            yaml.dump([], file)

    with open(USER_DATA_FILE, "r") as file:
        data = yaml.safe_load(file) or []

    data.append(user_data)

    with open(USER_DATA_FILE, "w") as file:
        yaml.dump(data, file)

    # Notify admin silently
    context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"New user started the bot:\n{yaml.dump(user_data)}",
    )

# Admin menu handler
def admin_menu(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    keyboard = [
        [InlineKeyboardButton("Send Message to Users", callback_data="send_message")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Admin Menu:", reply_markup=reply_markup)

# Callback query handler
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "send_message":
        with open(USER_DATA_FILE, "r") as file:
            users = yaml.safe_load(file) or []

        for user in users:
            try:
                context.bot.send_message(chat_id=user["chat_id"], text="Hello!")
            except Exception as e:
                print(f"Failed to send message to {user['chat_id']}: {e}")

# Main function
def main():
    updater = Updater(token=os.getenv("BOT_TOKEN"))
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("admin", admin_menu))
    dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
