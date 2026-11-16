"""
Run the real FastAPI app in-process against an in-memory MongoDB stand-in.

The older API test files in this folder (test_booking_system.py, test_iteration*.py,
test_p*.py, ...) call a LIVE deployed backend over HTTP and were written before
login was enforced, so today they need a server, a database and a token they
never send. This helper is the alternative: import server.py directly, swap
its `db` for mongomock-motor, and bypass login with a fixed test user. No
network, no MongoDB, no Render — just `pytest`.

Usage:

    from inprocess import api   # pytest fixture

    def test_something(api):
        api.seed("bookings", [{...}])
        res = api.client.post("/api/bookings/cancel", json={...})
        assert res.status_code == 200
        assert api.find_one("bookings", {"id": "b1"})["status"] == "cancelled"

    api.as_role("viewer")       # act as a different role for authorization tests
"""
import asyncio
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mongomock_motor", reason="pip install -r requirements-dev.txt")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")  # never connected to
os.environ.setdefault("DB_NAME", "sarai_inprocess_test")

from fastapi.testclient import TestClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

import server  # noqa: E402

DEFAULT_ROOMS = [
    {"id": "r1", "room_number": "C1-01", "category": "Cat I", "status": "available"},
    {"id": "r2", "room_number": "C1-02", "category": "Cat I", "status": "available"},
    {"id": "r3", "room_number": "C2-07", "category": "Cat II", "status": "available"},
    {"id": "r4", "room_number": "C2-08", "category": "Cat II", "status": "available"},
]
# Default rates: Cat I 470+30=500, Cat II 385+15=400, Non-Org 570+30=600
DEFAULT_SETTINGS = {"id": "s1", "is_setup_complete": True}


class InProcessAPI:
    def __init__(self):
        self.db = AsyncMongoMockClient()["sarai_inprocess_test"]
        server.db = self.db
        self.as_role("admin")
        # No `with`: startup events (scheduler, migrations) are not run.
        self.client = TestClient(server.app)
        self.seed("rooms", DEFAULT_ROOMS)
        self.seed("app_settings", [DEFAULT_SETTINGS])

    def as_role(self, role):
        user = {"id": f"test-{role}", "username": f"test-{role}", "role": role, "is_active": True}
        server.app.dependency_overrides[server.get_current_user_with_db] = lambda: user

    def seed(self, collection, docs):
        asyncio.run(self.db[collection].insert_many([dict(d) for d in docs]))

    def find_one(self, collection, query):
        return asyncio.run(self.db[collection].find_one(query, {"_id": 0}))

    def find(self, collection, query=None):
        return asyncio.run(self.db[collection].find(query or {}, {"_id": 0}).to_list(None))

    def close(self):
        server.app.dependency_overrides.clear()


@pytest.fixture
def api():
    harness = InProcessAPI()
    yield harness
    harness.close()
