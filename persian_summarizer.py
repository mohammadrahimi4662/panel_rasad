import requests
from bs4 import BeautifulSoup
import re
from transformers import pipeline, AutoTokenizer
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PersianSummarizer:
    def __init__(self):
        """راه‌اندازی خلاصه‌ساز فارسی"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"استفاده از دستگاه: {self.device}")
        
        # مدل خلاصه‌سازی فارسی
        try:
            print("در حال بارگذاری مدل خلاصه‌سازی فارسی...")
            self.summarizer = pipeline(
                "summarization",
                model="microsoft/DialoGPT-medium",  # مدل جایگزین برای خلاصه‌سازی
                device=self.device
            )
            print("مدل خلاصه‌سازی بارگذاری شد")
        except Exception as e:
            print(f"خطا در بارگذاری مدل خلاصه‌سازی: {e}")
            self.summarizer = None
        
        # مدل sentence transformer برای استخراج جملات مهم
        try:
            print("در حال بارگذاری مدل sentence transformer...")
            self.sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            print("مدل sentence transformer بارگذاری شد")
        except Exception as e:
            print(f"خطا در بارگذاری sentence transformer: {e}")
            self.sentence_model = None
    
    def clean_text(self, text):
        """پاک کردن متن"""
        if not text:
            return ""
        
        # حذف کاراکترهای اضافی
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\w\s\.\,\!\?\:\;\(\)\[\]\{\}]', '', text)
        text = text.strip()
        
        return text
    
    def extract_lead_paragraph(self, text, max_sentences=3):
        """استخراج پاراگراف اول (روتیتر)"""
        if not text:
            return ""
        
        # تقسیم به جملات
        sentences = re.split(r'[.!?؟]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # انتخاب جملات اول
        lead_sentences = sentences[:max_sentences]
        return '. '.join(lead_sentences) + '.'
    
    def extract_important_sentences(self, text, num_sentences=3):
        """استخراج جملات مهم با استفاده از TF-IDF"""
        if not text:
            return ""
        
        # تقسیم به جملات
        sentences = re.split(r'[.!?؟]', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        if len(sentences) <= num_sentences:
            return '. '.join(sentences) + '.'
        
        # استفاده از TF-IDF برای پیدا کردن جملات مهم
        try:
            vectorizer = TfidfVectorizer(max_features=100, stop_words=None)
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # محاسبه امتیاز هر جمله
            sentence_scores = tfidf_matrix.sum(axis=1).A1
            
            # انتخاب جملات با بالاترین امتیاز
            top_indices = sentence_scores.argsort()[-num_sentences:][::-1]
            top_sentences = [sentences[i] for i in sorted(top_indices)]
            
            return '. '.join(top_sentences) + '.'
        except Exception as e:
            print(f"خطا در TF-IDF: {e}")
            return self.extract_lead_paragraph(text, num_sentences)
    
    def extract_news_content(self, url):
        """استخراج محتوای خبر از URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # حذف اسکریپت‌ها و استایل‌ها
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # جستجوی محتوای اصلی خبر
            content_selectors = [
                'div.news-content',
                'div.article-content',
                'div.content',
                'article',
                'div.news-text',
                'div.news-body',
                'div.article-body',
                'div[class*="content"]',
                'div[class*="text"]',
                'div[class*="body"]'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.get_text(separator=' ', strip=True)
                        if len(text) > 100:  # فقط متن‌های طولانی
                            content_text += text + " "
                    if content_text:
                        break
            
            # اگر محتوای خاصی پیدا نشد، کل متن صفحه را بگیر
            if not content_text:
                content_text = soup.get_text(separator=' ', strip=True)
            
            return self.clean_text(content_text)
            
        except Exception as e:
            print(f"خطا در استخراج محتوای خبر: {e}")
            return ""
    
    def generate_summary(self, text, max_length=150):
        """تولید خلاصه هوشمند"""
        if not text:
            return ""
        
        # اگر متن خیلی کوتاه است، همان را برگردان
        if len(text) <= max_length:
            return text
        
        # روش 1: استفاده از مدل خلاصه‌سازی
        if self.summarizer and len(text) > 200:
            try:
                # تقسیم متن به بخش‌های کوچک‌تر
                chunks = self.split_text_into_chunks(text, 500)
                summaries = []
                
                for chunk in chunks:
                    if len(chunk) > 100:
                        summary = self.summarizer(chunk, max_length=100, min_length=30, do_sample=False)
                        if summary and len(summary) > 0:
                            summaries.append(summary[0]['summary_text'])
                
                if summaries:
                    return ' '.join(summaries)[:max_length] + "..."
            except Exception as e:
                print(f"خطا در خلاصه‌سازی با مدل: {e}")
        
        # روش 2: استخراج جملات مهم
        return self.extract_important_sentences(text, 2)
    
    def split_text_into_chunks(self, text, chunk_size=500):
        """تقسیم متن به بخش‌های کوچک‌تر"""
        sentences = re.split(r'[.!?؟]', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def get_news_summary(self, url, title):
        """دریافت خلاصه خبر"""
        print(f"در حال دریافت خلاصه برای: {title[:50]}...")
        
        # استخراج محتوای خبر
        content = self.extract_news_content(url)
        
        if not content:
            print("محتوای خبر یافت نشد")
            return ""
        
        # تولید خلاصه
        summary = self.generate_summary(content, max_length=200)
        
        print(f"خلاصه تولید شد: {len(summary)} کاراکتر")
        return summary

# نمونه استفاده
if __name__ == "__main__":
    summarizer = PersianSummarizer()
    
    # تست با یک URL نمونه
    test_url = "https://www.isna.ir/news/1404050401589/تریلر-آواتار-آتش-و-خاکستر-لو-رفت"
    summary = summarizer.get_news_summary(test_url, "تریلر آواتار")
    print(f"خلاصه: {summary}") 