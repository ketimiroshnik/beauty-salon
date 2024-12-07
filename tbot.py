# t.me/beauty_salon_hse_bot.
TOKEN = "7106520053:AAHtdf-9E2DKTIDxiauTj56WxyqlfC26Yms"
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

SIGN_UP_NAME,  SIGN_UP_PHONE, SIGN_UP_END, MENU, MOUTH_CHOOSE, DAY_CHOOSE, TIME_CHOOSE = range(7)

CALENDAR_31 = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
                    ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"],
                    ["Назад"]]
CALENDAR_30 = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
                    ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30"], 
                    ["Назад"]]
CALENDAR_28 = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                    ["11", "12", "13", "14", "15", "16", "17", "18", "19", "20"],
                    ["21", "22", "23", "24", "25", "26", "27", "28"],
                    ["Назад"]]
MOUTHS = [["Январь", "Февраль", "Март", "Апрель"],
                ["Май", "Июнь", "Июль", "Август"],
                ["Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
                ["Назад"]]

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

async def mouth_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text != "Назад"):

        # TODO проверить, есть ли свободные слоты в выбранном месяце
        mouth_free = True
        context.user_data["mouth"] = update.message.text
        if (mouth_free):
            if (context.user_data["mouth"] in ["Январь", "Март", "Май", "Июль", "Сентябрь", "Ноябрь"]):
                reply_keyboard = CALENDAR_31
            elif(context.user_data["mouth"] == "Февраль"):
                reply_keyboard = CALENDAR_28
            else:
                reply_keyboard = CALENDAR_30
            
            await update.message.reply_text(
                "Выберите дату записи",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return DAY_CHOOSE
        else:
            reply_keyboard = MOUTHS

            await update.message.reply_text(
                "В этом месяце нет доступных записей, выбери другой",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MOUTH_CHOOSE
    else:
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU

    

async def day_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text != "Назад"):
        # TODO проверить, есть ли свободные слоты в выбранном дне
        day_free = True
        context.user_data["day"] = update.message.text
        if (day_free):
            reply_keyboard = [["10:00-11:00", "11:00-12:00", "12:00-13:00"],
                              ["Назад"]]

            # TODO настроить, чтобы отображалсь только возможные интервалы, которые свободны
            
            await update.message.reply_text(
                "Выберите время записи",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return TIME_CHOOSE
        else:
            if (context.user_data["mouth"] in ["Январь", "Март", "Май", "Июль", "Сентябрь", "Ноябрь"]):
                reply_keyboard = CALENDAR_31
            elif(context.user_data["mouth"] == "Февраль"):
                reply_keyboard = CALENDAR_28
            else:
                reply_keyboard = CALENDAR_30
                
            await update.message.reply_text(
                "В этот день нету свободной записи, выбери другой",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return DAY_CHOOSE
    else:
        reply_keyboard = MOUTHS
    
        await update.message.reply_text(
            "Выберите месяц записи текущего года",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MOUTH_CHOOSE

async def time_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text != "Назад"):

        # TODO перенести в бд данные о записи
        await update.message.reply_text(f"Вы записались на {context.user_data["day"]} {context.user_data["mouth"]} {update.message.text}") 
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    else:
        if (context.user_data["mouth"] in ["Январь", "Март", "Май", "Июль", "Сентябрь", "Ноябрь"]):
            reply_keyboard = CALENDAR_31
        elif(context.user_data["mouth"] == "Февраль"):
            reply_keyboard = CALENDAR_28
        else:
            reply_keyboard = CALENDAR_30
            
        await update.message.reply_text(
            "В этот день нету свободной записи, выбери другой",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE



async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the information from user`s answer what he want to do and show him what he wanted"""

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his choice in menu is {update.message.text}")

    # TODO: продролжить здесь...
    if (update.message.text  == "Записаться") :
            reply_keyboard = MOUTHS
    
            await update.message.reply_text(
                "Выберите месяц записи текущего года",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MOUTH_CHOOSE
    elif (update.message.text == "Получить список записей") :
        pass
    elif (update.message.text == "Отменить запись") :
        pass
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
            MOUTH_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mouth_choose)],
            DAY_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_choose)],
            TIME_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_choose)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()