import requests
import xml.etree.ElementTree as ET
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

SITEMAP_INDEX = "https://mawdoo3.com/sitemap/sitemap-index-mawdoo3com.xml"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

results = []
seen = set()

def fetch_sitemap(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code != 200:
            print(f"❌ فشل تحميل: {url} → {r.status_code}")
            return []
        return r.text
    except Exception as e:
        print(f"❌ خطأ في {url}: {e}")
        return ""

def parse_sitemap(xml_text):
    links = []
    try:
        root = ET.fromstring(xml_text)
        # namespace الخاص بـ sitemap
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # إذا كان index (يحتوي على <sitemap>)
        for sitemap in root.findall('.//s:sitemap/s:loc', ns):
            sub_url = sitemap.text.strip()
            if sub_url:
                print(f"📂 جاري تحميل sub-sitemap: {sub_url}")
                sub_xml = fetch_sitemap(sub_url)
                if sub_xml:
                    links.extend(parse_sitemap(sub_xml))
        
        # إذا كان sitemap عادي (يحتوي على <url>)
        for url_tag in root.findall('.//s:url/s:loc', ns):
            link = url_tag.text.strip()
            if link and link not in seen and "/تصنيف:" not in link and "/tag/" not in link and "/page/" not in link:
                seen.add(link)
                # استخراج slug كـ title مؤقت (يمكن تحسينه لاحقاً)
                slug = link.rstrip('/').split('/')[-1].replace('-', ' ')
                title = slug.title() if slug else "مقال بدون عنوان"
                results.append({
                    "title": title,
                    "link": link,
                    "scraped_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                })
                links.append(link)
    except Exception as e:
        print(f"⚠️ خطأ في تحليل XML: {e}")
    return links

def run():
    print("🚀 بدء سكراب Sitemap لموقع mawdoo3.com...")
    xml_index = fetch_sitemap(SITEMAP_INDEX)
    
    if not xml_index:
        print("❌ فشل تحميل Sitemap Index")
        return
    
    print("📋 تحليل Sitemap Index...")
    parse_sitemap(xml_index)
    
    # ترتيب حسب الأحدث (اختياري)
    results.sort(key=lambda x: x["link"], reverse=True)
    
    # حفظ
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "total_posts": len(results),
        "posts": results[:1500]   # حد أعلى معقول (يمكنك رفعه)
    }
    
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 تم بنجاح! تم جمع {len(results)} رابط مقال")
    print(f"   💾 تم حفظ {len(output['posts'])} في output.json")

if __name__ == "__main__":
    run()
