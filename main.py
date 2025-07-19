from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from database import SessionLocal, News, TelegramMessage
from datetime import datetime
from news_fetcher import fetch_isna_top_news, save_news
from dateutil import parser as date_parser

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

@app.get('/', response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "message": "به پنل خبر خوش آمدید!"})

@app.get('/news', response_class=HTMLResponse)
def news_page(request: Request):
    db = SessionLocal()
    news_list = db.query(News).order_by(News.published_at.desc()).all()
    db.close()
    return templates.TemplateResponse('news.html', {
        "request": request,
        "news_list": news_list,
        "active_page": "news"
    })

@app.get('/telegram', response_class=HTMLResponse)
def telegram_page(request: Request):
    db = SessionLocal()
    telegram_list = db.query(TelegramMessage).order_by(TelegramMessage.date.desc()).all()
    db.close()
    return templates.TemplateResponse('telegram.html', {
        "request": request,
        "telegram_list": telegram_list,
        "active_page": "telegram"
    })

@app.get('/highlights', response_class=HTMLResponse)
def highlights_page(request: Request):
    highlights_list = []
    return templates.TemplateResponse('highlights.html', {
        "request": request,
        "highlights_list": highlights_list,
        "active_page": "highlights"
    })

def fetch_and_save_all_news():
    try:
        isna_news = fetch_isna_top_news()
        save_news(isna_news)
    except Exception as e:
        print("خطا در دریافت یا ذخیره اخبار ایسنا:", e)

fetch_and_save_all_news()

print("شروع تست دریافت اخبار ایسنا...")

from news_fetcher import fetch_isna_top_news

print("تابع ایمپورت شد.")

if __name__ == "__main__":
    print("شروع اجرای تابع fetch_isna_top_news ...")
    try:
        news = fetch_isna_top_news()
        print("تابع اجرا شد.")
        print("تعداد خبر دریافت شده:", len(news))
        for item in news:
            print(item)
    except Exception as e:
        print("خطا در دریافت اخبار:", e) 