from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# پایگاه داده SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./panel_rasad.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# جدول اخبار خبرگزاری‌ها
class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)  # عنوان خبر
    url = Column(String)  # لینک خبر
    summary = Column(Text)  # خلاصه خبر
    agency = Column(String)  # خبرگزاری
    published_at = Column(DateTime, default=datetime.datetime.utcnow)  # زمان انتشار

# جدول پیام‌های تلگرام
class TelegramMessage(Base):
    __tablename__ = "telegram_messages"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, index=True)  # آیدی پیام
    text = Column(Text)  # متن پیام
    date = Column(DateTime, default=datetime.datetime.utcnow)  # زمان پیام

# ایجاد جداول
Base.metadata.create_all(bind=engine) 