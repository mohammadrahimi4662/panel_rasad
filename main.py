from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from database import SessionLocal, News, TelegramMessage
from datetime import datetime
from news_fetcher import fetch_irna_top_news, save_news, fetch_bbc_persian_news, fetch_iranintl_news
from dateutil import parser as date_parser
import jdatetime
from fastapi.responses import FileResponse, StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io
from news_pdf_generator import generate_beautiful_news_pdf
from beautiful_news_html import generate_beautiful_news_html

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

def convert_to_jalali(date_obj):
    """تبدیل تاریخ میلادی به شمسی (فقط تاریخ)"""
    if date_obj:
        jalali_date = jdatetime.datetime.fromgregorian(datetime=date_obj)
        month_names = {
            1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
            4: 'تیر', 5: 'مرداد', 6: 'شهریور',
            7: 'مهر', 8: 'آبان', 9: 'آذر',
            10: 'دی', 11: 'بهمن', 12: 'اسفند'
        }
        month_name = month_names.get(jalali_date.month, '')
        return f"{jalali_date.day} {month_name} {jalali_date.year}"
    return ""

# اضافه کردن تابع تبدیل به context templates
templates.env.globals['jalali_date'] = convert_to_jalali

def group_news_by_day(news_list):
    grouped = {}
    for news in news_list:
        jalali = jdatetime.datetime.fromgregorian(datetime=news.published_at)
        day_key = f"{jalali.year}-{jalali.month:02d}-{jalali.day:02d}"
        if day_key not in grouped:
            grouped[day_key] = []
        grouped[day_key].append(news)
    return dict(sorted(grouped.items(), reverse=True))

@app.get('/', response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse('index.html', {"request": request, "message": "به پنل خبر خوش آمدید!"})

@app.get('/news', response_class=HTMLResponse)
def news_page(request: Request, agency: str = Query('all'), date_from: str = Query(None), date_to: str = Query(None), range: str = Query(None)):
    db = SessionLocal()
    news_query = db.query(News)
    # فیلتر بر اساس نوع خبرگزاری
    if agency == 'internal':
        news_query = news_query.filter(News.agency.in_(['IRNA', 'ISNA']))
    elif agency == 'external':
        news_query = news_query.filter(~News.agency.in_(['IRNA', 'ISNA']))
    # فیلتر بر اساس بازه تاریخ شمسی
    from_date = None
    to_date = None
    import jdatetime, datetime as dt
    today_jalali = jdatetime.date.today()
    if range:
        if range == 'today':
            from_date = to_date = today_jalali
        elif range == '10days':
            from_date = today_jalali - jdatetime.timedelta(days=10)
            to_date = today_jalali
        elif range == 'week':
            from_date = today_jalali - jdatetime.timedelta(days=today_jalali.weekday())
            to_date = today_jalali
        elif range == 'month':
            from_date = today_jalali.replace(day=1)
            to_date = today_jalali
        elif range == 'year':
            from_date = today_jalali.replace(month=1, day=1)
            to_date = today_jalali
    if date_from:
        try:
            y, m, d = map(int, date_from.split('-'))
            from_date = jdatetime.date(y, m, d)
        except Exception:
            pass
    if date_to:
        try:
            y, m, d = map(int, date_to.split('-'))
            to_date = jdatetime.date(y, m, d)
        except Exception:
            pass
    if from_date:
        start_gregorian = jdatetime.datetime(from_date.year, from_date.month, from_date.day, 0, 0, 0).togregorian()
        news_query = news_query.filter(News.published_at >= start_gregorian)
    if to_date:
        end_gregorian = jdatetime.datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59).togregorian()
        news_query = news_query.filter(News.published_at <= end_gregorian)
    news_list = news_query.order_by(News.published_at.desc()).all()
    db.close()
    grouped_news = group_news_by_day(news_list)
    return templates.TemplateResponse('news.html', {
        "request": request,
        "grouped_news": grouped_news,
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

@app.get('/fetch-news')
def fetch_news_endpoint():
    """API endpoint برای دریافت اخبار جدید"""
    try:
        isna_news = fetch_irna_top_news()
        bbc_news = fetch_bbc_persian_news()
        iranintl_news = fetch_iranintl_news()
        save_news(isna_news)
        save_news(bbc_news)
        save_news(iranintl_news)
        total_count = len(isna_news) + len(bbc_news) + len(iranintl_news)
        return {"message": "اخبار با موفقیت دریافت و ذخیره شد", "count": total_count}
    except Exception as e:
        return {"error": f"خطا در دریافت اخبار: {str(e)}"}

@app.get('/download-news-pdf')
def download_news_pdf(day: str):
    """دانلود PDF اخبار یک روز خاص"""
    import logging
    db = SessionLocal()
    try:
        try:
            year, month, day_num = map(int, day.split('-'))
            jalali_start = jdatetime.datetime(year, month, day_num, 0, 0, 0)
            jalali_end = jalali_start.replace(hour=23, minute=59, second=59)
            start_gregorian = jalali_start.togregorian()
            end_gregorian = jalali_end.togregorian()
        except Exception as e:
            logging.exception("خطا در تبدیل تاریخ day: %s", day)
            return HTMLResponse(f"پارامتر تاریخ اشتباه است: {day}", status_code=400)
        
        news_list = db.query(News).filter(
            News.published_at >= start_gregorian,
            News.published_at <= end_gregorian
        ).order_by(News.published_at.asc()).all()
    finally:
        db.close()
    
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=1, fontSize=16)
        normal_style = ParagraphStyle('normal', parent=styles['Normal'], fontSize=12)
        
        story = []
        story.append(Paragraph(f"اخبار روز {day.replace('-', '/')}" , title_style))
        story.append(Spacer(1, 12))
        
        if not news_list:
            story.append(Paragraph("هیچ خبری برای این روز ثبت نشده است.", normal_style))
        else:
            table_data = [["عنوان خبر", "خبرگزاری", "زمان انتشار", "لینک"]]
            for news in news_list:
                table_data.append([
                    news.title,
                    news.agency,
                    convert_to_jalali(news.published_at),
                    news.url
                ])
            
            table = Table(table_data, colWidths=[200, 80, 100, 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 12),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 1, colors.grey),
                ('FONTSIZE', (0,1), (-1,-1), 10),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            story.append(table)
        
        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type='application/pdf', headers={
            'Content-Disposition': f'attachment; filename=news_{day}.pdf'
        })
        
    except Exception as e:
        logging.exception("خطا در تولید PDF برای روز %s", day)
        return HTMLResponse(f"خطا در تولید PDF: {e}", status_code=500)

@app.get('/download-beautiful-news-pdf')
def download_beautiful_news_pdf(day: str):
    """دانلود PDF زیبا از اخبار یک روز خاص با خلاصه"""
    try:
        # تولید PDF زیبا
        output_path = generate_beautiful_news_pdf(day)
        
        # ارسال فایل
        return FileResponse(
            path=output_path,
            media_type='application/pdf',
            filename=f'beautiful_news_{day}.pdf'
        )
    except Exception as e:
        return HTMLResponse(f"خطا در تولید PDF زیبا: {e}", status_code=500)

@app.get('/download-beautiful-news-pdf-today')
def download_beautiful_news_pdf_today():
    """دانلود PDF زیبا از اخبار امروز"""
    try:
        today = jdatetime.datetime.now()
        day_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
        
        # تولید PDF زیبا
        output_path = generate_beautiful_news_pdf(day_str)
        
        # ارسال فایل
        return FileResponse(
            path=output_path,
            media_type='application/pdf',
            filename=f'beautiful_news_today.pdf'
        )
    except Exception as e:
        return HTMLResponse(f"خطا در تولید PDF زیبا: {e}", status_code=500)

@app.get('/beautiful-news-html')
def beautiful_news_html(day: str = None):
    """نمایش HTML زیبا از اخبار برای چاپ"""
    try:
        if day is None:
            today = jdatetime.datetime.now()
            day = f"{today.year}-{today.month:02d}-{today.day:02d}"
        
        # تولید HTML زیبا
        output_path = generate_beautiful_news_html(day)
        
        # خواندن محتوای HTML
        with open(output_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return HTMLResponse(html_content)
    except Exception as e:
        return HTMLResponse(f"خطا در تولید HTML زیبا: {e}", status_code=500)

@app.get('/beautiful-news-html-today')
def beautiful_news_html_today():
    """نمایش HTML زیبا از اخبار امروز"""
    return beautiful_news_html()

@app.get('/api/news-by-day')
def get_news_by_day_api(day: str):
    """API برای دریافت اخبار یک روز خاص"""
    try:
        year, month, day_num = map(int, day.split('-'))
        jalali_start = jdatetime.datetime(year, month, day_num, 0, 0, 0)
        jalali_end = jalali_start.replace(hour=23, minute=59, second=59)
        start_gregorian = jalali_start.togregorian()
        end_gregorian = jalali_end.togregorian()
        
        db = SessionLocal()
        news_list = db.query(News).filter(
            News.published_at >= start_gregorian,
            News.published_at <= end_gregorian
        ).order_by(News.published_at.asc()).all()
        db.close()
        
        return {"news": [
            {
                "title": news.title,
                "agency": news.agency,
                "published_at": convert_to_jalali(news.published_at),
                "url": news.url
            } for news in news_list
        ]}
    except Exception as e:
        return {"error": f"خطا در دریافت اخبار: {str(e)}"}

@app.post('/delete-news/{news_id}')
def delete_news(news_id: int):
    db = SessionLocal()
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        db.close()
        raise HTTPException(status_code=404, detail="خبر پیدا نشد")
    db.delete(news)
    db.commit()
    db.close()
    return {"message": "خبر با موفقیت حذف شد"}

if __name__ == "__main__":
    print("شروع سرور...")
    print("در حال دریافت اخبار جدید...")
    try:
        # دریافت اخبار جدید در ابتدای اجرا
        isna_news = fetch_irna_top_news()
        save_news(isna_news)
        print(f"تعداد {len(isna_news)} خبر جدید دریافت شد.")
    except Exception as e:
        print(f"خطا در دریافت اخبار: {e}")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True) 