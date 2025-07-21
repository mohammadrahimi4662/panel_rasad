import requests
from bs4 import BeautifulSoup
from database import SessionLocal, News
import datetime
import feedparser
from dateutil import parser as date_parser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urlparse, urlunparse

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
        news_list.append({
            'title': title,
            'url': link,
            'agency': 'IRNA',
            'published_at': datetime.datetime.utcnow(),
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
            news_list.append({
                'title': title,
                'url': link,
                'agency': 'ISNA',
                'published_at': datetime.datetime.utcnow(),
                'summary': summary
            })
        if len(news_list) >= 10:
            break
    print("news_list:", news_list)
    return news_list

def fetch_bbc_persian_news():
    """
    دریافت اخبار از BBC فارسی (https://www.bbc.com/persian/topics/ckdxnwvwwjnt) با Selenium و اسکرول خودکار
    خروجی: لیست دیکشنری با کلیدهای title, url, agency, published_at, summary
    """
    url = 'https://www.bbc.com/persian/topics/ckdxnwvwwjnt'
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(3)

    # اسکرول خودکار تا انتهای صفحه برای لود شدن همه خبرها
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(15):  # تعداد دفعات اسکرول را می‌توانی بیشتر یا کمتر کنی
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    news_list = []
    for li in soup.select('ul[data-testid="topic-promos"] > li'):
        a_tag = li.select_one('h2 a')
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        link = a_tag['href']
        if not link.startswith('http'):
            link = 'https://www.bbc.com' + link
        summary = ''
        time_tag = li.select_one('time')
        published_at = datetime.datetime.utcnow()
        if time_tag and time_tag.has_attr('datetime'):
            try:
                published_at = date_parser.parse(time_tag['datetime'])
            except Exception:
                pass
        news_list.append({
            'title': title,
            'url': link,
            'agency': 'BBC',
            'published_at': published_at,
            'summary': summary
        })
    driver.quit()
    return news_list

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
                title=norm_title,
                url=norm_url,
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
    save_news(isna_news)
    print("اخبار با موفقیت ذخیره شد.") 