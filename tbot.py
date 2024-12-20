# t.me/beauty_salon_hse_bot.

import logging
import os
import pandas as pd
import xlsxwriter

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
from datetime import datetime
from urllib.parse import quote


def get_calendar_link(title: str, date_start: datetime, date_end: datetime, location: str = "",
                      details: str = "") -> str:
    '''
    :param title: заголовок события
    :param date_start: дата и время начала мероприятия
    :param date_end: дата и время окончания мероприятия
    :param location: место проведения мероприятия
    :param details: описание мероприятия
    :return: ссылка для создания события в календаре
    '''
    res = f"https://www.google.com/calendar/render?action=TEMPLATE&text={quote(title)}"
    res += f"&dates={date_start.strftime('%Y%m%dT%H%M%S')}/{date_end.strftime('%Y%m%dT%H%M%S')}"
    if location:
        res += f"&location={quote(location)}"
    if details:
        res += f"&details={quote(details)}"

    return res


TOKEN = os.getenv("TOKEN")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MENU, SERVICE_CHOOSE, MASTER_CHOOSE, DAY_CHOOSE, TIME_CHOOSE, CHOOSE_CANCEL_APPOINTMENT, APPLY_CANCEL_APPOINTMENT, ADMIN_MENU, ADMIN_ADD_MASTER = range(9)

DL_ST = 3  # в некторых функциях отвечает за длину строки в таблице выводимых вариантов ответов
DURATION_OF_PROCEDURE = 2  # продолжительность процедур в часах

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation.
       If user is new so add him to data_base,
       else show a menu"""

    telegram_id = update.message.from_user.id
    admin_id = get_admin_id_by_telegram_id(session, telegram_id)

    if admin_id is not None:
        context.user_data["admin_id"] = admin_id

        reply_keyboard = [["получить статистику на данный момент", "Добавить мастера"]]
        await update.message.reply_text(
            "Привет, админ! Я могу помочь тебе рассмотреть собранную статистику!\n",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )
        return ADMIN_MENU
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

def get_statistics_file():
    """Готовит файл со статистикой для отправки администратору"""
    table_profit_by_service = get_table_profit_by_service(session)
    table_new_clients = get_table_new_clients_per_time(session)
    table_masters_work = get_table_work_masters(session)

    file_name = 'statistics_report.xlsx'
    workbook = xlsxwriter.Workbook(file_name)
    f_worksheet = workbook.add_worksheet()
    f_worksheet.name = "новые клиенты со временем"
    s_worksheet = workbook.add_worksheet()
    s_worksheet.name = "Доход по услугам"
    t_worksheet = workbook.add_worksheet()
    t_worksheet.name = "Доход по каждому мастеру"

    # Запись заголовков
    f_worksheet.write('A1', 'Дата')
    f_worksheet.write('B1', 'Количество новых клиентов')

    # Запись данных
    for i, row in enumerate(table_new_clients.values, start=1):
        f_worksheet.write(i, 0, row[0])  # Дата
        f_worksheet.write(i, 1, row[1])  # Количество новых клиентов

    # Создание графика
    chart = workbook.add_chart({'type': 'line'})

    # Добавление данных в график
    chart.add_series({
        'name': 'Количество новых клиентов',  # Название серии данных
        'categories': f"='новые клиенты со временем'!$A$2:$A${len(table_new_clients) + 1}",  # Диапазон данных для категорий (даты)
        'values': f"='новые клиенты со временем'!$B$2:$B${len(table_new_clients) + 1}",  # Диапазон данных для значений (новые клиенты)
    })

    # Настройка графика (заголовок, оси)
    chart.set_title({'name': 'Новые клиенты со временем'})
    chart.set_x_axis({'name': 'Дата'})
    chart.set_y_axis({'name': 'Количество новых клиентов'})

    # Вставка графика на лист
    f_worksheet.insert_chart('D2', chart)

    # Запись заголовков
    s_worksheet.write('A1', 'Услуга')
    s_worksheet.write('B1', 'Количество записей')
    s_worksheet.write('C1', 'Стоимость услуги')
    s_worksheet.write('D1', 'Общий доход')

    for i, row in enumerate(table_profit_by_service.values, start=1):
        s_worksheet.write(i, 0, row[0])
        s_worksheet.write(i, 1, row[1])
        s_worksheet.write(i, 2, row[2])
        s_worksheet.write(i, 3, row[3])

    # Создание гистограммы прибыли по каждому мастеру
    chart = workbook.add_chart({'type': 'column'})

    # Добавление данных в график
    chart.add_series({
        'name': 'Общий доход',
        'categories': f"='Доход по услугам'!$A$2:$A${len(table_profit_by_service) + 1}",
        'values': f"='Доход по услугам'!$D$2:$D${len(table_profit_by_service) + 1}",
    })

    # Настройка графика
    chart.set_title({'name': 'Общий доход по каждой услуге'})
    chart.set_x_axis({'name': 'Наименование услуги', 'reverse': True})
    chart.set_y_axis({'name': 'Общая стоимость оказанных услуг'})

    # Вставка графика на лист
    s_worksheet.insert_chart('F2', chart)

    # Запись заголовков
    t_worksheet.write('A1', 'Имя мастера')
    t_worksheet.write('B1', 'Количество выполненных услуг')
    t_worksheet.write('C1', 'Общая стоимость выполненных услуги')

    for i, row in enumerate(table_masters_work.values, start=1):
        t_worksheet.write(i, 0, row[0])
        t_worksheet.write(i, 1, row[1])
        t_worksheet.write(i, 2, row[2])

    # Создание гистограммы прибыли по каждому мастеру
    chart = workbook.add_chart({'type': 'bar'})

    # Добавление данных в график
    chart.add_series({
        'name': 'Общее количество услуг',
        'categories': f"='Доход по каждому мастеру'!$A$2:$A${len(table_masters_work) + 1}",  # Диапазон имен мастеров
        'values': f"='Доход по каждому мастеру'!$B$2:$B${len(table_masters_work) + 1}",  # Диапазон значений прибыли
    })

    # Настройка графика
    chart.set_title({'name': 'Общий количество услуг по каждому мастеру'})
    chart.set_x_axis({'name': 'Количество оказанных услуг'})
    chart.set_y_axis({'name': 'Имя мастера', 'reverse': True})

    # Вставка графика на лист
    t_worksheet.insert_chart('E2', chart)

    # Сохранение файла
    workbook.close()
    return file_name

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Get the information from user`s answer what he want to do and show him what he wanted"""

    user = update.message.from_user
    logger.info(f"Username: {user.username}, his choice in menu is {update.message.text}")

    if update.message.text == "получить статистику на данный момент":
        file_name = get_statistics_file()

        await update.message.reply_document(
            document=file_name,
            filename=file_name,
            caption="Вот таблица со статистикой"
        )
        os.remove(file_name)
        reply_keyboard = [["получить статистику на данный момент", "Добавить мастера"]]
        await update.message.reply_text(
            text="изволите еще чего нибудь?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
            ),
        )

        return ADMIN_MENU
    elif update.message.text == "Добавить мастера":
        await update.message.reply_text("Перешли мне какое нибудь сообщение нового мастера.")
        return ADMIN_ADD_MASTER
    else:
        reply_keyboard = [["получить статистику на данный момент", "Добавить мастера"]]
        await update.message.reply_text(
            "К сожалению я не понял твой ответ. Выбери пожалуйста вариант из клавиатуры.\n Выбери, что ты хочешь сделать?",
            reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, one_time_keyboard=True,
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
            await update.message.reply_text(f"Вы успешно выдали роль мастера!")
        else:
            await update.message.reply_text(f"Что то пошло не так. Попробуйте попозже.")
    else:
        await update.message.reply_text(f"Вы не переслали сообщение")

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
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
