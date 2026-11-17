#!/usr/bin/env python3
"""
Restore from a backup file downloaded with the "Download backup" button
(Backup & Restore page, admin).

    cd backend
    python3 scripts/restore_from_backup_file.py ~/Downloads/sarai-backup-2026-11-18-1030.json            # dry run
    python3 scripts/restore_from_backup_file.py ~/Downloads/sarai-backup-2026-11-18-1030.json --apply    # really restore

Reads MONGO_URL and DB_NAME from backend/.env or the environment — point them
at the database you want to restore INTO.

It MERGES, it never wipes: a record missing from the database is added; one
that is already there is replaced only if the file's copy is newer; nothing is
ever deleted. Run it without --apply first and read the counts.

Login accounts are not in a downloaded file (no password hashes leave the
server). Re-create them with scripts/create_admin.py and the User Management
page; the file's "users_reference" lists who had an account.
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from services.restore_service import merge_backup_data


async def main(path: str, apply: bool):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    with open(path) as f:
        data = json.load(f)
    if "collections" not in data:
        sys.exit("This does not look like a SARAI backup file (no 'collections').")
    db = AsyncIOMotorClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]
    print(f"Backup taken {data.get('timestamp')}  ->  database {os.environ['DB_NAME']}  ({'APPLYING' if apply else 'dry run'})")
    stats = await merge_backup_data(data, db, dry_run=not apply)
    for name, c in stats.items():
        print(f"  {name:24} in file {c['total']:6}   added {c['added']:6}   updated {c['updated']:6}   kept live {c['kept_live_version']:6}")
    print("Done." if apply else "Dry run only — nothing changed. Add --apply to restore.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    asyncio.run(main(a.file, a.apply))
