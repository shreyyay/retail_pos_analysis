#!/usr/bin/env python3
"""
Provision a new store and print its API key.

Usage:
    python create_store.py STORE001 "My Store Name"
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cloud-backend"))

from app.database import SessionLocal, init_db
from app.models.tally import Store
from app.services.auth import generate_api_key


def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    store_id, store_name = sys.argv[1].strip(), sys.argv[2].strip()
    init_db()
    db = SessionLocal()
    try:
        if db.query(Store).filter(Store.store_id == store_id).first():
            print(f"ERROR: Store '{store_id}' already exists."); sys.exit(1)
        plaintext, key_hash = generate_api_key(store_id)
        db.add(Store(store_id=store_id, store_name=store_name, api_key_hash=key_hash, is_active=True))
        db.commit()
        print(f"\n{'='*55}")
        print(f"  Store created!")
        print(f"  Store ID  : {store_id}")
        print(f"  Store Name: {store_name}")
        print(f"  API Key   : {plaintext}")
        print(f"  ⚠  Save this key now — it cannot be recovered.")
        print(f"{'='*55}\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
