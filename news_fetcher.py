import requests
from bs4 import BeautifulSoup
from database import SessionLocal, News
import datetime
from datetime import timezone
from dateutil import parser as date_parser
from urllib.parse import urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from persian_summarizer import PersianSummarizer

# تابع دریافت اخبار مهم از IRNA با خلاصه‌سازی هوشمند

def fetch_irna_top_news():
    url = 'https://www.irna.ir/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_list = []
    summarizer = PersianSummarizer()
    all_news_items = []
    for item in soup.select('div.top-news a')[:10]:
        title = item.get_text(strip=True)
        link = item['href']
        if not link.startswith('http'):
            link = 'https://www.irna.ir' + link
        # حذف تکراری
        is_duplicate = False
        for existing in all_news_items:
            if existing['title'] == title or existing['url'] == link:
                is_duplicate = True
                break
        if not is_duplicate:
            all_news_items.append({'title': title, 'url': link})
    print(f"تعداد کل اخبار IRNA: {len(all_news_items)}")
    for i, news_item in enumerate(all_news_items):
        print(f"\nپردازش خبر IRNA {i+1}/{len(all_news_items)}: {news_item['title'][:50]}...")
        summary = ""
        try:
            summary = summarizer.get_news_summary(news_item['url'], news_item['title'])
        except Exception as e:
            print(f"خطا در خلاصه‌سازی IRNA: {e}")
            summary = ""
        today = datetime.datetime.now(timezone.utc)
        news_list.append({
            'title': news_item['title'],
            'url': news_item['url'],
            'agency': 'IRNA',
            'published_at': today,
            'summary': summary
        })
        print(f"خبر IRNA {i+1} پردازش شد")
    print(f"\nIRNA news count: {len(news_list)}")
    return news_list

# تابع دریافت اخبار BBC فارسی با خلاصه‌سازی هوشمند

def fetch_bbc_persian_news():
    try:
        url = 'https://www.bbc.com/persian/topics/ckdxnwvwwjnt'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        summarizer = PersianSummarizer()
        all_news_items = []
        selectors = [
            'ul[data-testid="topic-promos"] > li h2 a',
            'article h2 a',
            'div[data-testid="card-headline"] a'
        ]
        for selector in selectors:
            for a_tag in soup.select(selector):
                title = a_tag.get_text(strip=True)
                if not title:
                    continue
                link = a_tag['href']
                if not link.startswith('http'):
                    link = 'https://www.bbc.com' + link
                is_duplicate = False
                for existing in all_news_items:
                    if existing['title'] == title or existing['url'] == link:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    all_news_items.append({'title': title, 'url': link})
                if len(all_news_items) >= 15:
                    break
            if len(all_news_items) >= 15:
                break
        print(f"تعداد کل اخبار BBC: {len(all_news_items)}")
        for i, news_item in enumerate(all_news_items):
            print(f"\nپردازش خبر BBC {i+1}/{len(all_news_items)}: {news_item['title'][:50]}...")
            summary = ""
            try:
                summary = summarizer.get_news_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در خلاصه‌سازی BBC: {e}")
                summary = ""
            today = datetime.datetime.now(timezone.utc)
            news_list.append({
                'title': news_item['title'],
                'url': news_item['url'],
                'agency': 'BBC',
                'published_at': today,
                'summary': summary
            })
            print(f"خبر BBC {i+1} پردازش شد")
        print(f"\nBBC news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار BBC: {e}")
        return []

# تابع دریافت اخبار ایران اینترنشنال با خلاصه‌سازی هوشمند

def fetch_iranintl_news():
    try:
        url = 'https://www.iranintl.com/iran'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        summarizer = PersianSummarizer()
        all_news_items = []
        selectors = [
            'article h3',
            'div.TopicCluster-module-scss-module__RZ03fG__featured article h3',
            'div.TopicCluster-module-scss-module__RZ03fG__additionalItem article h3',
            'div.topic__grid__item article h3'
        ]
        for selector in selectors:
            for title_tag in soup.select(selector):
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                if not title:
                    continue
                article = title_tag.find_parent('article')
                if not article:
                    continue
                link_tag = article.select_one('a')
                if not link_tag:
                    continue
                link = link_tag['href']
                if not link.startswith('http'):
                    link = 'https://www.iranintl.com' + link
                is_duplicate = False
                for existing in all_news_items:
                    if existing['title'] == title or existing['url'] == link:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    all_news_items.append({'title': title, 'url': link})
                if len(all_news_items) >= 15:
                    break
            if len(all_news_items) >= 15:
                break
        print(f"تعداد کل اخبار IranIntl: {len(all_news_items)}")
        for i, news_item in enumerate(all_news_items):
            print(f"\nپردازش خبر IranIntl {i+1}/{len(all_news_items)}: {news_item['title'][:50]}...")
            summary = ""
            try:
                summary = summarizer.get_news_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در خلاصه‌سازی IranIntl: {e}")
                summary = ""
            today = datetime.datetime.now(timezone.utc)
            news_list.append({
                'title': news_item['title'],
                'url': news_item['url'],
                'agency': 'IranIntl',
                'published_at': today,
                'summary': summary
            })
            print(f"خبر IranIntl {i+1} پردازش شد")
        print(f"\nIranIntl news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار IranIntl: {e}")
        return []

def normalize_text(text):
    """نرمال کردن متن برای مقایسه"""
    if not text:
        return ""
    # حذف کاراکترهای خاص و نرمال کردن
    import re
    text = text.strip().lower()
    text = re.sub(r'[^\w\s]', '', text)  # حذف علائم نگارشی
    text = re.sub(r'\s+', ' ', text)     # تبدیل چندین فاصله به یک فاصله
    return text

def normalize_url(url):
    """نرمال کردن URL برای مقایسه"""
    parsed = urlparse(url)
    clean_url = urlunparse(parsed._replace(query=""))
    return clean_url.strip().lower()

def is_similar_title(title1, title2, threshold=0.8):
    """بررسی شباهت دو عنوان با استفاده از الگوریتم ساده"""
    from difflib import SequenceMatcher
    
    norm1 = normalize_text(title1)
    norm2 = normalize_text(title2)
    
    if not norm1 or not norm2:
        return False
    
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    return similarity >= threshold

# ذخیره اخبار در پایگاه داده
# بهبود: بررسی تکراری بودن بر اساس title یا url و agency

def save_news(news_items):
    db = SessionLocal()
    try:
        added_count = 0
        for item in news_items:
            # بررسی تکراری بودن بر اساس عنوان مشابه و آژانس
            existing_news = db.query(News).filter(News.agency == item['agency']).all()
            
            is_duplicate = False
            for existing in existing_news:
                if is_similar_title(item['title'], existing.title):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                news = News(
                    title=item['title'],  # ذخیره متن اصلی
                    url=item['url'],      # ذخیره URL اصلی
                    agency=item['agency'],
                    published_at=item['published_at'],
                    summary=item['summary']
                )
                db.add(news)
                added_count += 1
                print(f"خبر جدید اضافه شد: {item['title'][:50]}...")
            else:
                print(f"خبر تکراری نادیده گرفته شد: {item['title'][:50]}...")
        
        db.commit()
        print(f"تعداد {added_count} خبر جدید از {len(news_items)} خبر اضافه شد")
    except Exception as e:
        print(f"خطا در ذخیره اخبار: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("شروع دریافت اخبار...")
    
    # irna_news = fetch_irna_top_news()
    
    try:
        isna_news = fetch_irna_top_news()
        if isna_news:
            save_news(isna_news)
        else:
            print("هیچ خبری از IRNA دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار IRNA: {e}")
        isna_news = []
    
    try:
        bbc_news = fetch_bbc_persian_news()
        if bbc_news:
            save_news(bbc_news)
        else:
            print("هیچ خبری از BBC دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار BBC: {e}")
        bbc_news = []
    
    try:
        iranintl_news = fetch_iranintl_news()
        if iranintl_news:
            save_news(iranintl_news)
        else:
            print("هیچ خبری از IranIntl دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار IranIntl: {e}")
        iranintl_news = []
    
    total_count = len(isna_news) + len(bbc_news) + len(iranintl_news)
    print(f"تعداد کل اخبار دریافت شده: {total_count}")
    print("عملیات دریافت اخبار کامل شد.") 