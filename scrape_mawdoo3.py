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
    "https://mawdoo3.com/",  # الصفحة الرئيسية
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
MAX_FULL_SCRAPE = 400   # غيّر الرقم حسب احتياجك (400 ≈ 15-20 دقيقة)

def get_article_details(url):
    """يدخل على المقالة ويجلب كل التفاصيل"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 1. العنوان
        title = soup.find("h1", class_="entry-title")
        if not title:
            title = soup.find("h1")
        title = title.get_text(strip=True) if title else "بدون عنوان"
        
        # 2. تاريخ النشر
        date = None
        # طرق متعددة لاستخراج التاريخ
        meta_date = soup.find("meta", property="article:published_time")
        if meta_date:
            date = meta_date.get("content")
        else:
            time_tag = soup.find("time")
            if time_tag:
                date = time_tag.get("datetime") or time_tag.get_text(strip=True)
        
        # 3. التصنيفات
        categories = []
        cat_links = soup.select(".cat-links a, .post-categories a, .entry-meta a[rel='category']")
        for a in cat_links:
            cat = a.get_text(strip=True)
            if cat and cat not in categories:
                categories.append(cat)
        
        # 4. الصورة الرئيسية
        featured_img = soup.find("img", class_="wp-post-image")
        if featured_img:
            featured = featured_img.get("src") or featured_img.get("data-src")
        else:
            featured = soup.find("meta", property="og:image")
            featured = featured.get("content") if featured else None
        
        # 5. نص المقالة كامل HTML (مع الصور والتنسيق)
        content_div = soup.select_one(".entry-content, .post-content, .article-content, .content-area")
        content_html = str(content_div) if content_div else "<p>لم يتم استخراج المحتوى</p>"
        
        return {
            "title": title,
            "link": url,
            "published_date": date,
            "categories": categories,
            "featured_image": featured,
            "content_html": content_html,
            "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
    except Exception as e:
        print(f"   ❌ خطأ في {url}: {e}")
        return None

def scrape_links():
    """المرحلة الأولى: جمع كل الروابط"""
    print("🚀 مرحلة 1: جمع الروابط...")
    for cat in CATEGORIES:
        for page in range(1, 5):  # حتى 4 صفحات من كل تصنيف
            url = f"{cat}/page/{page}/" if page > 1 else cat
            print(f"   📄 {url}")
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                links = soup.select("li a, h1 a, h2 a, h3 a, .entry-title a")
                found = 0
                for a in links:
                    href = a.get("href")
                    if not href or len(a.get_text(strip=True)) < 8:
                        continue
                    if not href.startswith("http"):
                        href = "https://mawdoo3.com" + href if href.startswith("/") else href
                    if href in seen or any(x in href for x in ["/تصنيف:", "/tag/", "/page/"]):
                        continue
                    seen.add(href)
                    results.append({"link": href})  # مؤقت
                    found += 1
                print(f"      ✅ {found} رابط جديد")
                if found == 0:
                    break
                time.sleep(1.2)
            except:
                break

def run():
    scrape_links()
    
    print(f"\n🔥 مرحلة 2: استخراج التفاصيل الكاملة لـ {min(MAX_FULL_SCRAPE, len(results))} مقالة...")
    full_articles = []
    for i, item in enumerate(results[:MAX_FULL_SCRAPE]):
        print(f"   [{i+1}/{MAX_FULL_SCRAPE}] {item['link']}")
        details = get_article_details(item["link"])
        if details:
            full_articles.append(details)
        time.sleep(1.8)  # delay مهذب جداً
    
    # حفظ
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_links_found": len(results),
        "total_full_articles": len(full_articles),
        "posts": full_articles
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 انتهى بنجاح!")
    print(f"   • تم جمع {len(results)} رابط")
    print(f"   • تم استخراج التفاصيل الكاملة (HTML + صور + تاريخ + تصنيفات) لـ {len(full_articles)} مقالة")

if __name__ == "__main__":
    run()
