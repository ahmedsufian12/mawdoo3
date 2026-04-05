import requests
from bs4 import BeautifulSoup
import json
import time
import re
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
MAX_FULL_SCRAPE = 200   # يمكنك رفعه أكثر

def clean_content(soup):
    """تنظيف المحتوى حسب طلبك بالضبط"""
    content = soup.find('div', id='mw-content-text')
    if not content:
        return "<p>لم يتم استخراج المحتوى</p>"

    # 1. حذف جدول المحتويات (TOC)
    toc = content.find('div', id='toc')
    if toc:
        toc.decompose()

    # 2. حذف أرقام المراجع (الـ sup)
    for sup in content.find_all('sup', class_='reference'):
        sup.decompose()

    # 3. تصليح روابط المراجع + إضافة nofollow + target="_blank"
    for a in content.find_all('a', class_='external'):
        href = a.get('href', '')
        # إصلاح الروابط المعطوبة (localhost)
        match = re.search(r'https?://[^"\']+', href)
        if match:
            href = match.group(0)
        a['href'] = href
        a['rel'] = 'nofollow'
        a['target'] = '_blank'

    # 4. حذف كل العناصر غير المرغوبة
    for junk in content.select('script, .feedback-feature, .popup-container, .share, #widget, .printfooter, .embedvideo, .related-articles-list1'):
        junk.decompose()

    # 5. تنظيف نهائي: إزالة المسافات الزائدة والـ \n
    for tag in content.find_all(['p', 'div', 'br']):
        if not tag.get_text(strip=True):
            tag.decompose()

    # تحويل إلى نص HTML نظيف جداً
    html = str(content)
    html = re.sub(r'\s+', ' ', html)          # إزالة كل المسافات الزائدة
    html = re.sub(r'<\s*br\s*/?>', '', html)  # حذف <br> الزائدة
    return html.strip()

def get_article_details(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # العنوان
        title_tag = soup.find('h1', class_='title') or soup.find('h1')
        title = title_tag.get_text(strip=True).replace(" - موضوع", "").strip() if title_tag else "بدون عنوان"

        # التاريخ
        published_date = None
        date_span = soup.find('span', attrs={"itemprop": ["dateModified", "datePublished"]})
        if date_span:
            published_date = date_span.get_text(strip=True)

        # التصنيفات
        categories = [a.get_text(strip=True) for a in soup.select("a[href^='/تصنيف:']") if a.get_text(strip=True)]

        # الصورة الرئيسية
        featured = None
        img = soup.find('img', id='articleimagediv')
        if img:
            featured = img.get('src') or img.get('data-src')
        if not featured:
            og = soup.find('meta', property='og:image')
            if og:
                featured = og.get('content')

        # المحتوى المنظف حسب طلبك
        content_html = clean_content(soup)

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

# باقي الكود (جمع الروابط) كما هو بدون تغيير
def scrape_links():
    print("🚀 مرحلة 1: جمع الروابط...")
    for cat in CATEGORIES:
        for page in range(1, 5):
            url = f"{cat}/page/{page}/" if page > 1 else cat
            print(f"   📄 {url}")
            try:
                r = requests.get(url, headers=HEADERS, timeout=20)
                if r.status_code != 200:
                    break
                soup = BeautifulSoup(r.text, "html.parser")
                links = soup.select("li a, h1 a, h2 a, h3 a, .title a")
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
    
    print(f"\n🔥 مرحلة 2: استخراج + تنظيف المحتوى لـ {min(MAX_FULL_SCRAPE, len(results))} مقالة...")
    full_articles = []
    for i, item in enumerate(results[:MAX_FULL_SCRAPE]):
        print(f"   [{i+1}/{MAX_FULL_SCRAPE}] {item['link']}")
        details = get_article_details(item["link"])
        if details:
            full_articles.append(details)
        time.sleep(1.6)
    
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_links_found": len(results),
        "total_full_articles": len(full_articles),
        "posts": full_articles
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 انتهى بنجاح! تم تنظيف كل المقالات حسب طلبك")

if __name__ == "__main__":
    run()
