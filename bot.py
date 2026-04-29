import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
ADMIN_IDS  = set(
    int(x.strip())
    for x in os.environ.get("ADMIN_IDS", "").split(",")
    if x.strip()
)

tasks: dict[int, str | None] = {}

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text("👋 Привет, админ!\n/task <текст> — создать задание")
    else:
        await update.message.reply_text("👋 Следи за каналом и будь первым!")

async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ Нет прав.")
        return
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Пример: /task Написать статью до пятницы")
        return
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Взять задание", callback_data="take")]])
    sent = await context.bot.send_message(chat_id=CHANNEL_ID, text=f"📋 Задание:\n\n{text}", reply_markup=keyboard)
    tasks[sent.message_id] = None
    await update.message.reply_text("✅ Опубликовано!")

async def callback_take(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    msg_id = query.message.message_id
    if msg_id not in tasks:
        tasks[msg_id] = None
    winner = tasks[msg_id]
    if winner is not None:
        await query.answer(f"Опоздал! Задание уже взял @{winner} 😔", show_alert=True)
        return
    username = user.username or user.full_name
    tasks[msg_id] = username
    await query.edit_message_text(text=f"{query.message.text}\n\n🏆 Задание взял: @{username}")
    await query.answer("🎉 Ты взял задание!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("task", cmd_task))
    app.add_handler(CallbackQueryHandler(callback_take, pattern="^take$"))
    app.run_polling(drop_pending_updates=True)

if name == "__main__":
    main()
