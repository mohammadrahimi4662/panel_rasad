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



# ذخیره اخبار در پایگاه داده
def save_news(news_items):
    db = SessionLocal()
    for item in news_items:
        # بررسی تکراری نبودن خبر بر اساس عنوان و خبرگزاری
        exists = db.query(News).filter_by(title=item['title'], agency=item['agency']).first()
        if not exists:
            news = News(
                title=item['title'],
                url=item['url'],
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