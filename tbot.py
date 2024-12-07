# t.me/beauty_salon_hse_bot.

import logging
import os

from db.connection import session
from db.database_functions import *
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MENU, SERVICE_CHOOSE, MASTER_CHOOSE, DAY_CHOOSE, TIME_CHOOSE, CHOOSE_CANCEL_APPOINTMENT, APPLY_CANCEL_APPOINTMENT = range(7)

DAYS = [datetime.strptime('2024-01-01', '%Y-%m-%d') + timedelta(days=x) for x in range(30)]

SERVICES = ["Постричься", "Покраска волос", "Маникюр"]

MASTERS = ["Амиран", "Екатерина", "Арина", "Роман", "Анна"]

TIMES = [datetime.strptime('2024-01-01 12:00', '%Y-%m-%d %H:%M') + timedelta(hours=x) for x in range(4)]

DL_ST = 3 # в некторых функциях отвечает за длину строки в таблице выводимых вариантов ответов

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation.
       If user is new so add him to data_base,
       else show a menu"""

    telegram_id = update.message.from_user.id
    client_id = get_client_id_by_telegram_id(session, telegram_id)

    if client_id is None:
        name = update.message.from_user.first_name
        client_id = add_user(session, telegram_id, name)
        pass

    context.user_data["client_id"] = client_id

    reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
    await update.message.reply_text(
        "Привет! Я могу записать в салон и могу рассказать тебе о твоих записях!\n"
        "Выбери, что ты хочешь сделать?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
        ),
    )
    return MENU

async def service_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in context.user_data["services"]):

         # TODO получить id для услуги

        context.user_data["service"] = SERVICES.index(update.message.text)
        masters = get_masters_for_service(session, context.user_data["service"])

        # TODO по списку id поулчить список мастеров MASTERS

        context.user_data["masters"] = MASTERS
        if (len(context.user_data["masters"]) != 0):
            reply_keyboard = [context.user_data["masters"][i:i+DL_ST] for i in range(0, len(context.user_data["masters"]), DL_ST)]
            reply_keyboard.append(["Назад"])
            await update.message.reply_text(
                "Выбери мастера",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MASTER_CHOOSE
        else:
            context.user_data["services"] = SERVICES
            reply_keyboard = [SERVICES[i:i+DL_ST] for i in range(0, len(SERVICES), DL_ST)]
            reply_keyboard.append(["Назад"])
            await update.message.reply_text(
                "Нету свободного мастера на данную услугу( Выбери другую услугу",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return SERVICE_CHOOSE
    elif (update.message.text  == "Назад"):
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    else:
        reply_keyboard = [context.user_data["services"][i:i+DL_ST] for i in range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери из предложенных вариантов услуг!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE

    

async def master_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in context.user_data["masters"]):

        # TODO получить id для мастера

        context.user_data["master"] = MASTERS.index(update.message.text)
        days = get_free_days_for_master(session, context.user_data["master"]) #days=DAYS

        day=[]
        for k in DAYS:
            day.append(k.strftime('%Y-%m-%d'))

        context.user_data["days"] = day
        reply_keyboard = [context.user_data["days"][i:i+10] for i in range(0, len(context.user_data["days"]), 10)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери удобный вам день",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE
    elif (update.message.text  == "Назад"):
        context.user_data["services"] = SERVICES
        reply_keyboard = [SERVICES[i:i+DL_ST] for i in range(0, len(SERVICES), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери услугу, на которую хотели бы записаться",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE
    else:
        reply_keyboard = [context.user_data["masters"][i:i+DL_ST] for i in range(0, len(context.user_data["masters"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери предложенного мастера!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_CHOOSE
    

async def day_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in context.user_data["days"]):
        context.user_data["day"] = datetime.strptime(update.message.text, '%Y-%m-%d')

        times = get_free_days_for_master(session, context.user_data["master"]) #times=TIMES

        time=[]
        for k in TIMES:
            time.append(k.strftime('%H:%M'))
        
        context.user_data["times"] = time
        reply_keyboard = [context.user_data["times"][i:i+DL_ST] for i in range(0, len(context.user_data["times"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери удобное вам время",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return TIME_CHOOSE
    elif (update.message.text  == "Назад"):
        reply_keyboard = [context.user_data["masters"][i:i+DL_ST] for i in range(0, len(context.user_data["masters"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери мастера",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_CHOOSE
    else:
        reply_keyboard = [context.user_data["days"][i:i+10] for i in range(0, len(context.user_data["days"]), 10)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери из предложенных дней!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE

async def time_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in context.user_data["times"]):
        context.user_data["time"] = datetime.strptime(update.message.text, '%H:%M')
        create_appointment(session, context.user_data["client_id"], context.user_data["service"], context.user_data["master"], context.user_data["day"].replace(hour = context.user_data["time"].hour, minute = context.user_data["time"].minute))

        # TODO везде, где поиск по индексам, использовать функцию перехода по id к названию

        await update.message.reply_text(f"Вы записаны на услугу: {SERVICES[context.user_data["service"]]} к мастеру: {MASTERS[context.user_data["master"]]} на {context.user_data["day"].strftime('%Y-%m-%d')} число к {context.user_data["time"].strftime('%H:%M')}")
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    elif (update.message.text  == "Назад"):
        reply_keyboard = [context.user_data["days"][i:i+10] for i in range(0, len(context.user_data["days"]), 10)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери удобный вам день",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE
    else:
        reply_keyboard = [context.user_data["times"][i:i+DL_ST] for i in range(len(0, context.user_data["times"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери из предоженного времени!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return TIME_CHOOSE


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
        cancel_appointment(session, appointment_id)
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
        reply_keyboard = [["Назад"], [str(i) for i in appointments_dict]]
        await update.message.reply_text(
            "Записи с таким номером нет в списке. Выбери пожалуйста существующий номер.",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return CHOOSE_CANCEL_APPOINTMENT

    appointment_id = appointments_dict[int(answer)]
    context.user_data["id_appointment_for_cancel"] = appointment_id
    this_appointment = get_appointment_by_id(session, appointment_id)

    text = []
    text.append("Вот выбранная запись:")

    now = []
    now.append(f"Услуга: {this_appointment["service"]["title"]}")
    now.append(f"Дата: {this_appointment["appointment_time"].strftime("%Y-%m-%d")}")
    now.append(f"Время: {this_appointment["appointment_time"].strftime("%H:%M")}")
    now.append(f"Мастер: {this_appointment["master"]["name"]}")

    text.append(", ".join(now))
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
        context.user_data["services"] = SERVICES
        reply_keyboard = [SERVICES[i:i+DL_ST] for i in range(0, len(SERVICES), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери услугу, на которую хотечешь записаться",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE
    elif (update.message.text == "Получить список записей") :
        appointments = get_client_appointments(session, context.user_data["client_id"])
        if (not appointments):
            reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
            await update.message.reply_text(
                "У тебя нет записей. Но ты всегда можешь записаться)) Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MENU
        else:
            text = ["Вот список твоих записей"]
            for i in range(len(appointments)):
                now = []
                now.append(f"Услуга: {appointments[i]["service"]["title"]}")
                now.append(f"Дата: {appointments[i]["appointment_time"].strftime("%Y-%m-%d")}")
                now.append(f"Время: {appointments[i]["appointment_time"].strftime("%H:%M")}")
                now.append(f"Мастер: {appointments[i]["master"]["name"]}")
                text.append(f"{i + 1}." + ", ".join(now))
            text.append("\nВыбери, что ты хочешь сделать?")
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
        appointments = get_client_appointments(session, context.user_data["client_id"])
        if (not appointments):
            reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
            await update.message.reply_text(
                "У тебя нет записей. Но ты всегда можешь записаться)) Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MENU
        else:
            text = ["Вот список твоих записей"]

            # сохраняем присвоенные номера, чтобы мы могли потом все удалить
            context.user_data["list_for_cancel"] = {} # dict: number: appointment_id

            numbers_for_user_answer = []

            for i in range(len(appointments)):
                numbers_for_user_answer.append(str(i + 1))
                context.user_data["list_for_cancel"][i + 1] = appointments[i]["appointment_id"]
                now = []
                now.append(f"Услуга: {appointments[i]["service"]["title"]}")
                now.append(f"Дата: {appointments[i]["appointment_time"].strftime("%Y-%m-%d")}")
                now.append(f"Время: {appointments[i]["appointment_time"].strftime("%H:%M")}")
                now.append(f"Мастер: {appointments[i]["master"]["name"]}")
                text.append(f"{i + 1}." + ", ".join(now))

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
        #print(123)
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
            SERVICE_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_choose)],
            MASTER_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, master_choose)],
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
    main()
