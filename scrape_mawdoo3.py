import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

URL = "https://mawdoo3.com/"
results = []

def scrape_mawdoo3(max_articles=500):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="ar-SA"
        )
        page = context.new_page()
        
        print("🔄 جاري فتح الموقع...")
        page.goto(URL, wait_until="networkidle", timeout=60000)
        time.sleep(3)

        print("📜 بدء السكراب (Infinite Scroll)...")
        last_count = 0
        scroll_attempts = 0
        max_scrolls = 80  # يمكنك زيادته إذا أردت المزيد

        while len(results) < max_articles and scroll_attempts < max_scrolls:
            # استخراج المقالات المرئية حالياً
            articles = page.query_selector_all("article, .post-item, .entry, a[href*='/'] h2, h1 a, h2 a")
            
            for article in articles:
                try:
                    # محاولة استخراج العنوان والرابط بطرق مختلفة
                    title_elem = article.query_selector("h1 a, h2 a, h3 a, .title a, a")
                    if not title_elem:
                        continue
                    title = title_elem.inner_text().strip()
                    link = title_elem.get_attribute("href")
                    
                    if link and title and len(title) > 5:
                        if not link.startswith("http"):
                            link = "https://mawdoo3.com" + link if link.startswith("/") else link
                        
                        # تجنب التكرار
                        if not any(r["link"] == link for r in results):
                            results.append({
                                "title": title,
                                "link": link,
                                "scraped_at": datetime.utcnow().isoformat()
                            })
                except:
                    continue

            current_count = len(results)
            print(f"   📊 تم جمع {current_count} مقال حتى الآن...")

            if current_count == last_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_count = current_count

            # Scroll للأسفل
            page.evaluate("window.scrollBy(0, 1200)")
            time.sleep(2.5)  # انتظر تحميل المحتوى

        browser.close()

    print(f"\n🎉 انتهى السكراب! تم جمع {len(results)} مقال")

    # حفظ النتيجة
    output = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_posts": len(results),
        "posts": results[:max_articles]
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_mawdoo3(max_articles=800)  # غير الرقم حسب حاجتك
