import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timezone

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    "Referer": "https://mawdoo3.com/",
}

# قائمة تصنيفات حقيقية وكبيرة (يمكنك إضافة المزيد)
CATEGORIES = [
    "https://mawdoo3.com/تصنيف:تغذية",
    "https://mawdoo3.com/تصنيف:صحة",
    "https://mawdoo3.com/تصنيف:فن_الطهي",
    "https://mawdoo3.com/تصنيف:حول_العالم",
    "https://mawdoo3.com/تصنيف:تقنية",
    "https://mawdoo3.com/تصنيف:إسلام",
    "https://mawdoo3.com/تصنيف:تاريخ",
    "https://mawdoo3.com/تصنيف:علوم",
    "https://mawdoo3.com/تصنيف:نفسية",
    "https://mawdoo3.com/تصنيف:رياضة",
    "https://mawdoo3.com/تصنيف:مال_وأعمال",
]

results = []
seen = set()

def scrape_page(url):
    print(f"📄 جاري جلب: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"   ❌ {r.status_code}")
            return 0
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # الـ selector الجديد القوي (li a + السابق)
        links = soup.select("li a, h1 a, h2 a, h3 a, .entry-title a, .post-title a, .card-title a, article .title a")
        
        found = 0
        for a in links:
            title = a.get_text(strip=True)
            href = a.get("href")
            if not href or len(title) < 8:
                continue
            
            if not href.startswith("http"):
                href = "https://mawdoo3.com" + href if href.startswith("/") else href
            
            if href in seen or any(x in href for x in ["/تصنيف:", "/tag/", "/page/", "/خاص:"]):
                continue
            
            seen.add(href)
            results.append({
                "title": title,
                "link": href,
                "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            })
            found += 1
        
        print(f"   ✅ تم العثور على {found} مقال جديد (إجمالي: {len(results)})")
        return found
        
    except Exception as e:
        print(f"   ❌ خطأ: {e}")
        return 0

def run():
    print("🚀 بدء سكراب mawdoo3.com (النسخة المصححة)...\n")
    
    # جلب الصفحة الرئيسية أولاً
    scrape_page("https://mawdoo3.com/")
    
    # جلب التصنيفات
    for cat in CATEGORIES:
        # الصفحة الأولى
        scrape_page(cat)
        time.sleep(1.2)
        
        # محاولة الصفحات التالية (حتى 3 صفحات لكل تصنيف)
        for page in range(2, 4):
            page_url = f"{cat}/page/{page}/"
            if scrape_page(page_url) == 0:
                break  # لا يوجد المزيد
            time.sleep(1.5)
    
    # حفظ الملف
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_posts": len(results),
        "posts": results
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 انتهى! تم جمع {len(results)} مقال وحفظها في output.json")

if __name__ == "__main__":
    run()
