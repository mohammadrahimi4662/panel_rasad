import sys
import traceback

# تست import ها
try:
    print("تست import ها...")
    import requests
    print("✓ requests نصب شده")
    
    from bs4 import BeautifulSoup
    print("✓ beautifulsoup4 نصب شده")
    
    from database import SessionLocal, News
    print("✓ database import موفق")
    
    import datetime
    print("✓ datetime نصب شده")
    
    from dateutil import parser as date_parser
    print("✓ python-dateutil نصب شده")
    
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    print("✓ selenium نصب شده")
    
except Exception as e:
    print(f"❌ خطا در import: {e}")
    traceback.print_exc()
    sys.exit(1)

# تست اتصال به دیتابیس
try:
    print("\nتست اتصال به دیتابیس...")
    db = SessionLocal()
    result = db.query(News).first()
    print("✓ اتصال به دیتابیس موفق")
    db.close()
except Exception as e:
    print(f"❌ خطا در اتصال به دیتابیس: {e}")
    traceback.print_exc()

# تست Chrome driver
try:
    print("\nتست Chrome driver...")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    driver.quit()
    print("✓ Chrome driver کار می‌کند")
except Exception as e:
    print(f"❌ خطا در Chrome driver: {e}")
    traceback.print_exc()

print("\nتست کامل شد!") 