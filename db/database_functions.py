from orm import *
from datetime import datetime, timedelta
from sqlalchemy import select, insert, and_, func, update
from sqlalchemy.orm import Session

def get_client_id_by_telegram_id(session: Session, telegram_id: int):
    """Возвращает client_id по telegram_id. Если нет такого клиента, возвращает None"""
    client_id = session.execute(
        select(Client.client_id)
        .join(User, User.id == Client.client_id)
        .where(User.telegram_id == telegram_id)
    ).scalar()
    return client_id

def add_user(session: Session, telegram_id: int, name: str):
    """Добавляет user по telegram_id и сразу добавляет его в клиентов"""
    new_user = User(telegram_id=telegram_id, role='client')
    session.add(new_user)
    session.flush()
    new_client = Client(client_id=new_user.id, name=name, time_registered=datetime.now())
    session.add(new_client)
    session.commit()
    return new_client.client_id

def get_masters_for_service(session: Session, service_id: int):
    """Выдает список мастеров выполняющих услугу с service_id со свободными слотами в ближайший месяц"""
    next_month = datetime.now() + timedelta(days=30)
    masters = session.execute(
        select(Master)
        .join(MasterService, Master.id == MasterService.master_id)
        .join(Time, Master.id == Time.master_id)
        .where(
            MasterService.service_id == service_id,
            Master.is_active == True,
            Time.status == True,
            Time.time <= next_month
        )
    ).scalars().all()
    return masters

def get_free_days_for_master(session: Session, master_id: int):
    """Возвращает список дней когда у данного мастера есть хотя бы одна свободная запись"""
    free_days = session.execute(
        select(func.date(Time.time))
        .where(
            Time.master_id == master_id,
            Time.status == True
        )
        .group_by(func.date(Time.time))
    ).scalars().all()
    return free_days

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
    """Выдает все записи для клиента кроме отмененных как список словарей"""
    appointments = session.execute(
        select(Appointment, Client, Master, Service)
        .outerjoin(Client, Appointment.client_id == Client.client_id)
        .outerjoin(Master, Appointment.master_id == Master.id)
        .outerjoin(Service, Appointment.service_id == Service.id)
        .where(Appointment.client_id == client_id, Appointment.status)
        .order_by(Appointment.appointment_time)
    ).all()
    if not appointments:
        return []
    result = []
    for app, client, master, service in appointments:
        result.append({
            "appointment_id": app.id,
            "client": {
                "id": client.client_id if client else None,
                "name": client.name if client else "Unknown",
            },
            "master": {
                "id": master.id if master else None,
                "name": master.name if master else "N/A",
            },
            "service": {
                "id": service.id if service else None,
                "title": service.title if service else "N/A",
                "cost": float(service.cost) if service else 0.0,
            },
            "appointment_time": app.appointment_time,
            "status": app.status,
        })
    return result

def get_appointment_by_id(session: Session, appointment_id: int):
    """Возвращает запись по id. Если такой нет, то None"""
    appointment = session.execute(
        select(Appointment, Client, Master, Service)
        .outerjoin(Client, Appointment.client_id == Client.client_id)
        .outerjoin(Master, Appointment.master_id == Master.id)
        .outerjoin(Service, Appointment.service_id == Service.id)
        .where(Appointment.id == appointment_id)
    ).one_or_none()
    if not appointment:
        return None
    app, client, master, service = appointment
    return {
        "appointment_id": app.id,
        "client": {
            "id": client.client_id if client else None,
            "name": client.name if client else "Unknown",
        },
        "master": {
            "id": master.id if master else None,
            "name": master.name if master else "Unknown",
        },
        "service": {
            "id": service.id if service else None,
            "title": service.title if service else "Unknown",
            "cost": float(service.cost) if service else 0.0,
        },
        "appointment_time": app.appointment_time,
        "status": app.status,
    }

def cancel_appointment(session: Session, appointment_id: int):
    """Выставляет статус 0 записи. Возвращает true если это что-то поменяло"""
    result = session.execute(
        update(Appointment)
        .where(Appointment.id == appointment_id)
        .values(status=0)
    )
    session.commit()
    return result.rowcount > 0