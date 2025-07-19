from database import SessionLocal, News

# اتصال به دیتابیس و نمایش همه اخبار

def show_all_news():
    db = SessionLocal()
    news_list = db.query(News).all()
    if not news_list:
        print('هیچ خبری در دیتابیس ذخیره نشده است.')
    for news in news_list:
        print(f"عنوان: {news.title}")
        print(f"خبرگزاری: {news.agency}")
        print(f"تاریخ: {news.published_at}")
        print(f"لینک: {news.url}")
        print(f"خلاصه: {news.summary}")
        print('-'*40)
    db.close()

if __name__ == "__main__":
    show_all_news() 