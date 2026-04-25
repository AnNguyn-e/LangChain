import sqlite3

db_path = "kuni.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {[t[0] for t in tables]}")

# Check columns of documents
cursor.execute("PRAGMA table_info(documents);")
cols = cursor.fetchall()
print(f"Columns in 'documents': {[c[1] for c in cols]}")

# Check columns of chats
cursor.execute("PRAGMA table_info(chats);")
cols = cursor.fetchall()
print(f"Columns in 'chats': {[c[1] for c in cols]}")

conn.close()
