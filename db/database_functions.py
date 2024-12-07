from orm import *
from datetime import datetime, timedelta
from sqlalchemy import select, insert, and_, func
from sqlalchemy.orm import Session

def get_client_id_by_telegram_id(session: Session, telegram_id: int):
    client_id = session.execute(
        select(Client.client_id)
        .join(User, User.id == Client.client_id)
        .where(User.telegram_id == telegram_id)
    ).scalar()
    return client_id

def add_user(session: Session, telegram_id: int, name: str):
    new_user = User(telegram_id=telegram_id, role='client')
    session.add(new_user)
    session.flush()
    new_client = Client(client_id=new_user.id, name=name, time_registered=datetime.now())
    session.add(new_client)
    session.commit()
    return new_client.client_id

def get_masters_for_service(session: Session, service_id: int):
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
    timeslots = session.execute(
        select(Time)
        .where(
            Time.master_id == master_id,
            func.date(Time.time) == day.date(),
            Time.status == True
        )
    ).scalars().all()
    return timeslots

def create_appointment(
    session: Session, client_id: int, service_id: int, master_id: int, appointment_time: datetime):
    time_slot = session.query(Time).filter(
        Time.master_id == master_id,
        Time.time == appointment_time,
        Time.status.is_(True)
    ).first()
    if not time_slot:
        raise ValueError("Time slot is not available.")
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