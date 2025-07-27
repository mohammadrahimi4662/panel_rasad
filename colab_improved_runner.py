#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 اجرای بهبود یافته برنامه اخبار در Google Colab
حل مشکلات فونت فارسی و خلاصه‌سازی
"""

import os
import subprocess
import sys
import urllib.request
from datetime import datetime

def download_font():
    """دانلود فونت فارسی"""
    print("📥 دانلود فونت فارسی...")
    try:
        urllib.request.urlretrieve(
            "https://github.com/rastikerdar/vazirmatn/releases/download/v33.003/Vazirmatn-Regular.ttf",
            "Vazirmatn.ttf"
        )
        print("✅ فونت فارسی دانلود شد")
        return True
    except Exception as e:
        print(f"❌ خطا در دانلود فونت: {e}")
        return False

def run_command(command, description=""):
    """اجرای دستور و نمایش نتیجه"""
    print(f"🔄 {description}")
    print(f"دستور: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - موفق")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - خطا")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ خطا در اجرای دستور: {e}")
        return False

def setup_environment():
    """راه‌اندازی محیط"""
    print("🚀 راه‌اندازی محیط...")
    
    # پاک کردن فایل‌های قبلی
    run_command("rm -rf panel_rasad", "پاک کردن فایل‌های قبلی")
    
    # کلون کردن repository (این URL را تغییر دهید)
    repo_url = "https://github.com/YOUR_USERNAME/panel_rasad.git"
    if not run_command(f"git clone {repo_url}", "کلون کردن repository"):
        return False
    
    # ورود به پوشه
    os.chdir('panel_rasad')
    
    # نصب dependencies
    if not run_command("pip install -r requirements.txt", "نصب dependencies"):
        return False
    
    if not run_command("pip install jdatetime reportlab fastapi uvicorn jinja2 python-multipart", "نصب کتابخانه‌های اضافی"):
        return False
    
    # دانلود فونت
    download_font()
    
    return True

def update_and_fetch_news():
    """به‌روزرسانی و دریافت اخبار"""
    print("📰 به‌روزرسانی و دریافت اخبار...")
    
    # به‌روزرسانی از گیت
    if not run_command("git pull origin main", "به‌روزرسانی از گیت"):
        print("⚠️ هشدار: به‌روزرسانی ناموفق بود")
    
    # دریافت اخبار
    if not run_command("python news_fetcher.py", "دریافت اخبار"):
        return False
    
    return True

def generate_reports():
    """تولید گزارش‌ها"""
    print("📄 تولید گزارش‌ها...")
    
    # تولید PDF
    if not run_command("python news_pdf_generator.py", "تولید PDF"):
        return False
    
    # تولید HTML
    if not run_command("python beautiful_news_html.py", "تولید HTML"):
        return False
    
    return True

def list_files():
    """نمایش فایل‌های تولید شده"""
    print("📁 فایل‌های تولید شده:")
    
    import glob
    pdf_files = glob.glob('*.pdf')
    html_files = glob.glob('*.html')
    
    if pdf_files:
        print("\n📄 فایل‌های PDF:")
        for pdf in sorted(pdf_files, key=os.path.getctime, reverse=True):
            size = os.path.getsize(pdf) / 1024
            print(f"  - {pdf} ({size:.1f} KB)")
    
    if html_files:
        print("\n🌐 فایل‌های HTML:")
        for html in sorted(html_files, key=os.path.getctime, reverse=True):
            size = os.path.getsize(html) / 1024
            print(f"  - {html} ({size:.1f} KB)")

def download_files():
    """دانلود فایل‌ها"""
    print("📥 دانلود فایل‌ها...")
    
    try:
        from google.colab import files
        import glob
        
        # دانلود آخرین PDF
        pdf_files = glob.glob('*.pdf')
        if pdf_files:
            latest_pdf = max(pdf_files, key=os.path.getctime)
            files.download(latest_pdf)
            print(f"📥 فایل {latest_pdf} برای دانلود آماده شد")
        
        # دانلود آخرین HTML
        html_files = glob.glob('*.html')
        if html_files:
            latest_html = max(html_files, key=os.path.getctime)
            files.download(latest_html)
            print(f"🌐 فایل {latest_html} برای دانلود آماده شد")
        
        return True
    except ImportError:
        print("⚠️ Google Colab در دسترس نیست")
        return False

def run_complete_pipeline():
    """اجرای کامل pipeline"""
    print("🎯 شروع اجرای کامل برنامه...")
    print(f"⏰ زمان شروع: {datetime.now()}")
    
    # راه‌اندازی
    if not setup_environment():
        print("❌ راه‌اندازی ناموفق بود")
        return False
    
    # به‌روزرسانی و دریافت اخبار
    if not update_and_fetch_news():
        print("❌ دریافت اخبار ناموفق بود")
        return False
    
    # تولید گزارش‌ها
    if not generate_reports():
        print("❌ تولید گزارش‌ها ناموفق بود")
        return False
    
    # نمایش فایل‌ها
    list_files()
    
    # دانلود فایل‌ها
    download_files()
    
    print(f"⏰ زمان پایان: {datetime.now()}")
    print("✅ اجرای کامل برنامه با موفقیت انجام شد!")
    
    return True

def main():
    """تابع اصلی"""
    print("🎯 اجرای بهبود یافته برنامه اخبار در Google Colab")
    print("🔧 حل مشکلات فونت فارسی و خلاصه‌سازی")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            setup_environment()
        elif command == "fetch":
            update_and_fetch_news()
        elif command == "generate":
            generate_reports()
        elif command == "list":
            list_files()
        elif command == "download":
            download_files()
        else:
            print("❌ دستور نامعتبر")
            print("دستورات موجود: setup, fetch, generate, list, download")
    else:
        # اجرای کامل pipeline
        run_complete_pipeline()

if __name__ == "__main__":
    main() 