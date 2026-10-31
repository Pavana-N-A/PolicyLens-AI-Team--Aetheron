import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "data", "db", "policylens.db")
print("Inspecting DB at:", os.path.abspath(db_path))

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print(f"Total tables: {len(tables)}")

for t in sorted(tables):
    try:
        cur.execute(f"SELECT COUNT(*) FROM \"{t}\"")
        cnt = cur.fetchone()[0]
        print(f"  - {t:<25}: {cnt} rows")
    except Exception as e:
        print(f"  - {t:<25}: error ({e})")

# Sample check on policies table
print("\nPolicies in database:")
cur.execute("SELECT id, product_name, insurer_name, distributor_name, extraction_status, ocr_used FROM policies;")
for row in cur.fetchall():
    print(" ", row)

# Sample check on policy_fts
print("\nFTS5 search test for 'waiting period':")
cur.execute("SELECT policy_id, page_number, snippet(policy_fts, 2, '<b>', '</b>', '...', 15) FROM policy_fts WHERE policy_fts MATCH 'waiting' LIMIT 3;")
for row in cur.fetchall():
    print(" ", row)

conn.close()
