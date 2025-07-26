from database import SessionLocal, News
from datetime import datetime
import jdatetime
import re

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

def generate_beautiful_news_html(day: str, output_path=None):
    """تولید HTML زیبا از اخبار با خلاصه"""
    if output_path is None:
        output_path = f"news_report_{day.replace('-', '_')}.html"
    
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
    
    # تبدیل تاریخ به شمسی
    jalali_date = jdatetime.datetime.fromgregorian(datetime=start_gregorian)
    month_names = {
        1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
        4: 'تیر', 5: 'مرداد', 6: 'شهریور',
        7: 'مهر', 8: 'آبان', 9: 'آذر',
        10: 'دی', 11: 'بهمن', 12: 'اسفند'
    }
    month_name = month_names.get(jalali_date.month, '')
    date_str = f"{jalali_date.day} {month_name} {jalali_date.year}"
    
    # گروه‌بندی اخبار بر اساس آژانس
    agencies = {}
    for news in news_list:
        if news.agency not in agencies:
            agencies[news.agency] = []
        agencies[news.agency].append(news)
    
    # تولید HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>گزارش اخبار روزانه - {date_str}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Vazirmatn', Tahoma, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f8f9fa;
            padding: 20px;
        }}
        
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .header .date {{
            font-size: 18px;
            opacity: 0.9;
        }}
        
        .summary-section {{
            background: #e3f2fd;
            padding: 25px;
            margin: 20px;
            border-radius: 8px;
            border-right: 5px solid #2196f3;
        }}
        
        .summary-title {{
            font-size: 20px;
            font-weight: 600;
            color: #1976d2;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }}
        
        .summary-content {{
            font-size: 14px;
            line-height: 1.8;
            white-space: pre-line;
        }}
        
        .agency-section {{
            margin: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .agency-header {{
            background: #4caf50;
            color: white;
            padding: 15px 20px;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
        }}
        
        .news-list {{
            padding: 0;
        }}
        
        .news-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            transition: background-color 0.2s;
        }}
        
        .news-item:hover {{
            background-color: #f8f9fa;
        }}
        
        .news-item:last-child {{
            border-bottom: none;
        }}
        
        .news-title {{
            font-size: 16px;
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 8px;
            line-height: 1.5;
        }}
        
        .news-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: #666;
            margin-top: 8px;
        }}
        
        .news-time {{
            background: #f1f3f4;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .news-link {{
            color: #2196f3;
            text-decoration: none;
            font-weight: 500;
        }}
        
        .news-link:hover {{
            text-decoration: underline;
        }}
        
        .news-summary {{
            font-size: 13px;
            color: #555;
            margin-top: 8px;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            border-right: 3px solid #e0e0e0;
        }}
        
        .stats-section {{
            background: #f5f5f5;
            padding: 20px;
            margin: 20px;
            border-radius: 8px;
        }}
        
        .stats-title {{
            font-size: 20px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .stats-table th {{
            background: #2196f3;
            color: white;
            padding: 12px;
            text-align: center;
            font-weight: 600;
        }}
        
        .stats-table td {{
            padding: 12px;
            text-align: center;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .stats-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
                border-radius: 0;
            }}
            
            .news-item:hover {{
                background-color: white;
            }}
            
            .news-link {{
                color: #333;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 گزارش اخبار روزانه</h1>
            <div class="date">تاریخ: {date_str}</div>
        </div>
"""
    
    if not news_list:
        html_content += """
        <div class="summary-section">
            <div class="summary-title">📋 خلاصه کلی اخبار</div>
            <div class="summary-content">هیچ خبری برای این روز ثبت نشده است.</div>
        </div>
"""
    else:
        # خلاصه کلی
        summary_text = generate_news_summary(news_list)
        html_content += f"""
        <div class="summary-section">
            <div class="summary-title">📋 خلاصه کلی اخبار</div>
            <div class="summary-content">{summary_text}</div>
        </div>
"""
        
        # اخبار تفصیلی بر اساس آژانس
        for agency, agency_news in agencies.items():
            html_content += f"""
        <div class="agency-section">
            <div class="agency-header">📰 {agency}</div>
            <div class="news-list">
"""
            
            for i, news in enumerate(agency_news):
                time_str = convert_to_jalali(news.published_at)
                summary_html = ""
                if news.summary:
                    summary_text = clean_text_for_summary(news.summary, 100)
                    summary_html = f'<div class="news-summary">📝 {summary_text}</div>'
                
                html_content += f"""
                <div class="news-item">
                    <div class="news-title">{i+1}. {news.title}</div>
                    {summary_html}
                    <div class="news-meta">
                        <span class="news-time">⏰ {time_str}</span>
                        <a href="{news.url}" target="_blank" class="news-link">🔗 مشاهده خبر</a>
                    </div>
                </div>
"""
            
            html_content += """
            </div>
        </div>
"""
        
        # آمار نهایی
        html_content += """
        <div class="stats-section">
            <div class="stats-title">📊 آمار نهایی</div>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>خبرگزاری</th>
                        <th>تعداد اخبار</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        for agency, agency_news in agencies.items():
            html_content += f"""
                    <tr>
                        <td>{agency}</td>
                        <td>{len(agency_news)}</td>
                    </tr>
"""
        
        html_content += """
                </tbody>
            </table>
        </div>
"""
    
    # فوتر
    current_time = datetime.now().strftime('%Y/%m/%d %H:%M')
    html_content += f"""
        <div class="footer">
            تولید شده در: {current_time}
        </div>
    </div>
    
    <script>
        // چاپ خودکار پس از لود صفحه
        window.onload = function() {{
            // setTimeout(() => {{
            //     window.print();
            // }}, 1000);
        }};
    </script>
</body>
</html>
"""
    
    # ذخیره فایل HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path

def generate_news_html_for_today():
    """تولید HTML اخبار امروز"""
    today = jdatetime.datetime.now()
    day_str = f"{today.year}-{today.month:02d}-{today.day:02d}"
    return generate_beautiful_news_html(day_str)

if __name__ == "__main__":
    # تست تولید HTML برای امروز
    try:
        output_file = generate_news_html_for_today()
        print(f"HTML با موفقیت تولید شد: {output_file}")
    except Exception as e:
        print(f"خطا در تولید HTML: {e}") 