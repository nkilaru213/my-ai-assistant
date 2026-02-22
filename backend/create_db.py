
import os
from db_manager import DBManager

ROOT = os.path.dirname(__file__)
DB_PATH = os.path.join(ROOT, "assistant.db")

def main():
    if os.path.exists(DB_PATH):
        print(f"assistant.db already exists at {DB_PATH}")
    else:
        print(f"Creating assistant.db at {DB_PATH}")
    mgr = DBManager(DB_PATH)
    mgr.create_schema()
    print("Schema created/verified.")

if __name__ == "__main__":
    main()
