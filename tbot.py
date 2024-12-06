# t.me/beauti_salon_hse_bot.
TOKEN = "7822764300:AAGfTqdvGn5BfvUEi9Y2O4viOsbbZtjmjk8"
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

SIGN_UP_NAME,  SIGN_UP_PHONE, SIGN_UP_END, MENU = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation.
       If user is new so start to sign up and ask a name,
       else show a menu"""

    # TODO: проверить есть ли пользователь с этим id в бд и если нет то регистрация, иначе - меню
    need_sign_up = True
    if need_sign_up:
        await update.message.reply_text(
            "Привет! Я помогу тебе записаться в  салон!\nДля начала давай зарегистрируем тебя. Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove(),
        )
        return SIGN_UP_NAME
    else:
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Привет! Я могу записать в салон и могу рассказать тебе о твоих записях!\n"
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU


async def sign_up_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sign up. Get the name from user`s answer and ask the phone"""
    context.user_data["name_for_sign_up"] = update.message.text  # save name in dict

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his name is {update.message.text}")
    await update.message.reply_text(
        "Напиши пожалуйста свой номер телефона для связи",
        reply_markup=ReplyKeyboardRemove(),
    )
    return SIGN_UP_PHONE

async def sign_up_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the phone from user`s answer and show menu. Also add user to database"""

    context.user_data["phone_for_sign_up"] = update.message.text  # safe phone

    # TODO: sign up user in database, where name == context.user_data["name_for_sign_up"]
    #  and phone == context.user_data["phone_for_sign_up"]

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his telephon number is {update.message.text}")

    reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
    await update.message.reply_text(
        "Спасибо, за контактные данные! Теперь мы можем перейти к записи. \nВыбери, что ты хочешь сделать?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
        ),
    )
    return MENU


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the information from user`s answer what he want to do and show him what he wanted"""

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his choice in menu is {update.message.text}")

    # TODO: продролжить здесь...
    if (update.message.text == "Записаться") :
        pass
    elif (update.message.text == "Получить список записей") :
        pass
    elif (update.message.text == "Отменить запись") :
        pass

    # TODO: эту надпись, конечно, убрать
    await update.message.reply_text("Ты в меню.",
                                    reply_markup=ReplyKeyboardRemove(),)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye!.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SIGN_UP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sign_up_name)],
            SIGN_UP_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sign_up_phone)],
            MENU: [MessageHandler(filters.Regex("^(Записаться|Получить список записей|Отменить запись)$"), menu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
