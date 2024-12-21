# t.me/beauty_salon_hse_bot.

import logging
import os
from supportive import *

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
    CallbackContext
)


TOKEN = os.getenv("TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


MENU, SERVICE_CHOOSE, MASTER_CHOOSE, DAY_CHOOSE, TIME_CHOOSE, CHOOSE_CANCEL_APPOINTMENT, APPLY_CANCEL_APPOINTMENT, ADMIN_MENU, ADMIN_ADD_MASTER, MASTER_MENU, DAY_CHOOSE_MASTER, TIME_CHOOSE_MASTER, ADMIN_ADD_SERVICE_CHOICE_TITLE, ADMIN_ADD_SERVICE_CHOICE_DESCRIPTION, ADMIN_ADD_SERVICE_CHOICE_PRICE, SERVICE_CHOOSE_MASTER = range(16)
DL_ST = 3  # в некторых функциях отвечает за длину строки в таблице выводимых вариантов ответов
DURATION_OF_PROCEDURE = 2  # продолжительность процедур в часах

admin_reply_keyboard = [["Получить статистику на данный момент", "Добавить мастера", "Добавить услугу"]]
master_menu_keyboard = [["Получить список предстоящих записей клиентов", "Добавить окошко"], ["Получить список твоих окон", "Добавить себе услугу"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation.
       If user is new so add him to data_base,
       else show a menu"""

    telegram_id = update.message.from_user.id
    admin_id = get_admin_id_by_telegram_id(session, telegram_id)
    master_id = get_master_id_by_telegram_id(session, telegram_id)

    if admin_id is not None:
        context.user_data["admin_id"] = admin_id
        await update.message.reply_text(
            "Привет, админ! Выбери, что ты хочешь сделать?\n",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )
        return ADMIN_MENU
    elif master_id is not None:
        context.user_data["master_id"] = master_id
        reply_keyboard = master_menu_keyboard
        await update.message.reply_text(
            "Привет, мастер! Выбери, что ты хочешь сделать?\n",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_MENU
    else:
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
    if (update.message.text in [k.title for k in context.user_data["services"]]):

        # получить id для услуги

        for k in context.user_data["services"]:
            if k.title == update.message.text:
                context.user_data["service"] = k

        # по списку id поулчить список мастеров MASTERS

        context.user_data["masters"] = get_masters_for_service(session, context.user_data["service"].id)
        if (len(context.user_data["masters"]) != 0):
            reply_keyboard = [[k.name for k in context.user_data["masters"][i:i + DL_ST]] for i in
                              range(0, len(context.user_data["masters"]), DL_ST)]
            reply_keyboard.append(["Назад"])
            await update.message.reply_text(
                "Выбери мастера",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MASTER_CHOOSE
        else:
            reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                              range(0, len(context.user_data["services"]), DL_ST)]
            reply_keyboard.append(["Назад"])
            await update.message.reply_text(
                "Нету свободного мастера на данную услугу( Выбери другую услугу",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return SERVICE_CHOOSE
    elif (update.message.text == "Назад"):
        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    else:
        reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери из предложенных вариантов услуг!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE

async def master_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in [k.name for k in context.user_data["masters"]]):

        # получить id для мастера

        for k in context.user_data["masters"]:
            if k.name == update.message.text:
                context.user_data["master"] = k

        context.user_data["days"] = get_free_days_for_master(session, context.user_data["master"].id)  # days=DAYS

        reply_keyboard = [context.user_data["days"][i:i + 10] for i in range(0, len(context.user_data["days"]), 10)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери удобный вам день",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE
    elif (update.message.text == "Назад"):
        reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери услугу, на которую хотели бы записаться",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE
    else:
        reply_keyboard = [[k.name for k in context.user_data["masters"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["masters"]), DL_ST)]
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

        context.user_data["times"] = [k.time.strftime('%H:%M') for k in
                                      get_timeslots_for_day(session, context.user_data["master"].id,
                                                            context.user_data["day"])]  # times=TIMES

        reply_keyboard = [context.user_data["times"][i:i + DL_ST] for i in
                          range(0, len(context.user_data["times"]), DL_ST)]
        reply_keyboard.append(["Назад"])

        await update.message.reply_text(
            "Выбери удобное вам время",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return TIME_CHOOSE
    elif (update.message.text == "Назад"):
        reply_keyboard = [[k.name for k in context.user_data["masters"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["masters"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери мастера",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_CHOOSE
    else:
        reply_keyboard = [context.user_data["days"][i:i + 10] for i in range(0, len(context.user_data["days"]), 10)]
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
        create_appointment(session, context.user_data["client_id"], context.user_data["service"].id,
                           context.user_data["master"].id,
                           context.user_data["day"].replace(hour=context.user_data["time"].hour,
                                                            minute=context.user_data["time"].minute))

        # везде, где поиск по индексам, использовать функцию перехода по id к названию

        await update.message.reply_text(
            f"Вы записаны на услугу: {context.user_data["service"].title} к мастеру: {context.user_data["master"].name} на {context.user_data["day"].strftime('%Y-%m-%d')} число к {context.user_data["time"].strftime('%H:%M')}")

        title = f"Процедура: {context.user_data["service"].title}"
        start_time = datetime.combine(context.user_data["day"], context.user_data["time"].time())
        end_time = start_time + timedelta(hours=DURATION_OF_PROCEDURE)
        details = f"Вы записались на услугу {context.user_data["service"].title} к мастеру {context.user_data["master"].name} на {context.user_data["day"].strftime('%Y-%m-%d')} число к {context.user_data["time"].strftime('%H:%M')}."
        await update.message.reply_text(
            f"Если не хотите забыть про данное событие - добавьте его в свой google календарь! \n Это можно сделать перейдя по ссылке: {get_calendar_link(title=title, date_start=start_time, date_end=end_time, details=details)}")

        reply_keyboard = [["Записаться", "Получить список записей", "Отменить запись"]]
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MENU
    elif (update.message.text == "Назад"):
        reply_keyboard = [context.user_data["days"][i:i + 10] for i in range(0, len(context.user_data["days"]), 10)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери удобный вам день",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE
    else:
        reply_keyboard = [context.user_data["times"][i:i + DL_ST] for i in
                          range(len(0, context.user_data["times"]), DL_ST)]
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
    appointment, client, master, service = this_appointment

    text = []
    text.append("Вот выбранная запись:")

    now = []
    now.append(f"Услуга: {service.title}")
    now.append(f"Дата: {appointment.appointment_time.strftime("%Y-%m-%d")}")
    now.append(f"Время: {appointment.appointment_time.strftime("%H:%M")}")
    now.append(f"Мастер: {master.name}")

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

    if (update.message.text == "Записаться"):
        context.user_data["services"] = get_services(session)
        reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери услугу, на которую хочешь записаться",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE
    elif (update.message.text == "Получить список записей"):
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
                appointment, client, master, service = appointments[i]
                now.append(f"Услуга: {service.title}")
                now.append(f"Дата: {appointment.appointment_time.strftime("%Y-%m-%d")}")
                now.append(f"Время: {appointment.appointment_time.strftime("%H:%M")}")
                now.append(f"Мастер: {master.name}")
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
    elif (update.message.text == "Отменить запись"):
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
            context.user_data["list_for_cancel"] = {}  # dict: number: appointment_id

            numbers_for_user_answer = []

            for i in range(len(appointments)):
                appointment, client, master, service = appointments[i]
                numbers_for_user_answer.append(str(i + 1))
                context.user_data["list_for_cancel"][i + 1] = appointment.id
                now = []
                now.append(f"Услуга: {service.title}")
                now.append(f"Дата: {appointment.appointment_time.strftime("%Y-%m-%d")}")
                now.append(f"Время: {appointment.appointment_time.strftime("%H:%M")}")
                now.append(f"Мастер: {master.name}")
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

async def time_choose_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == "Назад":
        reply_keyboard = [["Назад"]]
        await update.message.reply_text(
            "Выведи нужную дату в формате DD.MM.YYYY",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE_MASTER

    try:
        time_object = datetime.strptime(answer, '%H:%M').time()
    except Exception:
        reply_keyboard = [["Назад"]]
        await update.message.reply_text(
            "К сожалению твой ответ некорректен. Выведи нужное время в 24-часовом формате hh:mm",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return TIME_CHOOSE_MASTER

    date_object = context.user_data["date"]
    combined_datetime = datetime.combine(date_object.date(), time_object)

    res = create_new_timeslot(session, context.user_data["master_id"], combined_datetime)  # создали окно
    logger.info(f"{res}")

    formatted_datetime = combined_datetime.strftime('%d.%m.%Y %H:%M')
    reply_keyboard = master_menu_keyboard
    await update.message.reply_text(
        f"Вы успешно добавили окно на {formatted_datetime}."
        "\nВыбери, что ты хочешь сделать?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True,
        ),
    )
    return MASTER_MENU

async def day_choose_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == "Назад":
        reply_keyboard = master_menu_keyboard
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_MENU
    try:
        date_object = datetime.strptime(answer, '%d.%m.%Y')
        context.user_data["date"] = date_object
        reply_keyboard = [["Назад"]]
        await update.message.reply_text(
            "Выведи нужное время в 24-часовом формате hh:mm",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return TIME_CHOOSE_MASTER
    except Exception:
        reply_keyboard = [["Назад"]]
        await update.message.reply_text(
            "К сожалению твой ответ некорректен. Выведи нужную дату в формате DD.MM.YYYY",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE_MASTER

async def service_choose_master(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (update.message.text in [k.title for k in context.user_data["services"]]):

        for k in context.user_data["services"]:
            if k.title == update.message.text:
                context.user_data["service"] = k

        # context.user_data["service"].id
        logger.info(f"{context.user_data["service"].id} {context.user_data["master_id"]}")
        add_service_master_connection(session, context.user_data["master_id"], context.user_data["service"].id)

        reply_keyboard = master_menu_keyboard
        await update.message.reply_text(
            f"Услуга {context.user_data["service"].title} успешно добавлена.\n Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_MENU
    elif (update.message.text == "Назад"):
        reply_keyboard = master_menu_keyboard
        await update.message.reply_text(
            "Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return MASTER_MENU
    else:
        context.user_data["services"] = get_services(session)
        reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери из предложенных вариантов услуг!!!",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE_MASTER

async def master_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    if update.message.text == "Получить список предстоящих записей клиентов":
        appointments = get_master_appointments(session, context.user_data["master_id"])
        if (not appointments):
            reply_keyboard = master_menu_keyboard
            await update.message.reply_text(
                "К тебе нету записей. Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MASTER_MENU
        else:
            text = ["Вот список записей к тебе"]
            for i in range(len(appointments)):
                now = []
                appointment, client, master, service = appointments[i]
                now.append(f"Услуга: {service.title}")
                now.append(f"Дата: {appointment.appointment_time.strftime("%Y-%m-%d")}")
                now.append(f"Время: {appointment.appointment_time.strftime("%H:%M")}")
                now.append(f"Клиент: {client.name}")
                text.append(f"{i + 1}." + ", ".join(now))
            text.append("\nВыбери, что ты хочешь сделать?")
            text = '\n'.join(text)
            reply_keyboard = master_menu_keyboard
            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
        return MASTER_MENU
    elif update.message.text == "Получить список твоих окон":
        timeslots = get_master_timeslots(session, context.user_data["master_id"])
        if not timeslots:
            reply_keyboard = master_menu_keyboard
            await update.message.reply_text(
                "У тебя нет окон. Выбери, что ты хочешь сделать?",
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
            return MASTER_MENU
        else:
            text = ["Вот список твоих окон:"]
            for i in range(len(timeslots)):
                timeslot = timeslots[i]
                formatted_datetime = timeslot.time.strftime('%d.%m.%Y %H:%M')
                text.append(f"{i + 1}. {formatted_datetime}" )
            text.append("\nВыбери, что ты хочешь сделать?")
            text = '\n'.join(text)
            reply_keyboard = master_menu_keyboard
            await update.message.reply_text(
                text,
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True,
                ),
            )
        return MASTER_MENU
    elif update.message.text == "Добавить себе услугу":
        context.user_data["services"] = get_services(session)
        reply_keyboard = [[k.title for k in context.user_data["services"][i:i + DL_ST]] for i in
                          range(0, len(context.user_data["services"]), DL_ST)]
        reply_keyboard.append(["Назад"])
        await update.message.reply_text(
            "Выбери услугу",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return SERVICE_CHOOSE_MASTER
    elif update.message.text == "Добавить окошко":
        reply_keyboard = [["Назад"]]
        await update.message.reply_text(
            "Выведи нужную дату в формате DD.MM.YYYY",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return DAY_CHOOSE_MASTER
    else:
        reply_keyboard = master_menu_keyboard
        await update.message.reply_text(
            "К сожалению я не понял твой ответ. Выбери пожалуйста вариант из клавиатуры.\n Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return ADMIN_MENU

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the information from user`s answer what he want to do and show him what he wanted"""

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his choice in menu is {update.message.text}")

    if update.message.text == "Получить статистику на данный момент":
        file_name = get_statistics_file()

        await update.message.reply_document(
            document=file_name,
            filename=file_name,
            caption="Вот таблица со статистикой"
        )
        os.remove(file_name)
        await update.message.reply_text(
            text="изволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )

        return ADMIN_MENU
    elif update.message.text == "Добавить мастера":
        await update.message.reply_text("Перешли мне какое нибудь сообщение нового мастера.")
        return ADMIN_ADD_MASTER
    elif update.message.text == "Добавить услугу":
        await update.message.reply_text("Напишите наименование услуги")
        return ADMIN_ADD_SERVICE_CHOICE_TITLE
    else:
        await update.message.reply_text(
            "К сожалению я не понял твой ответ. Выбери пожалуйста вариант из клавиатуры.\n Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )
        return ADMIN_MENU

async def admin_add_master(update: Update, context: CallbackContext) -> int:
    if 'forward_from' in update.message.api_kwargs:
        telegram_id = update.message.api_kwargs['forward_from']['id']

        master_id = get_client_id_by_telegram_id(session, telegram_id)

        if master_id is None:
            name = update.message.api_kwargs['forward_from']['first_name']
            master_id = add_user(session, telegram_id, name)

        if set_master_state(session, master_id):
            await update.message.reply_text(
                text="Вы успешно выдали роль мастера! \nизволите еще чего нибудь?",
                reply_markup=ReplyKeyboardMarkup(
                    admin_reply_keyboard, one_time_keyboard=True,
                ),
            )
        else:
            await update.message.reply_text(
                text="Что то пошло не так. Попробуйте попозже. \nизволите еще чего нибудь?",
                reply_markup=ReplyKeyboardMarkup(
                    admin_reply_keyboard, one_time_keyboard=True,
                ),
            )
    else:
        await update.message.reply_text(
            text="Вы не переслали сообщение \nизволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )

    return ADMIN_MENU

async def admin_add_service_choice_title(update: Update, context: CallbackContext) -> int:
    service_title = update.message.text
    if get_service_by_title(session, service_title) is not None:
        await update.message.reply_text(
            "Услуга с таким именем существует \nизволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )
        return ADMIN_MENU

    context.user_data["service_title"] = service_title
    await update.message.reply_text("Напишите описание услуги")
    return ADMIN_ADD_SERVICE_CHOICE_DESCRIPTION

async def admin_add_service_choice_description(update: Update, context: CallbackContext) -> int:
    description = update.message.text
    context.user_data["service_description"] = description
    await update.message.reply_text("Напишите цену услуги, только число")
    return ADMIN_ADD_SERVICE_CHOICE_PRICE

async def admin_add_service_choice_price(update: Update, context: CallbackContext) -> int:
    price = update.message.text
    if not price.isdigit():
        await update.message.reply_text(text="Вы ввели не число\nНапишите цену услуги, только число")
        return ADMIN_ADD_SERVICE_CHOICE_PRICE

    price = int(price)

    res = create_service(session, context.user_data["service_title"], context.user_data["service_description"], price)
    if res is not None:
        await update.message.reply_text(
            text="Вы успешно создали новую услугу! \nизволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )
    else:
        await update.message.reply_text(
            text="Что то пошло не так, попробуйте позже \nизволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                admin_reply_keyboard, one_time_keyboard=True,
            ),
        )
    return ADMIN_MENU

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
            ADMIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu)],
            ADMIN_ADD_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_master)],
            MASTER_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, master_menu)],
            DAY_CHOOSE_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, day_choose_master)],
            TIME_CHOOSE_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_choose_master)],
            SERVICE_CHOOSE_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, service_choose_master)],
            ADMIN_ADD_SERVICE_CHOICE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_service_choice_title)],
            ADMIN_ADD_SERVICE_CHOICE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_service_choice_description)],
            ADMIN_ADD_SERVICE_CHOICE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_service_choice_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
