import sqlite3
import re
from groq import Groq

# ==========================
# GROQ SETUP
# ==========================

client = Groq(
    api_key="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"
)

# ==========================
# DATABASE SETUP
# ==========================

print("Loading CaseBook database...")

conn = sqlite3.connect(
    "database/secrets.db",
    check_same_thread=False
)
cursor = conn.cursor()

print("Database ready!")
print("Raven is ready!")

# ==========================
# SEARCH FUNCTION
# ==========================

STOP_WORDS = {
    "where", "is", "the", "a", "an", "how", "do", "i",
    "get", "to", "in", "of", "and", "what", "does",
    "tell", "me", "about", "please", "can", "you"
}


def search_casebook(question):
    words = re.findall(r"\w+", question.lower())
    words = [w for w in words if w not in STOP_WORDS]

    if not words:
        return []

    # First try strict search
    search_query = " AND ".join(f'"{w}"' for w in words)

    cursor.execute("""
        SELECT title, url, content
        FROM secrets_fts
        WHERE secrets_fts MATCH ?
        ORDER BY bm25(secrets_fts)
        LIMIT 10
    """, (search_query,))

    results = cursor.fetchall()

    # Fallback if nothing found
    if not results:
        search_query = " OR ".join(f'"{w}"' for w in words)

        cursor.execute("""
            SELECT title, url, content
            FROM secrets_fts
            WHERE secrets_fts MATCH ?
            ORDER BY bm25(secrets_fts)
            LIMIT 5
        """, (search_query,))

        results = cursor.fetchall()

    return results


# ==========================
# GENERATE AI ANSWER
# ==========================

def ask_raven(question, history=None):

    if history is None:
        history = []
    results = search_casebook(question)

   if not results:

    context = """
No strong search results were found.

The user may be referring to the same concept using different wording.

Think carefully.

If you can infer the answer from related CaseBook information, explain it.

If the CaseBook truly contains no information about the topic,
say that the information does not appear to be documented.

Never invent facts.
"""

else:

    context = ""

    for title, url, content in results:

        context += f"""
TITLE:
{title}

URL:
{url}

CONTENT:
{content[:1500]}

-------------------------
"""

    context = ""

    for title, url, content in results:
        context += f"""
TITLE:
{title}

URL:
{url}

CONTENT:
{content[:1500]}

-------------------------
"""

    prompt = f"""
You are Raven, an AI assistant for Roblox Brookhaven mysteries.

The information below comes from the Brookhaven Mystery CaseBook.
It is your ONLY factual source.

Your job is to THINK about the information before answering.

Rules:

- Think carefully before answering.
- Read every CaseBook result before writing anything.
- Combine information from multiple CaseBook pages when useful.
- Never stop after reading only one result.
- Use your own words.
- Never copy large sections.
- Never invent information.
- If the evidence is incomplete, explain what is known and what is still unknown.
- If the CaseBook mentions something but does not explain it, explicitly say that.
- Only conclude that something is not documented after considering all retrieved information.
CASEBOOK RESULTS:

{context}

USER QUESTION:

{question}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Raven, a Roblox Brookhaven Mystery assistant. "
                    "Only use the provided CaseBook information. "
                    "Think carefully before answering. "
                    "Do not copy large passages. "
                    "Summarize naturally and never invent facts."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=500
    )

    return response.choices[0].message.content.strip()


# ==========================
# TERMINAL CHAT
# ==========================

def terminal_chat():

    print("\nRaven Terminal")
    print("Type 'exit' to quit.\n")

    while True:

        question = input("Ask Raven: ")

        if question.lower() in ["exit", "quit"]:
            break

        print("\nSearching CaseBook...")

        answer = ask_raven(question)

        print("\nAnswer:\n")
        print(answer)
        print("\n" + "=" * 80 + "\n")


# ==========================
# START TERMINAL ONLY
# ==========================

if __name__ == "__main__":
    terminal_chat()
