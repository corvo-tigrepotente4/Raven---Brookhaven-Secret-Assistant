import requests
import sqlite3
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

START_URL = "https://solve.bhmystery.com/casebook/"


def get_page(url):
    for attempt in range(3):
        try:
            response = requests.get(
                url,
                timeout=15,
                headers={
                    "User-Agent": "BrookhavenSecretHunter/1.0"
                }
            )
            return response.text

        except Exception:
            print("Retry", attempt + 1, "failed:", url)
            time.sleep(3)

    print("FAILED:", url)
    return None


# -------------------------
# STEP 1: Find CaseBook links
# -------------------------

print("Finding CaseBook pages...")

html = get_page(START_URL)

if html is None:
    exit()

soup = BeautifulSoup(html, "html.parser")

pages = []

for a in soup.find_all("a"):
    href = a.get("href")

    if href:
        full_url = urljoin(START_URL, href)

        if "/casebook/" in full_url:
            pages.append(full_url)

pages = list(set(pages))

print("Found", len(pages), "links")


# -------------------------
# STEP 2: Filter real pages
# -------------------------

real_pages = []

for url in pages:

    print("Checking:", url)

    time.sleep(1)

    html = get_page(url)

    if html is None:
        continue

    soup = BeautifulSoup(html, "html.parser")

    article = soup.find("article", class_="default")

    if article:

        text = article.get_text(
            separator="\n",
            strip=True
        )

        if len(text) > 200:
            real_pages.append(url)

print()
print("REAL PAGES:", len(real_pages))


# -------------------------
# STEP 3: Open database
# -------------------------

conn = sqlite3.connect("database/secrets.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM secrets")


# -------------------------
# STEP 4: Save secrets
# -------------------------

for url in real_pages:

    print("Saving:", url)

    time.sleep(1)

    html = get_page(url)

    if html is None:
        continue

    soup = BeautifulSoup(html, "html.parser")

    article = soup.find("article", class_="default")

    if article:

        title = soup.title.text.strip()

        text = article.get_text(
            separator="\n",
            strip=True
        )

        cursor.execute(
            """
            INSERT INTO secrets (title, url, content)
            VALUES (?, ?, ?)
            """,
            (
                title,
                url,
                text
            )
        )


# -------------------------
# STEP 5: Finish
# -------------------------

conn.commit()
conn.close()

print()
print("DONE!")
print("Saved", len(real_pages), "secrets")