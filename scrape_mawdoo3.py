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
    "https://mawdoo3.com/",
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
MAX_FULL_SCRAPE = 800   # يمكنك رفعه إلى 1500 أو أكثر (لكن سيطول الوقت)

def get_article_details(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 1. العنوان
        h1 = soup.find("h1")
        title = h1.get_text(strip=True).replace(" - موضوع", "").strip() if h1 else "بدون عنوان"
        
        # 2. تاريخ النشر
        published_date = None
        date_p = soup.find("p", string=lambda t: t and "آخر تحديث" in t)
        if date_p:
            published_date = date_p.get_text(strip=True)
        
        # 3. التصنيفات (في MediaWiki تكون روابط داخلية)
        categories = []
        for a in soup.select("a[href^='/تصنيف:'], a[href*='تصنيف']"):
            cat = a.get_text(strip=True)
            if cat and cat not in categories:
                categories.append(cat)
        # إذا لم يوجد، نأخذ بعض الروابط المتعلقة داخل المحتوى
        if not categories:
            for a in soup.select(".mw-parser-output a"):
                text = a.get_text(strip=True)
                if text and len(text) > 3 and text not in categories and "فوائد" in text or "ما هو" in text:
                    categories.append(text)
        
        # 4. الصورة الرئيسية
        featured = None
        # طريقة 1: og:image
        og_img = soup.find("meta", property="og:image")
        if og_img:
            featured = og_img.get("content")
        # طريقة 2: أول صورة كبيرة
        if not featured:
            img = soup.find("img", src=lambda s: s and ("modo3.com" in s or "mawdoo3.com" in s))
            if img:
                featured = img.get("src") or img.get("data-src")
        
        # 5. نص المقالة كامل HTML (المحتوى الحقيقي)
        content_div = soup.find("div", class_="mw-parser-output")
        content_html = str(content_div) if content_div else "<p>لم يتم استخراج المحتوى</p>"
        
        return {
            "title": title,
            "link": url,
            "published_date": published_date,
            "categories": categories,
            "featured_image": featured,
            "content_html": content_html,
            "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
        
    except Exception as e:
        print(f"   ❌ خطأ في {url}: {e}")
        return None

def scrape_links():
    print("🚀 مرحلة 1: جمع كل الروابط...")
    for cat in CATEGORIES:
        for page in range(1, 5):
            url = f"{cat}/page/{page}/" if page > 1 else cat
            print(f"   📄 {url}")
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                links = soup.select("li a, h1 a, h2 a, h3 a")
                found = 0
                for a in links:
                    href = a.get("href")
                    title_text = a.get_text(strip=True)
                    if not href or len(title_text) < 8:
                        continue
                    if not href.startswith("http"):
                        href = "https://mawdoo3.com" + href if href.startswith("/") else href
                    if href in seen or any(x in href for x in ["/تصنيف:", "/tag/", "/page/"]):
                        continue
                    seen.add(href)
                    results.append({"link": href})
                    found += 1
                print(f"      ✅ {found} رابط جديد (إجمالي: {len(results)})")
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
        time.sleep(1.7)   # delay مهذب (يقلل الحظر)
    
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
