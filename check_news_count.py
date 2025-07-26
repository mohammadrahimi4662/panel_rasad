from database import SessionLocal, News
from sqlalchemy import func

def check_news_count():
    db = SessionLocal()
    try:
        # تعداد کل اخبار
        total_count = db.query(News).count()
        print(f"📊 تعداد کل اخبار: {total_count}")
        
        # تعداد اخبار بر اساس آژانس
        agency_counts = db.query(News.agency, func.count(News.id)).group_by(News.agency).all()
        print("\n📰 تعداد اخبار بر اساس آژانس:")
        for agency, count in agency_counts:
            print(f"  {agency}: {count} خبر")
        
        # جدیدترین اخبار
        latest_news = db.query(News).order_by(News.published_at.desc()).limit(5).all()
        print(f"\n🆕 جدیدترین اخبار:")
        for news in latest_news:
            print(f"  {news.agency}: {news.title[:50]}...")
            
    except Exception as e:
        print(f"خطا: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_news_count() 