
import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from html import unescape

BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHAT_ID = os.getenv("TG_CHAT_ID")

QUERIES = [
    '"TON mining bot"',
    '"Toncoin mining bot"',
    '"Telegram TON mining"',
]

STATE_FILE = "seen.json"


def load_seen():
    try:
        with open(STATE_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_seen(seen):
    with open(STATE_FILE, "w") as f:
        json.dump(list(seen)[-1000:], f)


def search_web(query):
    params = urllib.parse.urlencode({
        "q": query,
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en"
    })

    url = "https://news.google.com/rss/search?" + params
    request = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        root = ET.fromstring(response.read())

    results = []

    for item in root.findall(".//item"):
        title = unescape(item.findtext("title", ""))
        link = item.findtext("link", "")
        description = unescape(item.findtext("description", ""))

        text = (title + " " + description).lower()

        if "mining" in text and (
            "ton" in text or "toncoin" in text
        ):
            results.append((title, link))

    return results


def send_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram secrets are not configured.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message
    }).encode()

    request = urllib.request.Request(url, data=data)

    with urllib.request.urlopen(request, timeout=20) as response:
        print(response.read().decode())


def main():
    seen = load_seen()
    found = []

    for query in QUERIES:
        try:
            found.extend(search_web(query))
        except Exception as error:
            print("Search error:", error)

    for title, link in found:
        if not link or link in seen:
            continue

        message = (
            "⛏️ TON MINING NEWS FOUND\n\n"
            f"Title: {title}\n\n"
            f"Source: {link}\n\n"
            "⚠️ This is an unverified discovery."
        )

        send_alert(message)
        seen.add(link)

    save_seen(seen)


if __name__ == "__main__":
    main()
  
