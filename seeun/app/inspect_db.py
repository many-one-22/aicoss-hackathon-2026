import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "aicoss-hackathon-2026" / "minseo" / "data" / "processed" / "namdo.sqlite"


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        print(f"\n=== {table} ===")
        cursor.execute(f"PRAGMA table_info({table});")
        columns = cursor.fetchall()
        for col in columns:
            # col: (cid, name, type, notnull, default_value, pk)
            print(f"  {col[1]:<20} {col[2]}")

        col_names = [col[1] for col in columns]
        cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
        rows = cursor.fetchall()
        print("  --- sample rows ---")
        for row in rows:
            for name, value in zip(col_names, row):
                print(f"    {name}: {value}")
            print("    ---")

    conn.close()


if __name__ == "__main__":
    main()
