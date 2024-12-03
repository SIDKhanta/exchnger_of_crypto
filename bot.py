from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

with open('telegram_token.txt', 'r') as file:
    telegram_token_of_bot = file.readline().strip()
with open('contacts.txt', 'r') as file:
    contacts = file.read().strip()

async def main_menu():
    buttons = [
        [
            KeyboardButton(
                text="Начать",
                web_app=WebAppInfo(url="https://docs-python.ru/packages/biblioteka-python-telegram-bot-python/")
            )
        ],
        [KeyboardButton("Помощь"), KeyboardButton("Контакты")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def help_menu():
    buttons = [
        [KeyboardButton("Как обменивать токены"), KeyboardButton("Правила безопасности")],
        [KeyboardButton("Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = await main_menu()
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Помощь":
        await update.message.reply_text(
            "Чем могу помочь?",
            reply_markup=await help_menu()
        )
    elif text == "Как обменивать токены":
        await update.message.reply_text("Для обмена следуйте инструкциям.")
    elif text == "Правила безопасности":
        await update.message.reply_text("Никогда не сообщайте никому свою seed-фразу или приватные ключи.")
    elif text == "Назад в главное меню":
        reply_markup = await main_menu()
        await update.message.reply_text(
            "Вы вернулись в главное меню:",
            reply_markup=reply_markup
        )
    elif text == "Контакты":
        await update.message.reply_text(f"Наши контакты:\n{contacts}")
    else:
        await update.message.reply_text("Неизвестная команда. Попробуйте еще раз.")

def main():
    if not telegram_token_of_bot:
        raise ValueError("Токен отсутствует.")
    if not contacts:
        raise ValueError("Контакты отсутствуют.")

    app = Application.builder().token(telegram_token_of_bot).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
