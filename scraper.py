import requests
import json
import time

API_URL = "https://mawdoo3.com/wp-json/wp/v2/posts?_embed"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Referer": "https://mawdoo3.com/"
}

results = []


def fetch_posts(page=1):
    try:
        res = requests.get(API_URL, params={
            "per_page": 10,
            "page": page
        }, headers=HEADERS, timeout=10)

        print("STATUS:", res.status_code)

        if res.status_code != 200:
            print("ERROR RESPONSE:", res.text[:200])
            return []

        data = res.json()

        print("POSTS FOUND:", len(data))

        return data

    except Exception as e:
        print("EXCEPTION:", e)
        return []


def run():
    for page in range(1, 6):
        print(f"\n=== Page {page} ===")

        posts = fetch_posts(page)

        if not posts:
            print("No posts, stopping...")
            break

        for p in posts:
            title = p["title"]["rendered"]

            print("✔", title)

            results.append({
                "title": title,
                "link": p["link"]
            })

        time.sleep(1)

    print("\nTOTAL:", len(results))

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run()
