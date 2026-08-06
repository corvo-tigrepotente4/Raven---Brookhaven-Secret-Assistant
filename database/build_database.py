import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

BASE_URL = "https://solve.bhmystery.com/"

conn = sqlite3.connect("secrets.db")
cursor = conn.cursor()

print("Cleaning database...")

# Remove all existing entries
cursor.execute("DELETE FROM secrets;")

# Remove old test tables if they exist
test_tables = [
    "test_fts",
    "test_fts_data",
    "test_fts_idx",
    "test_fts_content",
    "test_fts_docsize",
    "test_fts_config"
]

for table in test_tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
        print(f"Removed {table}")
    except Exception as e:
        print(e)

conn.commit()

visited = set()
queue = deque([BASE_URL])
pages = []

session = requests.Session()
session.headers.update({
    "User-Agent": "Raven Database Builder/1.0"
})

# ==========================================
# CRAWLER
# ==========================================

def is_internal(url):
    parsed = urlparse(url)

    # Must stay on solve.bhmystery.com
    if parsed.netloc and parsed.netloc != "solve.bhmystery.com":
        return False

    # Skip files
    blocked = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg",
        ".ico", ".pdf", ".zip", ".mp4", ".mp3",
        ".webm", ".css", ".js", ".xml"
    )

    if parsed.path.lower().endswith(blocked):
        return False

    return True


def normalize(url):
    url = url.split("#")[0]
    if url.endswith("/") and url != BASE_URL:
        url = url[:-1]
    return url


print("Beginning crawl...\n")

while queue:

    url = normalize(queue.popleft())

    if url in visited:
        continue

    visited.add(url)

    try:

        print("Visiting:", url)

        response = session.get(url, timeout=20)

        if response.status_code != 200:
            continue

        if "text/html" not in response.headers.get("Content-Type", ""):
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        pages.append((url, soup))

        # Find every link
        for link in soup.find_all("a", href=True):

            href = urljoin(url, link["href"])
            href = normalize(href)

            if not is_internal(href):
                continue

            if href not in visited:
                queue.append(href)

        time.sleep(0.2)

    except Exception as e:
        print("Failed:", url)
        print(e)

print(f"\nFinished crawling {len(pages)} pages.")

# ==========================================
# EXTRACT PAGE CONTENT
# ==========================================

def clean_text(text):
    lines = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # remove excessive whitespace
        line = " ".join(line.split())

        lines.append(line)

    return "\n".join(lines)


def extract_page(soup):

    # Remove useless elements
    for tag in soup([
        "script",
        "style",
        "noscript",
        "svg",
        "footer",
        "header",
        "nav",
        "aside"
    ]):
        tag.decompose()

    # Try common documentation containers
    selectors = [

        "article",
        "main",

        ".md-content",
        ".md-content__inner",

        ".content",
        ".page-content",

        ".article",

        "#content",
        "#main-content",

        ".markdown",

        ".theme-doc-markdown",

        "body"

    ]

    content = None

    for selector in selectors:

        found = soup.select_one(selector)

        if found:

            content = found

            break

    if content is None:
        content = soup

    title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled"

    text = clean_text(
        content.get_text("\n", strip=True)
    )

    return title, text


print("\nExtracting page contents...\n")

records = []

for url, soup in pages:

    try:

        title, text = extract_page(soup)

        if len(text) < 100:
            continue

        records.append({

            "title": title,
            "url": url,
            "content": text

        })

        print(f"✓ {title}")

    except Exception as e:

        print("Extraction failed:", url)
        print(e)

print(f"\nReady to import {len(records)} pages.")

# ==========================================
# IMPORT INTO DATABASE
# ==========================================

print("\nImporting pages into database...\n")

inserted = 0

for record in records:

    try:

        cursor.execute("""
            INSERT INTO secrets(title, url, content)
            VALUES (?, ?, ?)
        """, (
            record["title"],
            record["url"],
            record["content"]
        ))

        inserted += 1

    except Exception as e:

        print("Failed to insert:", record["url"])
        print(e)

conn.commit()

print(f"\nInserted {inserted} pages.")

# ==========================================
# REBUILD FTS INDEX
# ==========================================

print("\nRebuilding Full Text Search index...")

try:

    cursor.execute(
        "INSERT INTO secrets_fts(secrets_fts) VALUES('rebuild');"
    )

    conn.commit()

    print("FTS rebuilt successfully!")

except Exception as e:

    print("FTS rebuild failed:")
    print(e)

# ==========================================
# OPTIMIZE FTS
# ==========================================

try:

    cursor.execute(
        "INSERT INTO secrets_fts(secrets_fts) VALUES('optimize');"
    )

    conn.commit()

    print("FTS optimized!")

except Exception:
    pass

# ==========================================
# FINAL STATISTICS
# ==========================================

cursor.execute("SELECT COUNT(*) FROM secrets")
count = cursor.fetchone()[0]

print("\n==============================")
print("DATABASE BUILD COMPLETE")
print("==============================")
print(f"Pages visited : {len(pages)}")
print(f"Pages imported: {inserted}")
print(f"Database rows : {count}")
print("==============================")

conn.close()