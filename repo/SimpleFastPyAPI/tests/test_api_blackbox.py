import os
from typing import Dict

import pytest
import requests


BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://127.0.0.1:8000")


def url(path: str) -> str:
    return f"{BASE_URL}{path}"


def create_user_payload(name: str = "Alice", email: str = "alice@example.com", password: str = "password1") -> Dict[str, str]:
    return {"name": name, "email": email, "password": password}


@pytest.mark.timeout(30)
def test_list_initial_users():
    r = requests.get(url("/users/"), timeout=10)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.timeout(30)
def test_crud_flow_create_get_update_delete():
    # Create
    c = requests.post(url("/users/"), json=create_user_payload(), timeout=10)
    assert c.status_code in (200, 201)
    created = c.json()
    assert set(["id", "name", "email", "password"]).issubset(created.keys())
    user_id = created["id"]

    # Get by id
    g = requests.get(url(f"/users/{user_id}"), timeout=10)
    assert g.status_code == 200
    got = g.json()
    assert got["id"] == user_id and got["email"] == "alice@example.com"

    # Update
    u = requests.put(url(f"/users/{user_id}"), json={"name": "Alice-2", "email": "alice2@example.com"}, timeout=10)
    assert u.status_code == 200
    assert u.json().get("message") == "User updated successfully"

    # Delete
    d = requests.delete(url(f"/users/{user_id}"), timeout=10)
    assert d.status_code == 200
    assert d.json().get("message") == "User deleted successfully"

    # Get after delete -> 404
    g2 = requests.get(url(f"/users/{user_id}"), timeout=10)
    assert g2.status_code == 404
    assert g2.json().get("detail") == "User not found"



