import requests
from bs4 import BeautifulSoup
import json
import time

BASE = "https://mawdoo3.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}

visited = set()
results = []


def get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except:
        return None


def get_posts(page_url):
    soup = get(page_url)
    links = set()

    if not soup:
        return links

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.startswith("/") and len(href.split("/")) > 2:
            links.add(BASE + href)

    return links


def scrape_post(url):
    if url in visited:
        return

    soup = get(url)
    if not soup:
        return

    title = soup.find("h1")
    article = soup.find("article")

    if not title or not article:
        return

    data = {
        "url": url,
        "title": title.get_text(strip=True),
        "content": article.get_text(strip=True)
    }

    print("✔", data["title"])

    visited.add(url)
    results.append(data)


def run():
    # جرب قسم واحد لتجنب البلوك
    category = BASE + "/%D8%AA%D8%B9%D9%84%D9%8A%D9%85"

    for page in range(1, 4):
        page_url = f"{category}/page/{page}"
        print("Page:", page_url)

        posts = get_posts(page_url)

        for p in posts:
            scrape_post(p)
            time.sleep(1)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
