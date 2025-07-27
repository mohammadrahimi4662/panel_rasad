from database import SessionLocal, News
from datetime import datetime, timedelta
import jdatetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import re
import os

# ثبت فونت فارسی
def register_persian_font():
    """ثبت فونت فارسی برای PDF"""
    try:
        # بررسی وجود فایل فونت
        font_path = "Vazirmatn.ttf"
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Vazirmatn', font_path))
            print("✅ فونت Vazirmatn با موفقیت ثبت شد")
            return 'Vazirmatn'
        else:
            print("⚠️ فایل فونت Vazirmatn.ttf یافت نشد. تلاش برای دانلود...")
            # دانلود فونت
            import urllib.request
            try:
                urllib.request.urlretrieve(
                    "https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/Vazirmatn-Regular.ttf",
                    "Vazirmatn.ttf"
                )
                pdfmetrics.registerFont(TTFont('Vazirmatn', 'Vazirmatn.ttf'))
                print("✅ فونت Vazirmatn دانلود و ثبت شد")
                return 'Vazirmatn'
            except:
                print("❌ دانلود فونت ناموفق بود. استفاده از فونت جایگزین...")
                # استفاده از فونت جایگزین
                try:
                    # تلاش برای استفاده از فونت‌های سیستم
                    pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
                    return 'Arial'
                except:
                    print("⚠️ استفاده از فونت پیش‌فرض Helvetica")
                    return 'Helvetica'
    except Exception as e:
        print(f"❌ خطا در ثبت فونت: {e}")
        return 'Helvetica'

def convert_to_jalali(date_obj):
    """تبدیل تاریخ میلادی به شمسی"""
    if isinstance(date_obj, str):
        date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
    jalali = jdatetime.datetime.fromgregorian(datetime=date_obj)
    return f"{jalali.year}/{jalali.month:02d}/{jalali.day:02d}"

def clean_text_for_summary(text, max_length=150):
    """پاک کردن متن و ایجاد خلاصه"""
    if not text:
        return ""
    
    # حذف کاراکترهای خاص و نرمال کردن
    text = re.sub(r'[^\u0600-\u06FF\w\s]', '', text)  # فقط حروف فارسی، انگلیسی و فاصله
    text = re.sub(r'\s+', ' ', text).strip()  # تبدیل چندین فاصله به یک فاصله
    
    # کوتاه کردن متن
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text

def generate_news_summary(news_list):
    """تولید خلاصه از اخبار"""
    if not news_list:
        return "هیچ خبری برای خلاصه‌سازی موجود نیست."
    
    # گروه‌بندی بر اساس آژانس
    agencies = {}
    for news in news_list:
        if news.agency not in agencies:
            agencies[news.agency] = []
        agencies[news.agency].append(news)
    
    summary_parts = []
    
    for agency, agency_news in agencies.items():
        summary_parts.append(f"📰 {agency}: {len(agency_news)} خبر")
        
        # خلاصه 3 خبر مهم هر آژانس
        for i, news in enumerate(agency_news[:3]):
            clean_title = clean_text_for_summary(news.title, 80)
            summary_parts.append(f"  • {clean_title}")
        
        if len(agency_news) > 3:
            summary_parts.append(f"  ... و {len(agency_news) - 3} خبر دیگر")
    
    return "\n".join(summary_parts)

def generate_beautiful_news_pdf(day: str, output_path=None):
    """تولید PDF زیبا از اخبار با خلاصه"""
    if output_path is None:
        output_path = f"news_report_{day.replace('-', '_')}.pdf"
    
    # ثبت فونت فارسی
    persian_font = register_persian_font()
    
    # تبدیل تاریخ شمسی به میلادی
    try:
        year, month, day_num = map(int, day.split('-'))
        jalali_start = jdatetime.datetime(year, month, day_num, 0, 0, 0)
        jalali_end = jalali_start.replace(hour=23, minute=59, second=59)
        start_gregorian = jalali_start.togregorian()
        end_gregorian = jalali_end.togregorian()
    except Exception as e:
        raise ValueError(f"خطا در تبدیل تاریخ: {e}")
    
    # دریافت اخبار
    db = SessionLocal()
    try:
        news_list = db.query(News).filter(
            News.published_at >= start_gregorian,
            News.published_at <= end_gregorian
        ).order_by(News.agency, News.published_at.asc()).all()
    finally:
        db.close()
    
    # ایجاد PDF
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                          rightMargin=30, leftMargin=30, 
                          topMargin=30, bottomMargin=30)
    story = []
    
    # استایل‌های زیبا
    styles = getSampleStyleSheet()
    
    # استایل عنوان اصلی
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        alignment=1,  # وسط
        textColor=colors.darkblue,
        fontName=persian_font
    )
    
    # استایل عنوان بخش
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        spaceBefore=20,
        textColor=colors.darkgreen,
        fontName=persian_font,
        borderWidth=1,
        borderColor=colors.darkgreen,
        borderPadding=10,
        backColor=colors.lightgreen
    )
    
    # استایل خلاصه
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=25,
        spaceBefore=15,
        alignment=0,  # راست
        fontName=persian_font,
        textColor=colors.darkblue,
        backColor=colors.lightblue,
        borderWidth=1,
        borderColor=colors.blue,
        borderPadding=15,
        leftIndent=20,
        rightIndent=20
    )
    
    # استایل خبر
    news_style = ParagraphStyle(
        'News',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=0,  # راست
        fontName=persian_font,
        leftIndent=20
    )
    
    # استایل زمان
    time_style = ParagraphStyle(
        'Time',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        fontName=persian_font
    )
    
    # عنوان اصلی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=start_gregorian)
    month_names = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
        4: 'تیر', 5: 'مرداد', 6: 'شهریور',
        7: 'مهر', 8: 'آبان', 9: 'آذر',
        10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }
    month_name = month_names.get(jalali_date.month, '')
    date_str = f"{jalali_date.day} {month_name} {jalali_date.year}"
    
    story.append(Paragraph(f"📰 گزارش اخبار روزانه", main_title_style))
    story.append(Paragraph(f"تاریخ: {date_str}", main_title_style))
    story.append(Spacer(1, 20))
    
    if not news_list:
        story.append(Paragraph("هیچ خبری برای این روز ثبت نشده است.", summary_style))
    else:
        # خلاصه کلی
        summary_text = generate_news_summary(news_list)
        story.append(Paragraph("📋 خلاصه کلی اخبار:", section_title_style))
        story.append(Paragraph(summary_text, summary_style))
        story.append(PageBreak())
        
        # اخبار تفصیلی بر اساس آژانس
        agencies = {}
        for news in news_list:
            if news.agency not in agencies:
                agencies[news.agency] = []
            agencies[news.agency].append(news)
        
        for agency, agency_news in agencies.items():
            story.append(Paragraph(f"📰 {agency}", section_title_style))
            
            for i, news in enumerate(agency_news):
                # عنوان خبر
                title_text = f"<b>{i+1}. {news.title}</b>"
                story.append(Paragraph(title_text, news_style))
                
                # زمان انتشار
                time_text = f"⏰ {convert_to_jalali(news.published_at)}"
                story.append(Paragraph(time_text, time_style))
                
                # خلاصه (اگر موجود باشد)
                if news.summary:
                    summary_text = clean_text_for_summary(news.summary, 100)
                    story.append(Paragraph(f"📝 {summary_text}", news_style))
                
                # لینک
                story.append(Paragraph(f"🔗 {news.url}", time_style))
                story.append(Spacer(1, 8))
        
        # آمار نهایی
        story.append(PageBreak())
        story.append(Paragraph("📊 آمار نهایی", section_title_style))
        
        stats_data = [["خبرگزاری", "تعداد اخبار"]]
        for agency, agency_news in agencies.items():
            stats_data.append([agency, str(len(agency_news))])
        
        stats_table = Table(stats_data, colWidths=[200, 100])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), persian_font),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('FONTSIZE', (0,1), (-1,-1), 11),
            ('FONTNAME', (0,1), (-1,-1), persian_font),
        ]))
        story.append(stats_table)
    
    # فوتر
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=1,  # وسط
        fontName=persian_font
    )
    story.append(Paragraph(f"تولید شده در: {datetime.now().strftime('%Y/%m/%d %H:%M')}", footer_style))
    
    # ساخت PDF
    doc.build(story)
    return output_path

def generate_news_pdf_for_today():
    """تولید PDF اخبار امروز"""
    today = jdatetime.datetime.now()
    day_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    return generate_beautiful_news_pdf(day_str)

if __name__ == "__main__":
    # تست تولید PDF برای امروز
    try:
        output_file = generate_news_pdf_for_today()
        print(f"PDF با موفقیت تولید شد: {output_file}")
    except Exception as e:
        print(f"خطا در تولید PDF: {e}") 