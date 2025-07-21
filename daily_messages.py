from database import SessionLocal, DailyMessage
from datetime import datetime, timedelta
import jdatetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
import os

def create_daily_message(title, content, category="عمومی", priority=1):
    """ایجاد پیام روزانه جدید"""
    db = SessionLocal()
    try:
        message = DailyMessage(
            title=title,
            content=content,
            category=category,
            priority=priority
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_daily_messages(category=None, limit=None):
    """دریافت پیام‌های روزانه"""
    db = SessionLocal()
    try:
        query = db.query(DailyMessage).order_by(DailyMessage.priority.desc(), DailyMessage.created_at.desc())
        if category:
            query = query.filter(DailyMessage.category == category)
        if limit:
            query = query.limit(limit)
        return query.all()
    finally:
        db.close()

def get_today_messages():
    """دریافت پیام‌های امروز"""
    db = SessionLocal()
    try:
        today = datetime.now().date()
        return db.query(DailyMessage).filter(
            DailyMessage.created_at >= today
        ).order_by(DailyMessage.priority.desc(), DailyMessage.created_at.desc()).all()
    finally:
        db.close()

def generate_daily_pdf(date=None, output_path="daily_report.pdf"):
    """تولید PDF از پیام‌های روزانه"""
    if date is None:
        date = datetime.now()
    
    # دریافت پیام‌های روز
    db = SessionLocal()
    try:
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        messages = db.query(DailyMessage).filter(
            DailyMessage.created_at >= start_date,
            DailyMessage.created_at < end_date
        ).order_by(DailyMessage.priority.desc(), DailyMessage.created_at.desc()).all()
    finally:
        db.close()
    
    # تبدیل تاریخ به شمسی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=date)
    month_names = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
        4: 'تیر', 5: 'مرداد', 6: 'شهریور',
        7: 'مهر', 8: 'آبان', 9: 'آذر',
        10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }
    month_name = month_names.get(jalali_date.month, '')
    date_str = f"{jalali_date.day} {month_name} {jalali_date.year}"
    
    # ایجاد PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []
    
    # استایل‌ها
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # وسط
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.darkblue
    )
    
    content_style = ParagraphStyle(
        'CustomContent',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=15,
        alignment=0  # راست
    )
    
    # عنوان اصلی
    story.append(Paragraph(f"گزارش روزانه - {date_str}", title_style))
    story.append(Spacer(1, 20))
    
    if not messages:
        story.append(Paragraph("هیچ پیامی برای این روز ثبت نشده است.", content_style))
    else:
        # گروه‌بندی بر اساس دسته‌بندی
        categories = {}
        for msg in messages:
            if msg.category not in categories:
                categories[msg.category] = []
            categories[msg.category].append(msg)
        
        for category, category_messages in categories.items():
            story.append(Paragraph(f"دسته‌بندی: {category}", subtitle_style))
            
            for msg in category_messages:
                # اولویت
                priority_stars = "⭐" * msg.priority
                story.append(Paragraph(f"<b>عنوان:</b> {msg.title} {priority_stars}", content_style))
                story.append(Paragraph(f"<b>محتوا:</b> {msg.content}", content_style))
                story.append(Spacer(1, 10))
    
    # فوتر
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"تولید شده در: {date_str}", styles['Normal']))
    
    doc.build(story)
    return output_path

def generate_html_report(date=None):
    """تولید HTML برای نمایش در وب"""
    if date is None:
        date = datetime.now()
    
    db = SessionLocal()
    try:
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        messages = db.query(DailyMessage).filter(
            DailyMessage.created_at >= start_date,
            DailyMessage.created_at < end_date
        ).order_by(DailyMessage.priority.desc(), DailyMessage.created_at.desc()).all()
    finally:
        db.close()
    
    # تبدیل تاریخ به شمسی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=date)
    month_names = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
        4: 'تیر', 5: 'مرداد', 6: 'شهریور',
        7: 'مهر', 8: 'آبان', 9: 'آذر',
        10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }
    month_name = month_names.get(jalali_date.month, '')
    date_str = f"{jalali_date.day} {month_name} {jalali_date.year}"
    
    return {
        'date': date_str,
        'messages': messages,
        'total_count': len(messages)
    }

# مثال استفاده
if __name__ == "__main__":
    # ایجاد چند پیام نمونه
    create_daily_message(
        "وضعیت اقتصادی کشور",
        "بر اساس آخرین گزارش‌ها، شاخص‌های اقتصادی کشور در حال بهبود است.",
        "اقتصادی",
        4
    )
    
    create_daily_message(
        "اخبار ورزشی",
        "تیم ملی فوتبال در بازی دیروز پیروز شد.",
        "ورزشی",
        3
    )
    
    # تولید PDF
    generate_daily_pdf(output_path="daily_report.pdf")
    print("PDF با موفقیت تولید شد!") 