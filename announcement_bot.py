"""
Multi-User Telegram Announcement Bot
-------------------------------------
Har user ka data (uske groups) alag-alag store hota hai.
User bot ko jis group me admin bana ke add karega, wo group
sirf usi user ke "mere groups" list me aayega.

Features:
  /start        -> Bot register karega, welcome message
  /addgroup     -> Bot ko group me add karke, group me ye command bhejo taaki wo tumhare account se link ho jaye
  /mygroups     -> Apne saare linked groups dekho
  /announce     -> Announcement bhejna shuru karo (text/photo/video/document sab chalega)
  /cancel       -> Chal rahi process cancel karo

Requirements:
    pip install python-telegram-bot==21.4

Run:
    export BOT_TOKEN="123456:ABC-YOUR-TOKEN"
    python announcement_bot.py
"""

import os
import sqlite3
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "bot_data.db")
WAITING_FOR_MESSAGE = 1

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            chat_title TEXT,
            UNIQUE(owner_id, chat_id)
        )
        """
    )
    conn.commit()
    conn.close()


def add_user(user_id, username, first_name):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
    )
    conn.commit()
    conn.close()


def add_group_for_user(owner_id, chat_id, chat_title):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO groups (owner_id, chat_id, chat_title) VALUES (?, ?, ?)",
        (owner_id, chat_id, chat_title),
    )
    conn.commit()
    conn.close()


def remove_group_for_user(owner_id, chat_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM groups WHERE owner_id = ? AND chat_id = ?", (owner_id, chat_id)
    )
    conn.commit()
    conn.close()


def get_groups_for_user(owner_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT chat_id, chat_title FROM groups WHERE owner_id = ?", (owner_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# /start
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        "Namaste {}! 👋\n\n"
        "Main multi-user Announcement Bot hoon. Har user ka data alag rehta hai.\n\n"
        "Steps:\n"
        "1️⃣ Mujhe apne group me admin bana ke add karo\n"
        "2️⃣ Us group me jaake /addgroup command bhejo (isse group tumhare account se link ho jayega)\n"
        "3️⃣ Phir yahan mujhe /announce bhejo aur apna message do\n"
        "4️⃣ Groups select karo (ya 'Select All') aur bhej do!\n\n"
        "/mygroups - apne linked groups dekho".format(user.first_name)
    )


# ---------------------------------------------------------------------------
# /addgroup  -> run this INSIDE the group, links that group to the sender
# ---------------------------------------------------------------------------

async def addgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "Ye command sirf group ke andar chalti hai. Pehle mujhe group me add karo, "
            "phir wahan /addgroup bhejo."
        )
        return

    # Check bot is admin in this group
    bot_member = await chat.get_member(context.bot.id)
    if bot_member.status not in (ChatMemberStatus.ADMINISTRATOR,):
        await update.message.reply_text(
            "⚠️ Mujhe pehle is group me Admin banao, tabhi announcement bhej paunga."
        )
        return

    add_user(user.id, user.username, user.first_name)
    add_group_for_user(user.id, chat.id, chat.title)

    await update.message.reply_text(
        f"✅ Ye group '{chat.title}' ab tumhare account se link ho gaya hai.\n"
        f"Bot ke DM me jaake /mygroups check karo."
    )


# ---------------------------------------------------------------------------
# /mygroups
# ---------------------------------------------------------------------------

async def mygroups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    groups = get_groups_for_user(user.id)
    if not groups:
        await update.message.reply_text(
            "Abhi tak koi group link nahi hai.\n"
            "Bot ko group me admin add karo aur wahan /addgroup bhejo."
        )
        return

    text = "📋 Tumhare Linked Groups:\n\n"
    for g in groups:
        text += f"• {g['chat_title']}  (ID: {g['chat_id']})\n"
    await update.message.reply_text(text)


# ---------------------------------------------------------------------------
# /announce conversation
# ---------------------------------------------------------------------------

async def announce_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    groups = get_groups_for_user(user.id)

    if not groups:
        await update.message.reply_text(
            "Tumhare paas koi linked group nahi hai. Pehle /addgroup use karke group link karo."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 Apna announcement message bhejo (text, photo, video ya document — "
        "sab chalega). Caption bhi le lega agar media ke sath doge.\n\n"
        "Cancel karne ke liye /cancel bhejo."
    )
    return WAITING_FOR_MESSAGE


async def announce_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save the message reference (chat_id + message_id) so we can copy it later
    context.user_data["announce_msg"] = {
        "chat_id": update.effective_chat.id,
        "message_id": update.effective_message.message_id,
    }
    context.user_data["selected_groups"] = set()

    user = update.effective_user
    groups = get_groups_for_user(user.id)
    context.user_data["all_groups"] = groups

    keyboard = build_group_keyboard(groups, context.user_data["selected_groups"])
    await update.message.reply_text(
        "👥 Kis-kis group me bhejna hai? Select karo:", reply_markup=keyboard
    )
    return ConversationHandler.END


def build_group_keyboard(groups, selected):
    buttons = []
    for g in groups:
        mark = "✅ " if g["chat_id"] in selected else "⬜ "
        buttons.append(
            [
                InlineKeyboardButton(
                    f"{mark}{g['chat_title']}",
                    callback_data=f"toggle:{g['chat_id']}",
                )
            ]
        )
    all_selected = len(selected) == len(groups) and len(groups) > 0
    select_all_label = "🔲 Deselect All" if all_selected else "☑️ Select All"
    buttons.append([InlineKeyboardButton(select_all_label, callback_data="toggle_all")])
    buttons.append([InlineKeyboardButton("🚀 Send Now", callback_data="send_now")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_announce")])
    return InlineKeyboardMarkup(buttons)


async def group_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    groups = context.user_data.get("all_groups", [])
    selected = context.user_data.get("selected_groups", set())

    if data == "toggle_all":
        if len(selected) == len(groups):
            selected.clear()
        else:
            selected = {g["chat_id"] for g in groups}
        context.user_data["selected_groups"] = selected
        await query.edit_message_reply_markup(
            reply_markup=build_group_keyboard(groups, selected)
        )
        return

    if data.startswith("toggle:"):
        chat_id = int(data.split(":")[1])
        if chat_id in selected:
            selected.remove(chat_id)
        else:
            selected.add(chat_id)
        context.user_data["selected_groups"] = selected
        await query.edit_message_reply_markup(
            reply_markup=build_group_keyboard(groups, selected)
        )
        return

    if data == "cancel_announce":
        context.user_data.clear()
        await query.edit_message_text("❌ Announcement cancel kar diya gaya.")
        return

    if data == "send_now":
        if not selected:
            await query.answer("Pehle kam se kam ek group select karo!", show_alert=True)
            return

        msg_ref = context.user_data.get("announce_msg")
        if not msg_ref:
            await query.edit_message_text("⚠️ Message data mil nahi paya, dobara /announce try karo.")
            return

        sent, failed = 0, []
        for chat_id in selected:
            try:
                await context.bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=msg_ref["chat_id"],
                    message_id=msg_ref["message_id"],
                )
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send to {chat_id}: {e}")
                failed.append(str(chat_id))

        result_text = f"✅ Announcement {sent} group(s) me bhej diya gaya."
        if failed:
            result_text += f"\n⚠️ Fail hua in group IDs me: {', '.join(failed)}"

        context.user_data.clear()
        await query.edit_message_text(result_text)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Cancel kar diya gaya.")
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Track when bot is added/removed from a group (auto info, owner still needs /addgroup)
# ---------------------------------------------------------------------------

async def track_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    chat = result.chat
    new_status = result.new_chat_member.status

    if new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        conn = get_db()
        conn.execute("DELETE FROM groups WHERE chat_id = ?", (chat.id,))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise SystemExit("BOT_TOKEN environment variable set karo pehle!")

    init_db()

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("announce", announce_start)],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.ALL & ~filters.COMMAND, announce_receive)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addgroup", addgroup))
    app.add_handler(CommandHandler("mygroups", mygroups))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(group_button_handler))
    app.add_handler(ChatMemberHandler(track_chat_member, ChatMemberHandler.MY_CHAT_MEMBER))

    logger.info("Bot chalu ho gaya...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
