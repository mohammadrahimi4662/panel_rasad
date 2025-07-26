import requests
from bs4 import BeautifulSoup
from database import SessionLocal, News
import datetime
from dateutil import parser as date_parser
from urllib.parse import urlparse, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# تابع دریافت اخبار مهم از IRNA
def fetch_irna_top_news():
    url = 'https://www.irna.ir/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    news_list = []
    # پیدا کردن اخبار مهم (مثال: بخش تیترهای اصلی)
    for item in soup.select('div.top-news a')[:5]:  # فقط ۵ خبر اول
        title = item.get_text(strip=True)
        link = item['href']
        print(title)
        print(link)
        if not link.startswith('http'):
            link = 'https://www.irna.ir' + link
        today = datetime.datetime.utcnow()
        news_list.append({
            'title': title,
            'url': link,
            'agency': 'IRNA',
            'published_at': today,
            'summary': ''
        })
    return news_list

def fetch_isna_top_news():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.isna.ir/')
    # صبر کن تا حداقل یک خبر لود شود (تا 10 ثانیه)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.coverage, li.trans"))
        )
    except Exception as e:
        print("اخطار: هیچ خبری پیدا نشد یا صفحه کامل لود نشد:", e)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    news_list = []
    # سلکتور دقیق‌تر: فقط liهای داخل div.owl-item
    for div in soup.select('div.owl-item'):
        li = div.find('li', class_=['coverage', 'trans'])
        if not li:
            continue
        a_tag = li.select_one('div.desc h3 a')
        if a_tag:
            title = a_tag.get_text(strip=True)
            link = a_tag['href']
            if not link.startswith('http'):
                link = 'https://www.isna.ir' + link
            summary_tag = li.select_one('div.desc p')
            summary = summary_tag.get_text(strip=True) if summary_tag else ''
            today = datetime.datetime.utcnow()
            news_list.append({
                'title': title,
                'url': link,
                'agency': 'ISNA',
                'published_at': today,
                'summary': summary
            })
        if len(news_list) >= 10:
            break
    print("news_list:", news_list)
    return news_list

def fetch_bbc_persian_news():
    """
    دریافت اخبار از BBC فارسی
    """
    try:
        url = 'https://www.bbc.com/persian/topics/ckdxnwvwwjnt'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        
        # جستجوی اخبار در بخش‌های مختلف
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
                
                # پیدا کردن زمان انتشار
                parent = a_tag.find_parent('li') or a_tag.find_parent('article')
                time_tag = None
                if parent:
                    time_tag = parent.select_one('time')
                
                today = datetime.datetime.utcnow()
                published_at = today
                if time_tag and time_tag.has_attr('datetime'):
                    try:
                        dt = date_parser.parse(time_tag['datetime'])
                        published_at = dt
                    except Exception:
                        pass
                
                news_list.append({
                    'title': title,
                    'url': link,
                    'agency': 'BBC',
                    'published_at': published_at,
                    'summary': ''
                })
                
                if len(news_list) >= 10:
                    break
            if len(news_list) >= 10:
                break
        
        print(f"BBC news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار BBC: {e}")
        return []

def fetch_iranintl_news():
    """
    دریافت اخبار ایران اینترنشنال
    """
    try:
        url = 'https://www.iranintl.com/iran'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        today = datetime.datetime.utcnow()

        # جستجوی اخبار در بخش‌های مختلف
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
                
                # پیدا کردن لینک
                article = title_tag.find_parent('article')
                if not article:
                    continue
                    
                link_tag = article.select_one('a')
                if not link_tag:
                    continue
                    
                link = link_tag['href']
                if not link.startswith('http'):
                    link = 'https://www.iranintl.com' + link
                
                # پیدا کردن خلاصه
                summary_tag = article.select_one('p')
                summary = summary_tag.get_text(strip=True) if summary_tag else ''
                
                news_list.append({
                    'title': title,
                    'url': link,
                    'agency': 'IranIntl',
                    'published_at': today,
                    'summary': summary
                })
                
                if len(news_list) >= 10:
                    break
            if len(news_list) >= 10:
                break
        
        print(f"IranIntl news count: {len(news_list)}")
        return news_list
    except Exception as e:
        print(f"خطا در دریافت اخبار IranIntl: {e}")
        return []

def normalize_text(text):
    return text.strip().lower()

def normalize_url(url):
    parsed = urlparse(url)
    clean_url = urlunparse(parsed._replace(query=""))
    return clean_url.strip().lower()

# ذخیره اخبار در پایگاه داده
# بهبود: بررسی تکراری بودن بر اساس title یا url و agency

def save_news(news_items):
    db = SessionLocal()
    for item in news_items:
        norm_title = normalize_text(item['title'])
        norm_url = normalize_url(item['url'])
        # بررسی تکراری بودن بر اساس هر دو (AND)
        exists = db.query(News).filter(
            News.title == norm_title,
            News.url == norm_url,
            News.agency == item['agency']
        ).first()
        if not exists:
            news = News(
                title=item['title'],  # ذخیره متن اصلی
                url=item['url'],      # ذخیره URL اصلی
                agency=item['agency'],
                published_at=item['published_at'],
                summary=item['summary']
            )
            db.add(news)
    db.commit()
    db.close()

if __name__ == "__main__":
    # irna_news = fetch_irna_top_news()
    isna_news = fetch_isna_top_news()
    bbc_news = fetch_bbc_persian_news()
    iranintl_news = fetch_iranintl_news()
    save_news(isna_news)
    save_news(bbc_news)
    save_news(iranintl_news)
    print("اخبار با موفقیت ذخیره شد.") 
    total_count = len(isna_news) + len(bbc_news) + len(iranintl_news)
    print(f"تعداد کل اخبار: {total_count}") 