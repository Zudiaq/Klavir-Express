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
    # Delete the /admin command message
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print(f"Failed to delete /admin command message: {e}")

    if str(update.effective_user.id) not in ADMIN_CHAT_IDS:
        error_message = await update.message.reply_text("Sorry, you are not an admin and cannot access this bot's panel.")
        # Delete the error message after 5 seconds
        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=error_message.chat_id, message_id=error_message.message_id)
        except Exception as e:
            print(f"Failed to delete error message: {e}")
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

# Helper function to send a temporary message
async def send_temporary_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = 5):
    """Send a message and delete it after a delay."""
    message = await context.bot.send_message(chat_id=chat_id, text=text)
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    except Exception as e:
        print(f"Failed to delete message: {e}")

# Callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "view_users":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        if users:
            user_list = "\n".join(
                [f"👤 <b>{user['first_name']} {user.get('last_name', '')}</b>\n"
                 f"🔗 Username: @{user['username'] or 'N/A'}\n"
                 f"🆔 Chat ID: <code>{user['chat_id']}</code>\n" for user in users]
            )
        else:
            user_list = "No users found."

        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"👥 <b>User List:</b>\n\n{user_list}", reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("👥 View User List", callback_data="view_users")],
            [InlineKeyboardButton("✉️ Send Message to Specific User", callback_data="send_message_user")],
            [InlineKeyboardButton("📢 Send Message to All Users", callback_data="send_message_all")],
            [InlineKeyboardButton("🔄 Refresh User Data", callback_data="refresh_data")],
            [InlineKeyboardButton("🗑️ Remove User from List", callback_data="remove_user")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Welcome to the Admin Panel! Please choose an option:", reply_markup=reply_markup)

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
        context.user_data["awaiting_message"] = True
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        prompt_message = await query.edit_message_text(
            f"Please type the message or send the media you want to send to user with Chat ID {chat_id}:",
            reply_markup=reply_markup
        )
        context.user_data["prompt_message_id"] = prompt_message.message_id  # Store the prompt message ID

    elif query.data == "send_message_all":
        context.user_data["awaiting_broadcast_message"] = True
        keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        prompt_message = await query.edit_message_text("Please type the message or send the media you want to broadcast:", reply_markup=reply_markup)
        context.user_data["prompt_message_id"] = prompt_message.message_id  # Store the prompt message ID

    elif query.data == "refresh_data":
        sync_repo()
        await send_temporary_message(context, update.effective_chat.id, "🔄 User data refreshed successfully!")

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
        await send_temporary_message(context, update.effective_chat.id, f"User with Chat ID {chat_id} has been removed from the list.")

    elif query.data == "cancel":
        # Cancel the operation
        cancel_message = await query.edit_message_text("❌ Operation cancelled.")  # Update the message to indicate cancellation
        context.user_data.clear()  # Clear any stored data related to ongoing operations

        # Delete the cancel message after 5 seconds
        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=cancel_message.chat_id, message_id=cancel_message.message_id)
        except Exception as e:
            print(f"Failed to delete cancel message: {e}")

# Helper function to send media or text
async def send_media_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        if update.message.photo:
            # Handle photo messages
            photo = update.message.photo[-1]  # Get the highest resolution photo
            await context.bot.send_photo(chat_id=chat_id, photo=photo.file_id, caption=update.message.caption or "")
        elif update.message.video:
            # Handle video messages with 50 MB limit
            video = update.message.video
            if video.file_size > 50 * 1024 * 1024:
                await update.message.reply_text("The video file size exceeds the 50 MB limit. Please send a smaller file.")
                return
            await context.bot.send_video(chat_id=chat_id, video=video.file_id, caption=update.message.caption or "")
        elif update.message.audio:
            # Handle audio messages with 50 MB limit
            audio = update.message.audio
            if audio.file_size > 50 * 1024 * 1024:
                await update.message.reply_text("The audio file size exceeds the 50 MB limit. Please send a smaller file.")
                return
            await context.bot.send_audio(chat_id=chat_id, audio=audio.file_id, caption=update.message.caption or "")
        elif update.message.voice:
            # Handle voice messages
            voice = update.message.voice
            await context.bot.send_voice(chat_id=chat_id, voice=voice.file_id, caption=update.message.caption or "")
        elif update.message.document:
            # Handle document messages
            document = update.message.document
            await context.bot.send_document(chat_id=chat_id, document=document.file_id, caption=update.message.caption or "")
        elif update.message.animation:
            # Handle animation (GIF) messages
            animation = update.message.animation
            await context.bot.send_animation(chat_id=chat_id, animation=animation.file_id, caption=update.message.caption or "")
        elif update.message.sticker:
            # Handle sticker messages
            sticker = update.message.sticker
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker.file_id)
        elif update.message.video_note:
            # Handle video note messages
            video_note = update.message.video_note
            await context.bot.send_video_note(chat_id=chat_id, video_note=video_note.file_id)
        elif update.message.location:
            # Handle location messages
            location = update.message.location
            await context.bot.send_location(chat_id=chat_id, latitude=location.latitude, longitude=location.longitude)
        elif update.message.text:
            # Handle text messages
            await context.bot.send_message(chat_id=chat_id, text=update.message.text)
        else:
            await update.message.reply_text("Unsupported message type.")
    except Exception as e:
        print(f"Error while sending media or text: {e}")
        await update.message.reply_text(f"Failed to send message: {e}")

# Message handler for forwarding user messages to admins
async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the sender is an admin
    if str(update.effective_user.id) in ADMIN_CHAT_IDS:
        return  # Do not forward messages from admins to themselves

    user = update.effective_user

    try:
        # Prepare user information
        user_info = f"""
📩 New Message from User:
👤 Name: {user.first_name} {user.last_name or ""}
🔗 Username: @{user.username or "N/A"}
🆔 Chat ID: {user.id}
        """

        # Send user information to admins
        for admin_id in ADMIN_CHAT_IDS:
            await context.bot.send_message(chat_id=admin_id, text=user_info)

        # Forward media or text to admins
        if update.message.photo or update.message.animation or update.message.document or update.message.video or update.message.audio or update.message.voice or update.message.sticker or update.message.video_note or update.message.location:
            for admin_id in ADMIN_CHAT_IDS:
                await send_media_or_text(update, context, admin_id)
        elif update.message.text:
            # Forward text messages to admins
            for admin_id in ADMIN_CHAT_IDS:
                await context.bot.send_message(chat_id=admin_id, text=update.message.text)
        else:
            await update.message.reply_text("Unsupported message type.")
    except Exception as e:
        print(f"Failed to forward message to admins: {e}")

# Message handler for sending a message to a specific user or broadcasting
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_message"):
        target_chat_id = context.user_data.get("target_chat_id")
        if target_chat_id:
            # Delete the prompt message immediately
            prompt_message_id = context.user_data.get("prompt_message_id")
            if prompt_message_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_message_id)
                except Exception as e:
                    print(f"Failed to delete prompt message: {e}")
                context.user_data.pop("prompt_message_id", None)  # Remove the stored prompt message ID

            # Send the media or message
            await send_media_or_text(update, context, target_chat_id)
            # Send success message
            await update.message.reply_text("✅ Message or media sent successfully!")  # Success message
        else:
            await send_temporary_message(context, update.effective_chat.id, "❌ No target user selected.")
        context.user_data["awaiting_message"] = False

    elif context.user_data.get("awaiting_broadcast_message"):
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []

        for user in users:
            # Skip sending messages to admins
            if str(user["chat_id"]) in ADMIN_CHAT_IDS:
                continue
            try:
                await send_media_or_text(update, context, user["chat_id"])
            except Exception as e:
                print(f"Failed to send message to {user['chat_id']}: {e}")

        # Send success message
        await update.message.reply_text("📢 Message sent to all users.")
        
        # Delete the prompt message immediately
        prompt_message_id = context.user_data.get("prompt_message_id")
        if prompt_message_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_message_id)
            except Exception as e:
                print(f"Failed to delete prompt message: {e}")
            context.user_data.pop("prompt_message_id", None)  # Remove the stored prompt message ID
        context.user_data["awaiting_broadcast_message"] = False

    else:
        # If not awaiting a message, forward it to admins
        await forward_user_message(update, context)

# Main function
async def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.ALL, handle_message))  # Updated to handle all message types

    # Run the bot
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
