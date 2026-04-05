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

CATEGORIES = [
    "https://mawdoo3.com/تصنيف:تغذية",
    "https://mawdoo3.com/تصنيف:فن_الطهي",
    "https://mawdoo3.com/تصنيف:حول_العالم",
    "https://mawdoo3.com/تصنيف:تقنية",
    "https://mawdoo3.com/تصنيف:إسلام",
    # أضف المزيد من التصنيفات إذا أردت
]

results = []
seen = set()

def scrape_category(url, max_pages=3):
    for page in range(1, max_pages + 1):
        page_url = f"{url}/page/{page}/" if page > 1 else url
        print(f"📄 جاري جلب: {page_url}")
        
        try:
            r = requests.get(page_url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"   ❌ {r.status_code} - توقف")
                break
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # selectors قوية ومتعددة (تعمل على معظم مواقع ووردبريس العربية)
            links = soup.select("h1 a, h2 a, h3 a, .entry-title a, .post-title a, .card-title a, article .title a, .blog-post a")
            
            found = 0
            for a in links:
                title = a.get_text(strip=True)
                href = a.get("href")
                if not href or len(title) < 10:
                    continue
                
                if not href.startswith("http"):
                    href = "https://mawdoo3.com" + href if href.startswith("/") else href
                
                if href in seen or any(x in href for x in ["/تصنيف:", "/tag/", "/page/"]):
                    continue
                
                seen.add(href)
                results.append({
                    "title": title,
                    "link": href,
                    "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                })
                found += 1
            
            print(f"   ✅ تم العثور على {found} مقال جديد (إجمالي: {len(results)})")
            
            if found == 0:
                break  # لا يوجد صفحات أخرى
                
            time.sleep(1.5)  # delay مهذب
            
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            break

def run():
    print("🚀 بدء سكراب mawdoo3.com من التصنيفات...")
    for cat in CATEGORIES:
        scrape_category(cat, max_pages=4)  # يجلب حتى 4 صفحات من كل تصنيف
    
    # حفظ
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
