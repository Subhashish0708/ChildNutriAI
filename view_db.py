"""
ChildNutri AI - Interactive SQLite Terminal Database Explorer
"""

import os
import sys
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "childnutri.db")

pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 120)

def view_database(table_name=None):
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # If specific table requested
    if table_name:
        print("\n" + "=" * 70)
        print(f"TABLE: {table_name.upper()}")
        print("=" * 70)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
            if not df.empty:
                print(df.to_string(index=False))
            else:
                print(f"Table '{table_name}' is currently empty.")
        except Exception as e:
            print(f"Error reading table '{table_name}': {e}")
        print("=" * 70 + "\n")
        conn.close()
        return

    # Show all tables and summary
    tables_df = pd.read_sql_query("SELECT name AS Table_Name FROM sqlite_master WHERE type='table';", conn)
    print("\n" + "=" * 70)
    print("SQLITE DATABASE OVERVIEW: database/childnutri.db")
    print("=" * 70)
    for idx, name in enumerate(tables_df["Table_Name"].tolist(), 1):
        count = pd.read_sql_query(f"SELECT COUNT(*) as c FROM {name}", conn).iloc[0]["c"]
        print(f"  {idx}. {name:<24} ({count} records)")

    # Key Tables preview
    for tbl in ["users", "children", "assessments", "predictions"]:
        if tbl in tables_df["Table_Name"].values:
            print("\n" + "-" * 70)
            print(f"TABLE: {tbl.upper()} (Top Records)")
            print("-" * 70)
            df = pd.read_sql_query(f"SELECT * FROM {tbl} LIMIT 5;", conn)
            if not df.empty:
                print(df.to_string(index=False))
            else:
                print(f"  (Table '{tbl}' is currently empty)")

    conn.close()
    print("\n" + "=" * 70)
    print("Tip: Run 'python view_db.py <table_name>' to view all records in a table.")
    print("Examples: python view_db.py users | python view_db.py children | python view_db.py assessments\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    view_database(target)
