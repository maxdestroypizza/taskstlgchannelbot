import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки — задай через переменные окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@ваш_канал")  # например @mychannel или -1001234567890
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "123456789").split(",")))  # Telegram ID админов

# Хранилище взятых заданий: {message_id: user или None}
taken_tasks = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /task <текст> — публикует задание в канале"""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text("⛔ У тебя нет прав для публикации заданий.")
        return

    if not context.args:
        await update.message.reply_text(
            "Использование:\n/task Текст задания\n\nПример:\n/task Сделать дизайн баннера до пятницы"
        )
        return

    task_text = " ".join(context.args)

    keyboard = [[InlineKeyboardButton("✅ Взять задание", callback_data="take_task")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Публикуем пост в канале
    sent = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"📋 *Задание:*\n\n{task_text}",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )

    taken_tasks[sent.message_id] = None
    logger.info(f"Опубликовано задание #{sent.message_id} в {CHANNEL_ID}")

    await update.message.reply_text(f"✅ Задание опубликовано в канале!")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки"""
    query = update.callback_query
    await query.answer()

    message_id = query.message.message_id
    user = query.from_user

    # Инициализируем задание если первый раз видим этот message_id
    if message_id not in taken_tasks:
        taken_tasks[message_id] = None

    if taken_tasks[message_id] is None:
        # Никто ещё не взял — фиксируем этого пользователя
        taken_tasks[message_id] = user

        username = f"@{user.username}" if user.username else user.full_name
        original_text = query.message.text

        # Редактируем пост в канале: убираем кнопку, добавляем победителя
        await query.edit_message_text(
            text=f"{original_text}\n\n🏆 *Задание взял:* {username}",
            parse_mode="Markdown",
        )

        logger.info(f"Задание #{message_id} взял {username} (id={user.id})")

    else:
        # Уже занято
        winner = taken_tasks[message_id]
        winner_name = f"@{winner.username}" if winner.username else winner.full_name

        await query.answer(
            f"Опоздал! Задание уже взял {winner_name} 😔",
            show_alert=True,
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update.effective_user.id):
        await update.message.reply_text(
            "👋 Привет, админ!\n\nДля публикации задания используй:\n/task Текст задания"
        )
    else:
        await update.message.reply_text("👋 Привет! Следи за заданиями в канале.")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("task", task))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="take_task"))

    logger.info("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
