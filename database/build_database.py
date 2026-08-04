import sqlite3

connection = sqlite3.connect("database/secrets.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS secrets (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    title TEXT,

    url TEXT,

    content TEXT

)
""")

connection.commit()

connection.close()

print("Database created!")