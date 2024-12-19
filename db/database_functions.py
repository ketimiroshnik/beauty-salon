from db.orm import *
from datetime import datetime, timedelta
from sqlalchemy import select, insert, and_, func, update
from sqlalchemy.orm import Session
import pandas as pd

def get_client_id_by_telegram_id(session: Session, telegram_id: int):
    """Возвращает client_id по telegram_id. Если нет такого клиента, возвращает None"""
    client_id = session.execute(
        select(Client.client_id)
        .join(User, User.id == Client.client_id)
        .where(User.telegram_id == telegram_id)
    ).scalar()
    return client_id

def get_admin_id_by_telegram_id(session: Session, telegram_id: int):
    """Проверяет, является ли пользователь админом, если да, возвращает user_id, если нет, возвращает None"""
    admin_id = session.execute(
        select(User.id)
        .where((User.telegram_id == telegram_id) & (User.role == "admin"))
    ).scalar()
    return admin_id

def get_table_profit_by_service(session: Session):
    """
    Запрос на получение таблицы со столбцами:
    1. Услуга
    2. Количество записей на данную услугу
    3. Стоимость услуги
    4. Общий доход по данной услуге (цена * количество)
    """
    # Запрос данных: считаем количество записей и общий доход по каждой услуге
    result = session.execute(
        select(
            Service.title.label('Услуга'),
            func.count(Appointment.id).filter(Appointment.status == 1).label('Количество записей'),
            Service.cost.label('Стоимость услуги'),
            (func.count(Appointment.id).filter(Appointment.status == 1) * Service.cost).label(
                'Общий доход за все записи')
        )
        .join(Appointment, Appointment.service_id == Service.id)
        .group_by(Service.id)
        .order_by(
            (func.count(Appointment.id).filter(Appointment.status == 1) * Service.cost).desc()
        )
    ).all()

    result = pd.DataFrame(result)

    return result

def get_table_new_clients_per_time(session: Session):
    """
    Запрос на получение таблицы со столбцами:
    1. Дата
    2. Количество новых клиентов в эту дату
    """
    result = session.query(
        func.date(Client.time_registered).label('date'),
        func.count(Client.client_id).label('new_clients')
    ).group_by(func.date(Client.time_registered)).all()

    result = pd.DataFrame(result)

    return result

def get_table_work_masters(session: Session):
    """
    Запрос на получение таблицы со столбцами:
    1. Имя мастера
    2. Количество выполненных услуг
    3. Общая стоимость выполненных услуг
    """
    result = session.query(
        Master.name.label('имя мастера'),
        func.count(Appointment.id).label('количество выполненных услуг'),
        func.sum(Service.cost).label('общая стоимость услуг')
    ).join(
        Appointment, Appointment.master_id == Master.id
    ).join(
        Service, Service.id == Appointment.service_id
    ).filter(
        Appointment.status == 1  # Статус 1, значит услуга выполнена
    ).group_by(
        Master.id
    ).order_by(
        func.count(Appointment.id).desc()  # Сортировка по количеству
    ).all()

    result = pd.DataFrame(result)

    return result

def add_user(session: Session, telegram_id: int, name: str):
    """Добавляет user по telegram_id и сразу добавляет его в клиентов"""
    new_user = User(telegram_id=telegram_id, role='client')
    session.add(new_user)
    session.flush()
    new_client = Client(client_id=new_user.id, name=name, time_registered=datetime.now())
    session.add(new_client)
    session.commit()
    return new_client.client_id


def get_services(session: Session):
    """Возвращает все услуги"""
    return session.query(Service).all()


def get_masters_for_service(session: Session, service_id: int):
    """Выдает список мастеров выполняющих услугу с service_id со свободными слотами в ближайший месяц"""
    next_month = datetime.now() + timedelta(days=30)
    available_masters = (
        session.query(Master)
        .join(Time, Master.id == Time.master_id)
        .join(MasterService, Master.id == MasterService.master_id)
        .filter(
            and_(
                MasterService.service_id == service_id,
                Time.status == True,
                Time.time >= datetime.now(),
                Time.time < next_month
            )
        )
        .distinct()
        .all()
    )
    return available_masters


def get_free_days_for_master(session: Session, master_id: int):
    """Возвращает список дней когда у данного мастера есть хотя бы одна свободная запись"""
    free_days = (
        session.query(func.date(Time.time).label("free_date"))
        .filter(Time.master_id == master_id, Time.status == True)
        .distinct()
        .order_by("free_date")
        .all()
    )
    return [result.free_date for result in free_days]


def get_timeslots_for_day(session: Session, master_id: int, day: datetime):
    """Возвращает свободные слоты мастера в определенный день"""
    timeslots = session.execute(
        select(Time)
        .where(
            Time.master_id == master_id,
            func.date(Time.time) == day.date(),
            Time.status == True
        )
    ).scalars().all()
    return timeslots


def create_appointment(session: Session, client_id: int, service_id: int, master_id: int, appointment_time: datetime):
    """Создает запись с заданными параметрами, возвращает id записи, поднимает ошибку если слот занят"""
    time_slot = session.query(Time).filter(
        Time.master_id == master_id,
        Time.time == appointment_time,
        Time.status.is_(True)
    ).first()
    if not time_slot:
        raise ValueError("Слот недоступен")
    new_appointment = Appointment(
        client_id=client_id, service_id=service_id, master_id=master_id,
        appointment_time=appointment_time, status=1
    )
    session.add(new_appointment)
    session.execute(
        Time.__table__.update()
        .where(and_(Time.master_id == master_id, Time.time == appointment_time))
        .values(status=False)
    )
    session.commit()
    return new_appointment.id


def get_client_appointments(session: Session, client_id: int):
    """Выдает все записи для клиента кроме отмененных"""
    appointments = session.execute(
        select(Appointment, Client, Master, Service)
        .outerjoin(Client, Appointment.client_id == Client.client_id)
        .outerjoin(Master, Appointment.master_id == Master.id)
        .outerjoin(Service, Appointment.service_id == Service.id)
        .where(Appointment.client_id == client_id, Appointment.status)
        .order_by(Appointment.appointment_time)
    ).all()
    return appointments


def get_appointment_by_id(session: Session, appointment_id: int):
    """Возвращает запись по id. Если такой нет, то None"""
    appointment = session.execute(
        select(Appointment, Client, Master, Service)
        .outerjoin(Client, Appointment.client_id == Client.client_id)
        .outerjoin(Master, Appointment.master_id == Master.id)
        .outerjoin(Service, Appointment.service_id == Service.id)
        .where(Appointment.id == appointment_id)
    ).one_or_none()
    return appointment


def cancel_appointment(session: Session, appointment_id: int):
    """Выставляет статус 0 записи. Возвращает true если это что-то поменяло"""
    result = session.execute(
        update(Appointment)
        .where(Appointment.id == appointment_id)
        .values(status=0)
    )
    session.commit()
    return result.rowcount > 0