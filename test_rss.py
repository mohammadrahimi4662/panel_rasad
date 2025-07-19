import requests

url = "https://www.isna.ir/rss"
try:
    response = requests.get(url, timeout=10)
    print("Status code:", response.status_code)
    print("Content (first 500 chars):")
    print(response.text[:500])
except Exception as e:
    print("خطا:", e) 