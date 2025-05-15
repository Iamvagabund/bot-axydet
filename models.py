from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    display_name = Column(String)
    paid_trainings = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    registrations = relationship("TrainingRegistration", back_populates="user")

class Training(Base):
    __tablename__ = 'trainings'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    time = Column(String)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    registrations = relationship("TrainingRegistration", back_populates="training")

class TrainingRegistration(Base):
    __tablename__ = 'training_registrations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    training_id = Column(Integer, ForeignKey('trainings.id'))
    registered_at = Column(DateTime, default=datetime.utcnow)
    is_cancelled = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="registrations")
    training = relationship("Training", back_populates="registrations")

# Створюємо таблиці
Base.metadata.create_all(engine) 