import requests
import json
import time

API_URL = "https://mawdoo3.com/wp-json/wp/v2/posts"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

results = []


def fetch_posts(page=1):
    try:
        res = requests.get(API_URL, params={
            "per_page": 10,
            "page": page
        }, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            return []

        return res.json()
    except:
        return []


def run():
    for page in range(1, 6):  # 🔥 عدد الصفحات
        print(f"Page {page}")

        posts = fetch_posts(page)

        if not posts:
            break

        for p in posts:
            data = {
                "id": p["id"],
                "title": p["title"]["rendered"],
                "content": p["content"]["rendered"],
                "excerpt": p["excerpt"]["rendered"],
                "link": p["link"]
            }

            print("✔", data["title"])

            results.append(data)

        time.sleep(1)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
