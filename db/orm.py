from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, TIMESTAMP, Numeric
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Client(Base):
    __tablename__ = 'clients'
    client_id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    time_registered = Column(TIMESTAMP, nullable=False)

    appointments = relationship("Appointment", back_populates="client")
    notifications = relationship("Notification", back_populates="client")


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    role = Column(Text, nullable=False)
    telegram_id = Column(Integer, nullable=True)


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    cost = Column(Numeric, nullable=False)

    appointments = relationship("Appointment", back_populates="service")


class Master(Base):
    __tablename__ = 'master_id'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)

    services = relationship("MasterService", back_populates="master")
    times = relationship("Time", back_populates="master")
    appointments = relationship("Appointment", back_populates="master")


class MasterService(Base):
    __tablename__ = 'master_services'
    master_id = Column(Integer, ForeignKey('master_id.id'), primary_key=True)
    service_id = Column(Integer, ForeignKey('services.id'), primary_key=True)

    master = relationship("Master", back_populates="services")
    service = relationship("Service")


class Time(Base):
    __tablename__ = 'times'
    time = Column(TIMESTAMP, nullable=False)
    master_id = Column(Integer, ForeignKey('master_id.id'), primary_key=True)
    status = Column(Boolean, nullable=False)

    master = relationship("Master", back_populates="times")


class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    master_id = Column(Integer, ForeignKey('master_id.id'), nullable=False)
    appointment_time = Column(TIMESTAMP, nullable=False)
    status = Column(Integer, nullable=False)

    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    master = relationship("Master", back_populates="appointments")


class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.client_id'), nullable=False)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=False)
    message = Column(Text, nullable=False)
    time_notify = Column(TIMESTAMP, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)

    client = relationship("Client", back_populates="notifications")
