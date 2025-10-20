import asyncio
from datetime import datetime, timedelta
from typing import Final
from decouple import config
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
)

# === Configuration ===
TOKEN: Final = config('BOT_TOKEN')

# === Unused ===
BOT_NAME = config('BOT_USERNAME')

# Message quotas
TEXT_LIMIT = int(config('LIMIT_TXT'))
VIDEO_LIMIT = int(config('LIMIT_VID'))

# Warn when remaining counts reach these numbers
WARN_THRESHOLDS = config('WARN_TXT').split(',')
WARN_THRESHOLDS = [int(e.strip()) for e in WARN_THRESHOLDS]

# === In-memory tracking ===
user_counts = {}  # {user_id: {"name": str, "text": n, "video": m}}
last_reset_time = datetime.now()

print(f'setup complete, time is {last_reset_time}')

def check_time():
    global last_reset_time
    current_time = datetime.now()
    if current_time - last_reset_time > timedelta(hours=24):
        last_reset_time = current_time
        return True
    else:
        return False

# === Reset counts every 24 hours ===
async def reset_counts_periodically():
    global user_counts, last_reset_time
    while True:
        await asyncio.sleep(24 * 60 * 60)
        user_counts.clear()
        last_reset_time = datetime.now()
        print("✅ Counts reset at", last_reset_time)

# === Handle incoming messages ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.from_user:
        return

    user = update.message.from_user
    user_id = user.id
    username = user.username or user.full_name

    # check if 24 hours passed
    if check_time():
        user_counts.clear()

    # Initialize user record
    if user_id not in user_counts:
        user_counts[user_id] = {"name": username, "text": 0, "video": 0}

    # Determine message type and limits
    if update.message.video:
        msg_type = "video"
        user_counts[user_id]["video"] += 1
        count = user_counts[user_id]["video"]
        remaining = VIDEO_LIMIT - count
        limit = VIDEO_LIMIT
    else:
        msg_type = "text"
        user_counts[user_id]["text"] += 1
        count = user_counts[user_id]["text"]
        remaining = TEXT_LIMIT - count
        limit = TEXT_LIMIT

    # --- Print message info to terminal ---
    msg_preview = update.message.text or "[non-text message]"
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
          f"{username} | {msg_type.upper()} | Remaining: {remaining}/{limit} | Message: {msg_preview}")
    
    # Warn at thresholds
    if remaining in WARN_THRESHOLDS:
        
        print(f'send reply: warn')
        await update.message.reply_text(
            f"⚠️ {username}, you have {remaining} {msg_type} messages left today (limit {limit})."
        )

    # Warn when exceeded
    if remaining < 0:
        await update.message.reply_text(
            f"🚫 {username}, you've exceeded your daily {msg_type} message limit ({limit})."
        )


# === Command: /usage ===
async def show_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays how many text and video messages each user has sent in 24 hours."""

    user = update.message.from_user
    username = user.username or user.full_name

    print(f'usage query from {username}')

    # check if 24 hours has passed
    if check_time():
        user_counts.clear()

    if not user_counts:
        await update.message.reply_text("📊 No messages recorded yet today.")
        return

    lines = ["📊 *Message usage in the past 24 hours:*", ""]
    for user_data in user_counts.values():
        name = user_data["name"]
        text_count = user_data["text"]
        video_count = user_data["video"]
        lines.append(f"👤 {name}\n📝 Text: {text_count}/{TEXT_LIMIT}\n🎥 Video: {video_count}/{VIDEO_LIMIT}\n")

    summary = "\n".join(lines)
    print(f'send reply: {lines}')
    await update.message.reply_text(summary, parse_mode="Markdown")


# === Main entry point ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers
    group_filter = filters.ChatType.GROUPS & (filters.TEXT | filters.VIDEO)
    app.add_handler(CommandHandler("usage", show_usage))
    app.add_handler(MessageHandler(group_filter, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()