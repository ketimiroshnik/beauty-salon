import xlsxwriter
from urllib.parse import quote
from datetime import datetime
from db.database_functions import *

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

def get_statistics_file(session):
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