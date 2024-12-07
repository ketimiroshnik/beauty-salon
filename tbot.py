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

MENU, MOUTH_CHOOSE, DAY_CHOOSE, TIME_CHOOSE, CHOOSE_CANCEL_APPOINTMENT, APPLY_CANCEL_APPOINTMENT = range(6)

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
       If user is new so add him to data_base,
       else show a menu"""
    # TODO: проверить есть ли пользователь с этим тг_id
    #  тг_id == update.message.from_user.id
    need_sign_up = True

    if need_sign_up:
        # TODO: add user to bd
        pass

    # TODO: save here bd_id of user
    context.user_data["db_id"] = -1

    reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
    await update.message.reply_text(
        "Привет! Я могу записать в салон и могу рассказать тебе о твоих записях!\n"
        "Выбери, что ты хочешь сделать?",
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
            "Выберите время записи",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE


async def apply_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer.lower() == "нет":
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Хорошо, процесс отмены записи остановлен.\nВыбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    elif answer.lower() == "да":
        appointment_id = context.user_data["id_appointment_for_cancel"]
        # TODO удалить запись с id == appointment_id
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Запись успешно отменена.\nВыбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    else:
        reply_keyboard = [["Да", "Нет"]]
        await update.message.reply_text(
            "К сожалению я не понял твоего ответа. Напиши пожалуйста Да или Нет",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
    return APPLY_CANCEL_APPOINTMENT




async def choose_cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == "Назад":
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU

    appointments_dict = context.user_data["list_for_cancel"]
    if not answer.isdigit() or int(answer) not in appointments_dict:
        print(12345678)
        reply_keyboard = [["Назад"], [str(i) for i in appointments_dict]]
        await update.message.reply_text(
            "Записи с таким номером нет в списке. Выбери пожалуйста существующий номер.",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return CHOOSE_CANCEL_APPOINTMENT

    appointment_id = appointments_dict[int(answer)]
    # TODO по appointment_id получаем из бд информацию о данной записи
    context.user_data["id_appointment_for_cancel"] = appointment_id
    this_appointment = {"date": "13.12.24", "time": "19:00",
                             "name of master": "Даниил", "procedure": "Стрижка", "appointment_id": 10}

    text = []
    text.append("Вот выбранная запись:")
    now = []
    for key, value in this_appointment.items():
        if key == "appointment_id":
            continue
        now.append(f"{key}: {value}")
    text.append(" ".join(now))
    text.append("Вы уверены, что хотите отменить эту запись?")
    text = '\n'.join(text)

    reply_keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
        ),
    )
    return APPLY_CANCEL_APPOINTMENT







async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the information from user`s answer what he want to do and show him what he wanted"""

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his choice in menu is {update.message.text}")

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
        # TODO выгрузить из бд список записей
        user_have_appointment = True
        if (not user_have_appointment):
            reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
            await update.message.reply_text(
                "У тебя нет записей. Но ты всегда можешь записаться)) Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MENU
        else:
            # TODO получаем из бд данные о записях пользователя и кладем его в список
            # (тут должен быть нормальный список)
            appointments = [{"date": "12.12.24", "time": "13:00",
                             "name of master": "Надя", "procedure": "Маникюр", "appointment_id": 1},
                            {"date": "13.12.24", "time": "11:00", "name of master": "Лена",
                             "procedure": "Стрижка", "appointment_id": 1}, ]
            text = ["Вот список твоих записей"]
            for i in range(len(appointments)):
                now = [f"{i + 1}."]
                for key, value in appointments[i].items():
                    if key == "appointment_id":
                        continue
                    now.append(f"{key}: {value}")
                text.append(",\t".join(now))
            text = '\n'.join(text)
            reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MENU
    elif (update.message.text == "Отменить запись") :
        # TODO выгрузить из бд список записей
        user_have_appointment = True
        if (not user_have_appointment):
            reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
            await update.message.reply_text(
                "У тебя нет записей. Но ты всегда можешь записаться)) Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MENU
        else:
            # TODO получаем из бд данные о записях пользователя и кладем его в список
            # (тут должен быть нормальный список)
            appointments = [{"date": "12.12.24", "time": "13:00",
                             "name of master": "Надя", "procedure": "Маникюр", "appointment_id": 1},
                            {"date": "13.12.24", "time": "11:00", "name of master": "Лена",
                             "procedure": "Стрижка", "appointment_id": 1}, ]
            text = ["Вот список твоих записей"]

            # сохраняем присвоенные номера, чтобы мы могли потом все удалить
            context.user_data["list_for_cancel"] = {} # dict: number: appointment_id

            numbers_for_user_answer = []

            for i in range(len(appointments)):
                now = [f"{i + 1}."]
                numbers_for_user_answer.append(str(i+1))
                for key, value in appointments[i].items():
                    if key == "appointment_id":
                        context.user_data["list_for_cancel"][i+1] = value
                        continue
                    now.append(f"{key}: {value}")
                text.append(",\t".join(now))
            text.append("\nВыбери номер записи, от которой ты хочешь отписаться")
            text = '\n'.join(text)

            reply_keyboard = [["Назад"], numbers_for_user_answer]
            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return CHOOSE_CANCEL_APPOINTMENT
    else:
        print(123)
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "К сожалению я не понял твой ответ. Выбери пожалуйста вариант из клавиатуры.\n Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU

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
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            MOUTH_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, mouth_choose)],
            DAY_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_choose)],
            TIME_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_choose)],
            CHOOSE_CANCEL_APPOINTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_cancel_appointment)],
            APPLY_CANCEL_APPOINTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, apply_cancel_appointment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main())
