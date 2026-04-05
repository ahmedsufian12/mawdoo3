import json
import time
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

URL = "https://mawdoo3.com/"
results = []
seen_links = set()

def scrape_mawdoo3(max_articles=1000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="ar-SA"
        )
        page = context.new_page()
        
        print("🔄 جاري فتح الموقع...")
        page.goto(URL, wait_until="networkidle", timeout=90000)
        time.sleep(4)

        print("📜 بدء السكراب (Infinite Scroll + تحسين selectors)...")
        scroll_attempts = 0
        max_scrolls = 120   # يجلب ~800-1000 مقال بسهولة

        while len(results) < max_articles and scroll_attempts < max_scrolls:
            # === SELECTORS المحسنة والقوية جداً ===
            title_links = page.query_selector_all('h1 a, h2 a, h3 a, .post-title a, .entry-title a, .title a, .card-title a, .blog-title a')

            found_new = 0
            for link in title_links:
                try:
                    title = link.inner_text().strip()
                    href = link.get_attribute("href")
                    if not href or len(title) < 8:
                        continue
                    
                    if not href.startswith("http"):
                        href = "https://mawdoo3.com" + href if href.startswith("/") else href
                    
                    if href in seen_links or "تصنيف" in href or "tag" in href or "page" in href:
                        continue
                    
                    seen_links.add(href)
                    results.append({
                        "title": title,
                        "link": href,
                        "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    })
                    found_new += 1
                except:
                    continue

            print(f"   📊 الصفحة الحالية: {len(results)} مقال | جديد هذه الدورة: {found_new}")

            if found_new == 0:
                scroll_attempts += 1
            else:
                scroll_attempts = 0

            # Scroll أقوى + انتظر تحميل المحتوى
            page.evaluate("window.scrollBy(0, 1800)")
            time.sleep(2.8)

            # محاولة الضغط على زر "تحميل المزيد" إذا وجد
            try:
                load_more = page.query_selector('button:has-text("تحميل"), button:has-text("المزيد"), .load-more, [class*="load"]')
                if load_more:
                    load_more.click()
                    time.sleep(2)
            except:
                pass

        browser.close()

    print(f"\n🎉 انتهى السكراب! تم جمع {len(results)} مقال")

    # حفظ النتيجة
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_posts": len(results),
        "posts": results[:max_articles]
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scrape_mawdoo3(max_articles=1200)   # يمكنك تغييره
