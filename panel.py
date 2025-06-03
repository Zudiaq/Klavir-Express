import yaml
import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
import nest_asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import sys
import requests
from api_key_stats import get_api_key_stats  

# ==========================
# Configuration Variables
# ==========================
nest_asyncio.apply()

# Load admin chat IDs from secrets (support multiple admins)
ADMIN_CHAT_IDS = os.getenv("ADMIN_CHAT_ID", "").split(",")  # Split by comma for multiple admin IDs
GH_PAT = os.getenv("GH_PAT")  # GitHub Personal Access Token
REPO_URL = "github.com/Zudiaq/panel_user_data.git"  # GitHub repository URL
USER_DATA_FILE = "panel_user_data.yaml"  # User data file name
MESSAGE_LIMITS = {  # Message limits per user
    "text": 40,
    "photo": 10,
    "sticker": 10,
    "voice": 5,
    "video_note": 5,
    "audio": 10,
    "animation": 5,
}
LIMIT_DURATION_MINUTES = 30  # Duration of the limit in minutes

# Command rate limits (modifiable by the developer)
COMMAND_RATE_LIMITS = {
    "start": {"limit": 5, "reset_duration": timedelta(days=1)},  # 5 times per day
    "admin": {"limit": 5, "reset_duration": timedelta(days=1)},  # 5 times per day
    # Add other commands here with their limits
}

# ==========================
# Global Variables
# ==========================
user_message_counts = defaultdict(lambda: defaultdict(int))
user_limit_reset_times = defaultdict(lambda: defaultdict(lambda: datetime.now() + timedelta(minutes=LIMIT_DURATION_MINUTES)))
user_warning_messages = defaultdict(dict)  # Store warning messages per user and media type
user_command_counts = defaultdict(lambda: defaultdict(int))  # Track command usage per user
user_command_reset_times = defaultdict(lambda: defaultdict(lambda: datetime.now()))  # Reset times for commands
admin_last_message_ids = {}  # Track the last admin panel message ID per admin
cached_users = []  # Initialize cached_users
user_languages = defaultdict(lambda: "en")  # Default to English

# ==========================
# Helper Functions
# ==========================
def sync_repo():
    if not os.path.exists("repo"):
        subprocess.run(["git", "clone", f"https://{GH_PAT}@{REPO_URL}", "repo"], check=True)
    else:
        subprocess.run(["git", "-C", "repo", "pull"], check=True)

def push_changes():
    subprocess.run(["git", "-C", "repo", "config", "user.email", "you@example.com"], check=True)
    subprocess.run(["git", "-C", "repo", "config", "user.name", "Your Name"], check=True)
    subprocess.run(["git", "-C", "repo", "add", USER_DATA_FILE], check=True)
    subprocess.run(["git", "-C", "repo", "commit", "-m", "Update user data"], check=True)
    subprocess.run(["git", "-C", "repo", "push"], check=True)

def round_to_nearest_15_minutes(minutes: int) -> int:
    return ((minutes + 14) // 15) * 15

async def send_temporary_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = 5):
    message = await context.bot.send_message(chat_id=chat_id, text=text)
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    except Exception:
        pass

async def send_media_or_text(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    user_id = update.effective_user.id
    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=chat_id, photo=update.message.photo[-1].file_id, caption=update.message.caption or "")
        elif update.message.video:
            if update.message.video.file_size > 50 * 1024 * 1024:
                await update.message.reply_text(t(user_id, "unsupported_type"))
                return
            await context.bot.send_video(chat_id=chat_id, video=update.message.video.file_id, caption=update.message.caption or "")
        elif update.message.audio:
            if update.message.audio.file_size > 50 * 1024 * 1024:
                await update.message.reply_text(t(user_id, "unsupported_type"))
                return
            await context.bot.send_audio(chat_id=chat_id, audio=update.message.audio.file_id, caption=update.message.caption or "")
        elif update.message.voice:
            await context.bot.send_voice(chat_id=chat_id, voice=update.message.voice.file_id, caption=update.message.caption or "")
        elif update.message.document:
            await context.bot.send_document(chat_id=chat_id, document=update.message.document.file_id, caption=update.message.caption or "")
        elif update.message.animation:
            await context.bot.send_animation(chat_id=chat_id, animation=update.message.animation.file_id, caption=update.message.caption or "")
        elif update.message.sticker:
            await context.bot.send_sticker(chat_id=chat_id, sticker=update.message.sticker.file_id)
        elif update.message.video_note:
            await context.bot.send_video_note(chat_id=chat_id, video_note=update.message.video_note.file_id)
        elif update.message.location:
            await context.bot.send_location(chat_id=chat_id, latitude=update.message.location.latitude, longitude=update.message.location.longitude)
        elif update.message.text:
            await context.bot.send_message(chat_id=chat_id, text=update.message.text)
        else:
            await update.message.reply_text(t(user_id, "unsupported_type"))
    except Exception as e:
        await update.message.reply_text(f"Failed to send message: {e}")

def load_users_and_languages():
    global cached_users, user_languages
    try:
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                cached_users = yaml.safe_load(file) or []
            for user in cached_users:
                if "chat_id" in user and "language" in user:
                    user_languages[user["chat_id"]] = user["language"]
        print("Users and languages loaded successfully.")
    except Exception as e:
        print(f"Error loading users and languages: {e}")

def save_users_and_languages():
    global cached_users
    try:
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "w") as file:
            yaml.dump(cached_users, file)
        push_changes()
        print("Users and languages saved successfully.")
    except Exception as e:
        print(f"Error saving users and languages: {e}")

def get_user_language(user_id):
    return user_languages[user_id]

async def check_command_limit(user_id: int, command: str) -> bool:
    """
    Check if the user has exceeded the limit for a specific command.
    """
    now = datetime.now()

    # Get the command limit and reset duration
    command_limit = COMMAND_RATE_LIMITS.get(command, {"limit": 0, "reset_duration": timedelta(days=1)})
    limit = command_limit["limit"]
    reset_duration = command_limit["reset_duration"]

    # Reset command count if the reset time has passed
    if now >= user_command_reset_times[user_id][command]:
        user_command_counts[user_id][command] = 0
        user_command_reset_times[user_id][command] = now + reset_duration

    # Increment the command count
    user_command_counts[user_id][command] += 1

    # Check if the user has exceeded the limit
    if user_command_counts[user_id][command] > limit:
        return False  # Exceeded limit

    return True  # Within limit

# ==========================
# Core Functions
# ==========================
async def check_message_limit(update: Update, context: ContextTypes.DEFAULT_TYPE, message_type: str):
    user_id = update.effective_user.id
    now = datetime.now()

    # Reset message counts for the specific message type if the reset time has passed
    if now >= user_limit_reset_times[user_id][message_type]:
        user_message_counts[user_id][message_type] = 0
        user_limit_reset_times[user_id][message_type] = now + timedelta(minutes=LIMIT_DURATION_MINUTES)
        # Clear the warning message for this message type
        if message_type in user_warning_messages[user_id]:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=user_warning_messages[user_id][message_type])
            except Exception:
                pass
            del user_warning_messages[user_id][message_type]

    # Increment the message count for the specific message type
    user_message_counts[user_id][message_type] += 1

    # Check if the user has exceeded the limit for the given message type
    if user_message_counts[user_id][message_type] > MESSAGE_LIMITS.get(message_type, 0):
        # Apply the restriction for this message type
        user_limit_reset_times[user_id][message_type] = now + timedelta(minutes=LIMIT_DURATION_MINUTES)

        # Calculate remaining time and round to the nearest 15 minutes
        remaining_time = (user_limit_reset_times[user_id][message_type] - now).seconds // 60
        rounded_time = round_to_nearest_15_minutes(remaining_time)
        warning_text = t(user_id, "limit_warning", type=message_type, minutes=rounded_time)

        # Send or update the warning message for this message type
        if message_type in user_warning_messages[user_id]:
            try:
                await context.bot.edit_message_text(chat_id=user_id, message_id=user_warning_messages[user_id][message_type], text=warning_text)
            except Exception:
                pass
        else:
            warning_message = await update.message.reply_text(warning_text)
            user_warning_messages[user_id][message_type] = warning_message.message_id

        # Schedule deletion of the warning message after the limit duration
        asyncio.create_task(delete_warning_message(context, user_id, message_type, LIMIT_DURATION_MINUTES * 60))

        # Delete the user's message to enforce the limit
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        except Exception:
            pass
        return False

    return True

async def delete_warning_message(context: ContextTypes.DEFAULT_TYPE, user_id: int, message_type: str, delay: int):
    await asyncio.sleep(delay)
    if message_type in user_warning_messages[user_id]:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=user_warning_messages[user_id][message_type])
        except Exception:
            pass
        del user_warning_messages[user_id][message_type]

async def forward_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) in ADMIN_CHAT_IDS:
        return
    user = update.effective_user
    user_info = t(
        user_id, "user_info",
        name=f"{user.first_name} {user.last_name or ''}",
        username=user.username or "N/A",
        chat_id=user.id
    )
    for admin_id in ADMIN_CHAT_IDS:
        await context.bot.send_message(chat_id=admin_id, text=user_info)
        await send_media_or_text(update, context, admin_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Determine the type of message being sent
    if update.message.text:
        message_type = "text"
    elif update.message.photo:
        message_type = "photo"
    elif update.message.sticker:
        message_type = "sticker"
    elif update.message.voice:
        message_type = "voice"
    elif update.message.video_note:
        message_type = "video_note"
    elif update.message.audio:
        message_type = "audio"
    elif update.message.animation:
        message_type = "animation"
    else:
        message_type = "unknown"

    # Check if the message exceeds the limit
    if not await check_message_limit(update, context, message_type):
        return  # Do not forward or process the message if the limit is exceeded

    # Handle other message scenarios
    if context.user_data.get("awaiting_message"):
        target_chat_id = context.user_data.get("target_chat_id")
        if target_chat_id:
            prompt_message_id = context.user_data.get("prompt_message_id")
            if prompt_message_id:
                try:
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_message_id)
                except Exception:
                    pass
                context.user_data.pop("prompt_message_id", None)
            await send_media_or_text(update, context, target_chat_id)
            await update.message.reply_text(t(user_id, "message_sent"))
        else:
            await send_temporary_message(context, update.effective_chat.id, t(user_id, "no_target_user"))
        context.user_data["awaiting_message"] = False

    elif context.user_data.get("awaiting_broadcast_message"):
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []
        for user in users:
            if str(user["chat_id"]) in ADMIN_CHAT_IDS:
                continue
            try:
                await send_media_or_text(update, context, user["chat_id"])
            except Exception:
                pass
        await update.message.reply_text(t(user_id, "broadcast_sent"))
        prompt_message_id = context.user_data.get("prompt_message_id")
        if prompt_message_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_message_id)
            except Exception:
                pass
            context.user_data.pop("prompt_message_id", None)
        context.user_data["awaiting_broadcast_message"] = False

    else:
        await forward_user_message(update, context)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Check command limit
    if not await check_command_limit(user_id, "start"):
        return  # Do not process further if limit is exceeded

    # Check if user already exists in cached_users
    if any(u["chat_id"] == user_id for u in cached_users):
        return  # Do not send welcome message if user already exists

    user_data = {
        "chat_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user_languages[user_id],
    }

    # Add user to cached_users
    cached_users.append(user_data)
    save_users_and_languages()

    # Send welcome message
    await update.message.reply_text(t(user_id, "welcome_user", name=user.first_name))
    await context.bot.send_message(chat_id=ADMIN_CHAT_IDS[0], text=t(user_id, "start_admin_notify", user_data=yaml.dump(user_data)))

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Check command limit for non-admin users
    if str(user_id) not in ADMIN_CHAT_IDS:
        if not await check_command_limit(user_id, "admin"):
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
            except Exception:
                pass
            return  # Do not process further if limit is exceeded

    # Delete the previous admin panel message if it exists
    if user_id in admin_last_message_ids:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=admin_last_message_ids[user_id])
        except Exception:
            pass

    # Delete the /admin command message
    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception:
        pass

    # Check if the user is an admin
    if str(user_id) not in ADMIN_CHAT_IDS:
        error_message = await update.message.reply_text(t(user_id, "not_admin"))
        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=error_message.chat_id, message_id=error_message.message_id)
        except Exception:
            pass
        return

    # Create the admin panel
    keyboard = [
        [InlineKeyboardButton(t(user_id, "view_user_list"), callback_data="view_users")],
        [InlineKeyboardButton(t(user_id, "send_message_user"), callback_data="send_message_user")],
        [InlineKeyboardButton(t(user_id, "send_message_all"), callback_data="send_message_all")],
        [InlineKeyboardButton(t(user_id, "refresh_data"), callback_data="refresh_data")],
        [InlineKeyboardButton(t(user_id, "remove_user"), callback_data="remove_user")],
        [InlineKeyboardButton(t(user_id, "view_api_keys"), callback_data="view_api_keys")],
        [InlineKeyboardButton(t(user_id, "cancel"), callback_data="cancel")],
    ]
    admin_message = await update.message.reply_text(
        t(user_id, "welcome_admin_panel"),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Store the message ID of the new admin panel
    admin_last_message_ids[user_id] = admin_message.message_id

def update_admin_status():
    """
    Update the admin status of users in cached_users based on ADMIN_CHAT_IDS.
    """
    global cached_users
    admin_ids = set(ADMIN_CHAT_IDS)  # Convert to set for faster lookup
    for user in cached_users:
        user["is_admin"] = str(user["chat_id"]) in admin_ids

    # Add missing admins to cached_users
    for admin_id in admin_ids:
        if not any(user["chat_id"] == int(admin_id) for user in cached_users):
            cached_users.append({
                "chat_id": int(admin_id),
                "username": None,
                "first_name": "Admin",
                "last_name": None,
                "language": "en",
                "is_admin": True,
            })

    save_users_and_languages()

# ==========================
# Language Configuration
# ==========================
LANGUAGES = {
    "en": {
        "not_admin": "🚫 Sorry, you are not an admin and cannot access this section.\n\nBut don't worry! If you have a question or message for the admins, you can type it here, and I'll forward it to them. 📩",
        "welcome_admin_panel": "Welcome to the Admin Panel! Please choose an option:",
        "welcome_user": "🎉 Welcome, {name}! 🎉\nFeel free to explore and interact with the bot.",
        "message_sent": "✅ Message or media sent successfully!",
        "broadcast_sent": "📢 Message sent to all users.",
        "operation_cancelled": "❌ Operation cancelled.",
        "user_removed": "User with Chat ID {chat_id} has been removed from the list.",
        "updated_user_list": "👥 <b>Updated User List:</b>\n\n{user_list}",
        "no_users_found": "No users found.",
        "select_user": "Select a user to send a message:",
        "type_message": "Please type the message or send the media you want to send to user with Chat ID {chat_id}:",
        "type_broadcast": "Please type the message or send the media you want to broadcast:",
        "refresh_success": "🔄 User data refreshed successfully!",
        "view_user_list": "👥 View User List",
        "send_message_user": "✉️ Send Message to Specific User",
        "send_message_all": "📢 Send Message to All Users",
        "refresh_data": "🔄 Refresh User Data",
        "remove_user": "🗑️ Remove User from List",
        "view_api_keys": "🔑 View API Key Stats",
        "cancel": "❌ Cancel",
        "back_to_main": "🔙 Back to Main Menu",
        "select_language": "Please select your language:",
        "lang_updated": "Language updated successfully!",
        "start_admin_notify": "New user started the bot:\n{user_data}",
        "limit_warning": "⚠️ You have reached the limit for {type} messages.\n⏳ Please wait {minutes} minutes for the limit to reset.",
        "no_target_user": "❌ No target user selected.",
        "unsupported_type": "Unsupported message type.",
        "user_info": "📩 New Message from User:\n👤 Name: {name}\n🔗 Username: @{username}\n🆔 Chat ID: {chat_id}",
    },
    "fa": {
        "not_admin": "🚫 متأسفیم، شما ادمین نیستید و نمی‌توانید به این بخش دسترسی داشته باشید.\n\nاما نگران نباشید! اگر سوال یا پیامی برای ادمین‌ها دارید، می‌توانید همینجا تایپ کنید و من آن را برای ادمین‌ها ارسال می‌کنم. 📩",
        "welcome_admin_panel": "به پنل ادمین خوش آمدید! لطفاً یک گزینه را انتخاب کنید:",
        "welcome_user": "🎉 خوش آمدید، {name}! 🎉\nلطفاً از ربات استفاده کنید و اگر سوالی دارید، همینجا بپرسید.",
        "message_sent": "✅ پیام یا رسانه با موفقیت ارسال شد!",
        "broadcast_sent": "📢 پیام به همه کاربران ارسال شد.",
        "operation_cancelled": "❌ عملیات لغو شد.",
        "user_removed": "کاربر با شناسه {chat_id} از لیست حذف شد.",
        "updated_user_list": "👥 <b>لیست کاربران به‌روزرسانی شد:</b>\n\n{user_list}",
        "no_users_found": "هیچ کاربری یافت نشد.",
        "select_user": "یک کاربر را برای ارسال پیام انتخاب کنید:",
        "type_message": "لطفاً پیام یا رسانه‌ای که می‌خواهید به کاربر با شناسه {chat_id} ارسال کنید، وارد کنید:",
        "type_broadcast": "لطفاً پیام یا رسانه‌ای که می‌خواهید به همه کاربران ارسال کنید، وارد کنید:",
        "refresh_success": "🔄 داده‌های کاربران با موفقیت به‌روزرسانی شد!",
        "view_user_list": "👥 مشاهده لیست کاربران",
        "send_message_user": "✉️ ارسال پیام به کاربر خاص",
        "send_message_all": "📢 ارسال پیام به همه کاربران",
        "refresh_data": "🔄 بروزرسانی لیست کاربران",
        "remove_user": "🗑️ حذف کاربر از لیست",
        "view_api_keys": "🔑 مشاهده وضعیت کلیدهای API",
        "cancel": "❌ لغو",
        "back_to_main": "🔙 بازگشت به منوی اصلی",
        "select_language": "لطفاً زبان خود را انتخاب کنید:",
        "lang_updated": "زبان با موفقیت تغییر کرد!",
        "start_admin_notify": "کاربر جدید ربات را استارت کرد:\n{user_data}",
        "limit_warning": "⚠️ شما به محدودیت ارسال پیام {type} رسیده‌اید.\n⏳ لطفاً {minutes} دقیقه صبر کنید تا محدودیت برداشته شود.",
        "no_target_user": "❌ هیچ کاربری انتخاب نشده است.",
        "unsupported_type": "نوع پیام پشتیبانی نمی‌شود.",
        "user_info": "📩 پیام جدید از کاربر:\n👤 نام: {name}\n🔗 نام کاربری: @{username}\n🆔 شناسه: {chat_id}",
    },
}
DEFAULT_LANGUAGE = "en"
user_languages = defaultdict(lambda: DEFAULT_LANGUAGE)

def get_lang(user_id):
    return user_languages[user_id]

def t(user_id, key, **kwargs):
    lang = get_user_language(user_id)
    return LANGUAGES[lang][key].format(**kwargs)

async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("English", callback_data="lang_en")],
        [InlineKeyboardButton("فارسی", callback_data="lang_fa")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        LANGUAGES["en"]["select_language"] + "\n" + LANGUAGES["fa"]["select_language"],
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    if query.data.startswith("lang_"):
        lang = query.data.split("_")[1]
        user_languages[user_id] = lang

        # Update language in cached_users
        for user in cached_users:
            if user["chat_id"] == user_id:
                user["language"] = lang
                break
        save_users_and_languages()

        await query.edit_message_text(
            LANGUAGES["en"]["lang_updated"] + "\n" + LANGUAGES["fa"]["lang_updated"]
        )
        return

    if query.data == "view_users":
        sync_repo()
        update_admin_status()  # Ensure admin status is updated
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []
        # Filter out admins from the user list
        non_admin_users = [user for user in users if not user.get("is_admin", False)]
        if non_admin_users:
            user_list = "\n".join(
                [f"👤 <b>{user['first_name']} {user.get('last_name', '')}</b>\n"
                 f"🔗 Username: @{user['username'] or 'N/A'}\n"
                 f"🆔 Chat ID: <code>{user['chat_id']}</code>\n" for user in non_admin_users]
            )
        else:
            user_list = t(user_id, "no_users_found")
        keyboard = [[InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, "updated_user_list", user_list=user_list), reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton(t(user_id, "view_user_list"), callback_data="view_users")],
            [InlineKeyboardButton(t(user_id, "send_message_user"), callback_data="send_message_user")],
            [InlineKeyboardButton(t(user_id, "send_message_all"), callback_data="send_message_all")],
            [InlineKeyboardButton(t(user_id, "refresh_data"), callback_data="refresh_data")],
            [InlineKeyboardButton(t(user_id, "remove_user"), callback_data="remove_user")],
            [InlineKeyboardButton(t(user_id, "view_api_keys"), callback_data="view_api_keys")],
            [InlineKeyboardButton(t(user_id, "cancel"), callback_data="cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, "welcome_admin_panel"), reply_markup=reply_markup)

    elif query.data == "send_message_user":
        sync_repo()
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []
        keyboard = [
            [InlineKeyboardButton(f"{user['first_name']} (@{user['username']})", callback_data=f"send_to_{user['chat_id']}")]
            for user in users
        ]
        keyboard.append([InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, "select_user"), reply_markup=reply_markup)

    elif query.data.startswith("send_to_"):
        chat_id = int(query.data.split("_")[2])
        context.user_data["target_chat_id"] = chat_id
        context.user_data["awaiting_message"] = True
        keyboard = [[InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        prompt_message = await query.edit_message_text(
            t(user_id, "type_message", chat_id=chat_id),
            reply_markup=reply_markup
        )
        context.user_data["prompt_message_id"] = prompt_message.message_id

    elif query.data == "send_message_all":
        context.user_data["awaiting_broadcast_message"] = True
        keyboard = [[InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        prompt_message = await query.edit_message_text(t(user_id, "type_broadcast"), reply_markup=reply_markup)
        context.user_data["prompt_message_id"] = prompt_message.message_id

    elif query.data == "refresh_data":
        sync_repo()
        await send_temporary_message(context, update.effective_chat.id, t(user_id, "refresh_success"))
        
    elif query.data == "view_api_keys":
        # Get API key statistics
        api_key_stats = get_api_key_stats()
        keyboard = [[InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(api_key_stats, reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "remove_user":
        sync_repo()
        update_admin_status()  # Ensure admin status is updated
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []
        # Filter out admins from the removable user list
        removable_users = [user for user in users if not user.get("is_admin", False)]
        keyboard = [
            [InlineKeyboardButton(f"{user['first_name']} (@{user['username']})", callback_data=f"remove_{user['chat_id']}")]
            for user in removable_users
        ]
        keyboard.append([InlineKeyboardButton(t(user_id, "cancel"), callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(t(user_id, "remove_user"), reply_markup=reply_markup)

    elif query.data.startswith("remove_"):
        chat_id = int(query.data.split("_")[1])
        sync_repo()
        update_admin_status()  # Ensure admin status is updated
        file_path = os.path.join("repo", USER_DATA_FILE)
        with open(file_path, "r") as file:
            users = yaml.safe_load(file) or []
        # Prevent removing admins
        if any(user["chat_id"] == chat_id and user.get("is_admin", False) for user in users):
            await send_temporary_message(context, update.effective_chat.id, "❌ You cannot remove an admin.")
            return
        updated_users = [user for user in users if user["chat_id"] != chat_id]
        with open(file_path, "w") as file:
            yaml.dump(updated_users, file)
        push_changes()
        await send_temporary_message(context, update.effective_chat.id, t(user_id, "user_removed", chat_id=chat_id))
        # Refresh the user list
        sync_repo()
        with open(file_path, "r") as file:
            refreshed_users = yaml.safe_load(file) or []
        non_admin_users = [user for user in refreshed_users if not user.get("is_admin", False)]
        if non_admin_users:
            user_list = "\n".join(
                [f"👤 <b>{user['first_name']} {user.get('last_name', '')}</b>\n"
                 f"🔗 Username: @{user['username'] or 'N/A'}\n"
                 f"🆔 Chat ID: <code>{user['chat_id']}</code>\n" for user in non_admin_users]
            )
        else:
            user_list = t(user_id, "no_users_found")
        keyboard = [[InlineKeyboardButton(t(user_id, "back_to_main"), callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=t(user_id, "updated_user_list", user_list=user_list), reply_markup=reply_markup, parse_mode="HTML")

    elif query.data == "cancel":
        cancel_message = await query.edit_message_text(t(user_id, "operation_cancelled"))
        context.user_data.clear()
        await asyncio.sleep(5)
        try:
            await context.bot.delete_message(chat_id=cancel_message.chat_id, message_id=cancel_message.message_id)
        except Exception:
            pass

# ==========================
# Restart Functions
# ==========================
async def restart_panel():
    """
    Restarts the panel every 5 hours with a delay to allow workflow restart.
    """
    while True:
        await asyncio.sleep((5 * 60 * 60) - 300)  # Wait for 5 hours minus 5 minutes
        print("Preparing to restart the panel...")
        await asyncio.sleep(300)  # Wait for 5 minutes to allow workflow restart
        print("Restarting the panel...")
        os.execv(sys.executable, ['python'] + sys.argv)  # Restart the script

# ==========================
# Trigger Workflow Function
# ==========================
async def trigger_restart_workflow():
    """
    Triggers the 'panel_restart' workflow on GitHub after 4 hours and 55 minutes.
    """
    await asyncio.sleep((4 * 60 * 60) + (55 * 60))  # Wait for 4 hours and 55 minutes
    print("Triggering the 'panel_restart' workflow...")

    github_token = os.getenv("GH_PAT")  # GitHub Personal Access Token
    repo = "Zudiaq/Klavir-Express"  # Repository name
    workflow = "panel_restart.yml"  # Workflow file name

    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow}/dispatches"
    headers = {"Authorization": f"Bearer {github_token}"}
    data = {"ref": "main"}  # Branch to trigger the workflow on

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 204:
        print("Successfully triggered the 'panel_restart' workflow.")
    else:
        print(f"Failed to trigger the workflow: {response.status_code}, {response.text}")

    # Notify GitHub Actions of success before stopping the script
    print("::notice::Panel workflow completed successfully. Preparing to stop the script.")

    # Wait 1 minute before stopping the script
    await asyncio.sleep(60)
    print("Stopping the panel...")
    os._exit(0)  # Use os._exit to terminate the process directly without raising exceptions

# ==========================
# Main Function
# ==========================
async def main():
    load_users_and_languages()  # Load users and languages from YAML file
    update_admin_status()  # Ensure admin status is updated at startup

    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_menu))
    application.add_handler(CommandHandler("lang", lang))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.ALL, handle_message))

    # Start the restart workflow trigger task
    asyncio.create_task(trigger_restart_workflow())

    print("Bot is starting...")
    await application.run_polling()  # Use polling for simplicity in GitHub Actions

if __name__ == "__main__":
    asyncio.run(main())
