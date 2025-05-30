import yaml
import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
import nest_asyncio

# Allow nested event loops
nest_asyncio.apply()

# Load admin chat IDs from secrets (support multiple admins)
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_ID", "").splitlines()
GH_PAT = os.getenv("GH_PAT")

# GitHub repo and file details
REPO_URL = "github.com/Zudiaq/panel_user_data.git"  # Fixed URL
USER_DATA_FILE = "panel_user_data.yaml"

# Clone or pull the latest repo
def sync_repo():
    if not os.path.exists("repo"):
        subprocess.run(["git", "clone", f"https://{GH_PAT}@{REPO_URL}", "repo"], check=True)
    else:
        subprocess.run(["git", "-C", "repo", "pull"], check=True)

# Push changes to the repo
def push_changes():
    # Set Git user configuration
    subprocess.run(["git", "-C", "repo", "config", "user.email", "you@example.com"], check=True)
    subprocess.run(["git", "-C", "repo", "config", "user.name", "Your Name"], check=True)

    # Add, commit, and push changes
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

    # Avoid duplicate entries
    if not any(user["chat_id"] == user_data["chat_id"] for user in data):
        data.append(user_data)

    with open(file_path, "w") as file:
        yaml.dump(data, file)

    # Push updated data to repo
    push_changes()

    # Send a creative welcome message to the user
    welcome_message = f"""
🎉 Welcome, {user.first_name}! 🎉

I'm thrilled to have you here. 🚀
Feel free to explore and interact with the bot. If you have any questions, just type them here, and I'll assist you ASAP!

✨ Have a great time! ✨
    """
    await update.message.reply_text(welcome_message)

    # Notify admin silently
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_IDS[0],  # Notify the first admin in the list
        text=f"New user started the bot:\n{yaml.dump(user_data)}",
    )

# Admin menu handler
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) not in ADMIN_CHAT_IDS:
        await update.message.reply_text("Sorry, you are not an admin and cannot access this bot's panel.")
        return

    keyboard = [
        [InlineKeyboardButton("👥 View User List", callback_data="view_users")],
        [InlineKeyboardButton("✉️ Send Message to Specific User", callback_data="send_message_user")],
        [InlineKeyboardButton("📢 Send Message to All Users", callback_data="send_message_all")],
        [InlineKeyboardButton("🔄 Refresh User Data", callback_data="refresh_data")],
        [InlineKeyboardButton("🗑️ Remove User from List", callback_data="remove_user")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to the Admin Panel! Please choose an option:", reply_markup=reply_markup)

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "view_users":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        user_list = "\n".join(
            [f"{user['first_name']} (@{user['username']}) - {user['chat_id']}" for user in users]
        )
        await query.edit_message_text(f"👥 User List:\n{user_list}")

    elif query.data == "send_message_user":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        keyboard = [
            [InlineKeyboardButton(f"{user['first_name']} (@{user['username']})", callback_data=f"send_to_{user['chat_id']}")]
            for user in users
        ]
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a user to send a message:", reply_markup=reply_markup)

    elif query.data.startswith("send_to_"):
        chat_id = int(query.data.split("_")[2])
        context.user_data["target_chat_id"] = chat_id
        await query.edit_message_text("Please type the message you want to send:")
        context.user_data["awaiting_message"] = True

    elif query.data == "send_message_all":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        for user in users:
            try:
                await context.bot.send_message(chat_id=user["chat_id"], text="Hello from Admin!")
            except Exception as e:
                print(f"Failed to send message to {user['chat_id']}: {e}")

        await query.edit_message_text("📢 Message sent to all users.")

    elif query.data == "refresh_data":
        sync_repo()
        await query.edit_message_text("🔄 User data refreshed successfully!")

    elif query.data == "remove_user":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        keyboard = [
            [InlineKeyboardButton(f"{user['first_name']} (@{user['username']})", callback_data=f"remove_{user['chat_id']}")]
            for user in users
        ]
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select a user to remove from the list:", reply_markup=reply_markup)

    elif query.data.startswith("remove_"):
        chat_id = int(query.data.split("_")[1])
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        updated_users = [user for user in users if user["chat_id"] != chat_id]

        with open(file_path, "w") as file:
            yaml.dump(updated_users, file)

        push_changes()
        await query.edit_message_text(f"User with Chat ID {chat_id} has been removed from the list.")

    elif query.data == "cancel":
        await query.edit_message_text("❌ Operation cancelled.")

# Message handler for sending a message to a specific user
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_message"):
        target_chat_id = context.user_data.get("target_chat_id")
        if target_chat_id:
            try:
                await context.bot.send_message(chat_id=target_chat_id, text=update.message.text)
                await update.message.reply_text("Message sent successfully!")
            except Exception as e:
                await update.message.reply_text(f"Failed to send message: {e}")
        else:
            await update.message.reply_text("No target user selected.")
        context.user_data["awaiting_message"] = False

# Message handler for forwarding user messages to admins
async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text

    user_info = f"""
📩 New Message from User:
👤 Name: {user.first_name} {user.last_name or ""}
🔗 Username: @{user.username or "N/A"}
🆔 Chat ID: {user.id}
💬 Message: {message_text}
    """

    for admin_id in ADMIN_CHAT_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=user_info)
        except Exception as e:
            print(f"Failed to send message to admin {admin_id}: {e}")

# Main function
async def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_user_message))  # Updated handler

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
