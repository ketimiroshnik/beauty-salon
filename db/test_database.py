import pytest
from database_functions import *
from connection import *
from orm import *

@pytest.fixture(scope="function")
def session():
    """Создаем новую сессию для каждого теста"""
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def sample_data(session):
    """Дата для тестов"""
    service = Service(title="Стрижка", description="Мужская стрижка", cost=50)
    master = Master(name="Иван Иванов", description="Парикмахер", is_active=True)
    session.add_all([service, master])
    session.flush()
    master_service = MasterService(master_id=master.id, service_id=service.id)
    session.add(master_service)
    session.commit()

    return {
        "service_id": service.id,
        "master_id": master.id,
    }


def test_get_client_id_by_telegram_id(session):
    user = User(role="client", telegram_id=12345)
    client = Client(client_id=1, name="абоба", time_registered=datetime.now())
    session.add_all([user, client])
    session.commit()

    client_id = get_client_id_by_telegram_id(session, 12345)
    assert client_id == client.client_id

    client_id = get_client_id_by_telegram_id(session, 99989)
    assert client_id == None


def test_add_new_user(session):
    client_id = add_user(session, telegram_id=54321, name="абоба2")
    assert client_id is not None
    client = session.query(Client).filter_by(client_id=client_id).first()
    assert client is not None
    assert client.name == "абоба2"


def test_get_masters_for_service(session, sample_data):
    next_month = datetime.now() + timedelta(days=15)
    time_slot = Time(master_id=sample_data['master_id'], time=next_month, status=True)
    session.add(time_slot)
    session.commit()

    masters = get_masters_for_service(session, sample_data['service_id'])
    assert len(masters) == 1
    assert masters[0].name == "Иван Иванов"


def test_get_days_with_free_slots(session, sample_data):
    today = datetime.now()
    free_time = Time(master_id=sample_data['master_id'], time=today, status=True)
    session.add(free_time)
    session.commit()

    days = get_free_days_for_master(session, sample_data['master_id'])
    assert str(today.date()) in days


def test_get_timeslots_for_day_and_master(session, sample_data):
    today = datetime.now()
    time_slot = Time(master_id=sample_data['master_id'], time=today, status=True)
    session.add(time_slot)
    session.commit()

    slots = get_timeslots_for_day(session, sample_data['master_id'], today)
    assert len(slots) == 1
    assert slots[0].time == today


def test_create_appointment(session, sample_data):
    appointment_time = datetime.now()
    today = datetime.now()
    time_slot = Time(master_id=sample_data['master_id'], time=today, status=True)
    session.add(time_slot)
    session.commit()
    client = Client(client_id=1, name="абоба", time_registered=datetime.now())
    appointment_id = create_appointment(
        session, client_id=client.client_id, service_id=sample_data['service_id'],
        master_id=sample_data['master_id'], appointment_time=appointment_time
    )
    appointment = session.query(Appointment).filter_by(id=appointment_id).first()
    assert appointment is not None
    assert appointment.client_id == client.client_id
    time_slot = session.query(Time).filter_by(
        master_id=sample_data['master_id'], time=appointment_time
    ).first()
    assert time_slot.status is False
    try:
        appointment_id = create_appointment(
        session, client_id=client.client_id, service_id=sample_data['service_id'],
        master_id=sample_data['master_id'], appointment_time=appointment_time
    )
    except Exception as e:
        assert True