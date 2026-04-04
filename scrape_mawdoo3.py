import requests
import json
import time
from datetime import datetime

API_BASE = "https://mawdoo3.com/wp-json/wp/v2/posts"

# Headers قوية جداً (تشبه المتصفح الحقيقي)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://mawdoo3.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

results = []

def fetch_posts(page=1, per_page=100):
    for attempt in range(3):  # retry 3 مرات
        try:
            res = requests.get(
                API_BASE,
                params={
                    "per_page": per_page,
                    "page": page,
                    "_embed": "true"   # مهم: يجلب المؤلف + الصور + التصنيفات
                },
                headers=HEADERS,
                timeout=30
            )
            
            print(f"📄 Page {page} → Status: {res.status_code}")
            
            if res.status_code == 200:
                data = res.json()
                print(f"   ✅ تم جلب {len(data)} مقال")
                return data
                
            elif res.status_code == 429:  # rate limit
                wait = 60 * (attempt + 1)
                print(f"   ⏳ Rate limit → ننتظر {wait} ثانية")
                time.sleep(wait)
                continue
                
            elif res.status_code >= 400:
                print(f"   ❌ Error: {res.text[:400]}")
                time.sleep(10)
                continue
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            time.sleep(5)
    
    return []  # فشل بعد 3 محاولات

def run():
    page = 1
    per_page = 100
    max_pages = 100  # أمان (يمكنك رفعه)

    while page <= max_pages:
        print(f"\n{'='*50}\n🚀 جلب الصفحة {page}\n{'='*50}")
        posts = fetch_posts(page, per_page)
        
        if not posts:
            print("🚫 لا يوجد المزيد من المقالات → انتهى")
            break
        
        for p in posts:
            results.append({
                "title": p["title"]["rendered"],
                "link": p["link"],
                "date": p.get("date_gmt"),
                "excerpt": p["excerpt"]["rendered"],
                "author": p["_embedded"]["author"][0]["name"] if "_embedded" in p and "author" in p["_embedded"] else None,
                "categories": [cat["name"] for cat in p["_embedded"].get("wp:term", [[]])[0]] if "_embedded" in p else [],
                "featured_image": p["_embedded"]["wp:featuredmedia"][0]["source_url"] if "_embedded" in p and "wp:featuredmedia" in p["_embedded"] else None,
            })
        
        page += 1
        time.sleep(2)  # delay مهذب (يقلل من الحظر)

    # حفظ النتيجة
    timestamp = datetime.utcnow().isoformat()
    output = {
        "last_updated": timestamp,
        "total_posts": len(results),
        "posts": results
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 انتهى! تم جلب {len(results)} مقال وحفظها في output.json")

if __name__ == "__main__":
    run()
