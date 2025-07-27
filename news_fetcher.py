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
import openai
import os
import re

# تابع دریافت اخبار مهم از IRNA با خلاصه‌سازی هوشمند

def fetch_irna_top_news():
    url = 'https://www.irna.ir/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_list = []
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
            summary = extract_irna_content_with_summary(news_item['url'], news_item['title'])
        except Exception as e:
            print(f"خطا در استخراج محتوای IRNA: {e}")
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

def extract_irna_content(url):
    """استخراج محتوای اصلی خبر از IRNA"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_parts = []
        
        # جستجو در محتوای اصلی IRNA
        selectors = [
            'div.news-content p',
            'div.news-text p',
            'div.content p',
            'article p'
        ]
        
        for selector in selectors:
            paragraphs = soup.select(selector)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 1000:
                    content_parts.append(text)
                if len(content_parts) >= 5:
                    break
            if len(content_parts) >= 5:
                break
        
        # ترکیب محتوا
        if content_parts:
            full_content = ' '.join(content_parts)
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            return full_content
        else:
            return ""
            
    except Exception as e:
        print(f"خطا در استخراج محتوای IRNA: {e}")
        return ""

def extract_irna_content_with_summary(url, title):
    """استخراج محتوای IRNA و خلاصه‌سازی با ChatGPT"""
    content = extract_irna_content(url)
    if content:
        # IRNA روتیتر ندارد، از ChatGPT استفاده کن
        return get_chatgpt_summary(content, title)
    return ""

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
                # استخراج محتوای اصلی خبر
                summary = extract_bbc_content_with_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در استخراج محتوای BBC: {e}")
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

def extract_bbc_content(url):
    """استخراج محتوای اصلی خبر از BBC"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # استخراج محتوای اصلی با کلاس‌های مشخص شده
        content_parts = []
        
        # جستجو در div با کلاس bbc-4wucq3 ebmt73l0
        main_content_divs = soup.find_all('div', class_='bbc-4wucq3 ebmt73l0')
        for div in main_content_divs:
            # جستجو در p با کلاس bbc-1gjryo4 e17g058b0
            paragraphs = div.find_all('p', class_='bbc-1gjryo4 e17g058b0')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # فقط متن‌های معنادار
                    content_parts.append(text)
        
        # اگر محتوای اصلی پیدا نشد، از روش جایگزین استفاده کن
        if not content_parts:
            # جستجو در تمام p های موجود
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 50 and len(text) < 1000:  # متن‌های متوسط
                    content_parts.append(text)
                if len(content_parts) >= 5:  # حداکثر 5 پاراگراف
                    break
        
        # ترکیب محتوا
        if content_parts:
            full_content = ' '.join(content_parts)
            # کوتاه کردن اگر خیلی طولانی باشد
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            return full_content
        else:
            return ""
            
    except Exception as e:
        print(f"خطا در استخراج محتوای BBC: {e}")
        return ""

def extract_bbc_content_with_summary(url, title):
    """استخراج محتوای BBC و خلاصه‌سازی با ChatGPT"""
    content = extract_bbc_content(url)
    if content:
        # BBC روتیتر ندارد، از ChatGPT استفاده کن
        return get_chatgpt_summary(content, title)
    return ""

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
                summary = extract_iranintl_content_with_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در استخراج محتوای IranIntl: {e}")
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

def extract_iranintl_content(url):
    """استخراج محتوای اصلی خبر از IranIntl"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_parts = []
        lead_paragraph = ""
        
        # جستجو در محتوای اصلی IranIntl
        selectors = [
            'div.article-content p',
            'div.content p',
            'article p',
            'div.article-body p'
        ]
        
        # ابتدا به دنبال روتیتر (پاراگراف اول) بگرد
        for selector in selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                # پاراگراف اول معمولاً روتیتر است
                lead_text = paragraphs[0].get_text(strip=True)
                if lead_text and len(lead_text) > 50 and len(lead_text) < 300:
                    lead_paragraph = lead_text
                    print(f"✅ روتیتر IranIntl پیدا شد: {lead_text[:100]}...")
                    break
        
        # اگر روتیتر پیدا شد، آن را برگردان
        if lead_paragraph:
            return lead_paragraph
        
        # اگر روتیتر پیدا نشد، از ChatGPT استفاده کن
        for selector in selectors:
            paragraphs = soup.select(selector)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 1000:
                    content_parts.append(text)
                if len(content_parts) >= 5:
                    break
            if len(content_parts) >= 5:
                break
        
        # ترکیب محتوا
        if content_parts:
            full_content = ' '.join(content_parts)
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            return full_content
        else:
            return ""
            
    except Exception as e:
        print(f"خطا در استخراج محتوای IranIntl: {e}")
        return ""

def extract_iranintl_content_with_summary(url, title):
    """استخراج محتوای IranIntl و تشخیص روتیتر"""
    content = extract_iranintl_content(url)
    if content:
        # بررسی اینکه آیا این روتیتر است یا نه
        if len(content) < 300 and not content.endswith("..."):
            # احتمالاً روتیتر است
            print("✅ از روتیتر IranIntl استفاده می‌شود")
            return content
        else:
            # از ChatGPT استفاده کن
            print("🔄 از ChatGPT برای خلاصه‌سازی استفاده می‌شود")
            return get_chatgpt_summary(content, title)
    return ""

# تابع دریافت اخبار ISNA
def fetch_isna_news():
    try:
        url = 'https://www.isna.ir/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        summarizer = PersianSummarizer()
        all_news_items = []
        
        # انتخاب عناوین اخبار
        selectors = [
            'div.news-list h3 a',
            'div.top-news h3 a',
            'div.latest-news h3 a',
            'article h3 a'
        ]
        
        for selector in selectors:
            for a_tag in soup.select(selector):
                title = a_tag.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                link = a_tag['href']
                if not link.startswith('http'):
                    link = 'https://www.isna.ir' + link
                
                # حذف تکراری
                is_duplicate = False
                for existing in all_news_items:
                    if existing['title'] == title or existing['url'] == link:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    all_news_items.append({'title': title, 'url': link})
                if len(all_news_items) >= 10:
                    break
            if len(all_news_items) >= 10:
                break
        
        print(f"تعداد کل اخبار ISNA: {len(all_news_items)}")
        
        for i, news_item in enumerate(all_news_items):
            print(f"\nپردازش خبر ISNA {i+1}/{len(all_news_items)}: {news_item['title'][:50]}...")
            summary = ""
            try:
                summary = extract_isna_content_with_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در استخراج محتوای ISNA: {e}")
                summary = ""
            
            today = datetime.datetime.now(timezone.utc)
            news_list.append({
                'title': news_item['title'],
                'url': news_item['url'],
                'agency': 'ISNA',
                'published_at': today,
                'summary': summary
            })
            print(f"خبر ISNA {i+1} پردازش شد")
        
        print(f"\nISNA news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار ISNA: {e}")
        return []

# تابع دریافت اخبار تسنیم
def fetch_tasnim_news():
    try:
        url = 'https://www.tasnimnews.com/'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        summarizer = PersianSummarizer()
        all_news_items = []
        
        # انتخاب عناوین اخبار
        selectors = [
            'div.news-list h3 a',
            'div.top-news h3 a',
            'div.latest-news h3 a',
            'article h3 a',
            'div.news-item h3 a'
        ]
        
        for selector in selectors:
            for a_tag in soup.select(selector):
                title = a_tag.get_text(strip=True)
                if not title or len(title) < 10:
                    continue
                link = a_tag['href']
                if not link.startswith('http'):
                    link = 'https://www.tasnimnews.com' + link
                
                # حذف تکراری
                is_duplicate = False
                for existing in all_news_items:
                    if existing['title'] == title or existing['url'] == link:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    all_news_items.append({'title': title, 'url': link})
                if len(all_news_items) >= 10:
                    break
            if len(all_news_items) >= 10:
                break
        
        print(f"تعداد کل اخبار Tasnim: {len(all_news_items)}")
        
        for i, news_item in enumerate(all_news_items):
            print(f"\nپردازش خبر Tasnim {i+1}/{len(all_news_items)}: {news_item['title'][:50]}...")
            summary = ""
            try:
                summary = extract_tasnim_content_with_summary(news_item['url'], news_item['title'])
            except Exception as e:
                print(f"خطا در استخراج محتوای Tasnim: {e}")
                summary = ""
            
            today = datetime.datetime.now(timezone.utc)
            news_list.append({
                'title': news_item['title'],
                'url': news_item['url'],
                'agency': 'Tasnim',
                'published_at': today,
                'summary': summary
            })
            print(f"خبر Tasnim {i+1} پردازش شد")
        
        print(f"\nTasnim news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار Tasnim: {e}")
        return []

def extract_isna_content(url):
    """استخراج محتوای اصلی خبر از ISNA"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_parts = []
        
        # جستجو در محتوای اصلی ISNA
        selectors = [
            'div.news-content p',
            'div.news-text p',
            'div.content p',
            'article p',
            'div.news-body p'
        ]
        
        for selector in selectors:
            paragraphs = soup.select(selector)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 1000:
                    content_parts.append(text)
                if len(content_parts) >= 5:
                    break
            if len(content_parts) >= 5:
                break
        
        # ترکیب محتوا
        if content_parts:
            full_content = ' '.join(content_parts)
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            return full_content
        else:
            return ""
            
    except Exception as e:
        print(f"خطا در استخراج محتوای ISNA: {e}")
        return ""

def extract_isna_content_with_summary(url, title):
    """استخراج محتوای ISNA و خلاصه‌سازی با ChatGPT"""
    content = extract_isna_content(url)
    if content:
        # ISNA روتیتر ندارد، از ChatGPT استفاده کن
        return get_chatgpt_summary(content, title)
    return ""

def extract_tasnim_content(url):
    """استخراج محتوای اصلی خبر از Tasnim"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_parts = []
        
        # جستجو در محتوای اصلی Tasnim
        selectors = [
            'div.news-content p',
            'div.news-text p',
            'div.content p',
            'article p',
            'div.news-body p'
        ]
        
        for selector in selectors:
            paragraphs = soup.select(selector)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 30 and len(text) < 1000:
                    content_parts.append(text)
                if len(content_parts) >= 5:
                    break
            if len(content_parts) >= 5:
                break
        
        # ترکیب محتوا
        if content_parts:
            full_content = ' '.join(content_parts)
            if len(full_content) > 2000:
                full_content = full_content[:2000] + "..."
            return full_content
        else:
            return ""
            
    except Exception as e:
        print(f"خطا در استخراج محتوای Tasnim: {e}")
        return ""

def extract_tasnim_content_with_summary(url, title):
    """استخراج محتوای Tasnim و خلاصه‌سازی با ChatGPT"""
    content = extract_tasnim_content(url)
    if content:
        # Tasnim روتیتر ندارد، از ChatGPT استفاده کن
        return get_chatgpt_summary(content, title)
    return ""

def get_chatgpt_summary(text, title):
    """دریافت خلاصه از ChatGPT"""
    try:
        # تنظیم API key (اگر موجود باشد)
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️ OPENAI_API_KEY تنظیم نشده است. از متن کامل استفاده می‌شود.")
            return text[:500] + "..." if len(text) > 500 else text
        
        openai.api_key = api_key
        
        prompt = f"""
        عنوان خبر: {title}
        
        متن کامل خبر:
        {text}
        
        لطفاً این خبر را در یک پاراگراف کوتاه و معنادار خلاصه کنید. 
        خلاصه باید شامل نکات اصلی و مهم خبر باشد و به زبان فارسی نوشته شود.
        حداکثر 200 کلمه باشد.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "شما یک خبرنگار حرفه‌ای هستید که اخبار را خلاصه می‌کند."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
        
    except Exception as e:
        print(f"خطا در دریافت خلاصه از ChatGPT: {e}")
        # در صورت خطا، از متن کوتاه شده استفاده کن
        return text[:500] + "..." if len(text) > 500 else text

def normalize_text(text):
    """نرمال کردن متن برای مقایسه"""
    if not text:
        return ""
    # حذف کاراکترهای خاص و نرمال کردن
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
    
    all_news = []
    
    # دریافت اخبار IRNA
    try:
        irna_news = fetch_irna_top_news()
        if irna_news:
            save_news(irna_news)
            all_news.extend(irna_news)
        else:
            print("هیچ خبری از IRNA دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار IRNA: {e}")
    
    # دریافت اخبار BBC
    try:
        bbc_news = fetch_bbc_persian_news()
        if bbc_news:
            save_news(bbc_news)
            all_news.extend(bbc_news)
        else:
            print("هیچ خبری از BBC دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار BBC: {e}")
    
    # دریافت اخبار IranIntl
    try:
        iranintl_news = fetch_iranintl_news()
        if iranintl_news:
            save_news(iranintl_news)
            all_news.extend(iranintl_news)
        else:
            print("هیچ خبری از IranIntl دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار IranIntl: {e}")
    
    # دریافت اخبار ISNA
    try:
        isna_news = fetch_isna_news()
        if isna_news:
            save_news(isna_news)
            all_news.extend(isna_news)
        else:
            print("هیچ خبری از ISNA دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار ISNA: {e}")
    
    # دریافت اخبار Tasnim
    try:
        tasnim_news = fetch_tasnim_news()
        if tasnim_news:
            save_news(tasnim_news)
            all_news.extend(tasnim_news)
        else:
            print("هیچ خبری از Tasnim دریافت نشد")
    except Exception as e:
        print(f"خطا در پردازش اخبار Tasnim: {e}")
    
    # خلاصه نهایی
    agencies = {}
    for news in all_news:
        if news['agency'] not in agencies:
            agencies[news['agency']] = 0
        agencies[news['agency']] += 1
    
    print(f"\n📊 خلاصه نهایی:")
    for agency, count in agencies.items():
        print(f"  📰 {agency}: {count} خبر")
    
    print(f"\n✅ تعداد کل اخبار دریافت شده: {len(all_news)}")
    print("🎯 عملیات دریافت اخبار کامل شد.") 