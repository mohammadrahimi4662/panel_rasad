#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback

def test_imports():
    """تست import های مورد نیاز"""
    try:
        print("🔍 تست import ها...")
        
        import requests
        print("✅ requests")
        
        from bs4 import BeautifulSoup
        print("✅ beautifulsoup4")
        
        from database import SessionLocal, News
        print("✅ database")
        
        import datetime
        print("✅ datetime")
        
        from dateutil import parser as date_parser
        print("✅ python-dateutil")
        
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        print("✅ selenium")
        
        return True
    except Exception as e:
        print(f"❌ خطا در import: {e}")
        traceback.print_exc()
        return False

def test_database():
    """تست اتصال به دیتابیس"""
    try:
        print("\n🔍 تست دیتابیس...")
        from database import SessionLocal, News
        
        db = SessionLocal()
        count = db.query(News).count()
        print(f"✅ اتصال به دیتابیس موفق - تعداد اخبار موجود: {count}")
        db.close()
        return True
    except Exception as e:
        print(f"❌ خطا در دیتابیس: {e}")
        traceback.print_exc()
        return False

def test_web_requests():
    """تست درخواست‌های وب"""
    try:
        print("\n🔍 تست درخواست‌های وب...")
        import requests
        
        # تست BBC
        response = requests.get('https://www.bbc.com/persian/topics/ckdxnwvwwjnt', timeout=10)
        print(f"✅ BBC - Status: {response.status_code}")
        
        # تست IranIntl
        response = requests.get('https://www.iranintl.com/iran', timeout=10)
        print(f"✅ IranIntl - Status: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ خطا در درخواست‌های وب: {e}")
        return False

def test_chrome_driver():
    """تست Chrome driver"""
    try:
        print("\n🔍 تست Chrome driver...")
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.get('https://www.google.com')
        title = driver.title
        driver.quit()
        print(f"✅ Chrome driver کار می‌کند - عنوان صفحه: {title}")
        return True
    except Exception as e:
        print(f"❌ خطا در Chrome driver: {e}")
        traceback.print_exc()
        return False

def main():
    print("🚀 شروع تست‌های برنامه...")
    
    tests = [
        test_imports,
        test_database,
        test_web_requests,
        test_chrome_driver
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 نتیجه تست‌ها: {passed}/{total} موفق")
    
    if passed == total:
        print("🎉 همه تست‌ها موفق بودند!")
        print("💡 حالا می‌توانید news_fetcher.py را اجرا کنید")
    else:
        print("⚠️ برخی تست‌ها ناموفق بودند")
        print("🔧 لطفاً مشکلات را برطرف کنید")

if __name__ == "__main__":
    main() 