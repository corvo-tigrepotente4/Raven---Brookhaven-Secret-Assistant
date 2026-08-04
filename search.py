import sqlite3
import re

# Connect to database
conn = sqlite3.connect("database/secrets.db")
cursor = conn.cursor()

# Load all secrets
cursor.execute("SELECT title, url, content FROM secrets")
secrets = cursor.fetchall()

conn.close()


def clean(text):
    """Lowercase and remove punctuation."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return text


def score(secret, query):
    title, url, content = secret

    title_clean = clean(title)
    url_clean = clean(url)
    content_clean = clean(content)
    query_clean = clean(query)

    words = query_clean.split()

    points = 0

    for word in words:

        # Exact title match
        if word in title_clean:
            points += 100

        # URL match
        if word in url_clean:
            points += 50

        # Count occurrences in content
        points += content_clean.count(word) * 10

    return points


while True:

    query = input("\nAsk a secret: ").strip()

    if query.lower() in ("exit", "quit"):
        break

    results = []

    for secret in secrets:
        s = score(secret, query)

        if s > 0:
            results.append((s, secret))

    results.sort(reverse=True, key=lambda x: x[0])

    if not results:
        print("\nNo matches found.")
        continue

    print("\nTOP RESULTS:\n")

    for points, secret in results[:5]:

        title, url, content = secret

        print(f"Score: {points}")
        print(title)
        print(url)
        print("-" * 50)

    print("\nBEST MATCH:\n")

    print(results[0][1][0])

    print("\nANSWER:\n")

    print(results[0][1][2][:3000])