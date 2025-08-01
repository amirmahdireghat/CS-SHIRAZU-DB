import sqlite3

db_path = "./db.sqlite3"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all user-defined tables (excluding sqlite_sequence)
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = cursor.fetchall()

# Delete data from each table
for (table,) in tables:
    cursor.execute(f"DELETE FROM {table}")
    print(f"Cleared table: {table}")

# Reset auto-increment counters
cursor.execute("DELETE FROM sqlite_sequence")

conn.commit()
conn.close()

