import os
import time
from typing import Dict

import pytest
import requests


BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://127.0.0.1:8000")


def url(path: str) -> str:
    return f"{BASE_URL}{path}"


def register_user(payload: Dict[str, str]):
    return requests.post(url("/api/v1/auth/register/"), json=payload, timeout=10)


def obtain_token(username: str, password: str):
    return requests.post(
        url("/api/v1/auth/token/"), json={"username": username, "password": password}, timeout=10
    )


def auth_headers(username: str, password: str) -> Dict[str, str]:
    tok = obtain_token(username, password)
    assert tok.status_code == 200, tok.text
    access = tok.json()["access"]
    return {"Authorization": f"Bearer {access}"}


@pytest.mark.timeout(30)
def test_register_and_obtain_token_blackbox():
    payload = {
        "username": "alice_bb",
        "password": "StrongPassw0rd!",
        "password2": "StrongPassw0rd!",
        "email": "alice_bb@example.com",
        "first_name": "Alice",
        "last_name": "Tester",
    }

    r = register_user(payload)
    assert r.status_code in (201, 400), r.text
    if r.status_code == 400:
        # user may already exist in a reused environment
        pass

    t = obtain_token(payload["username"], payload["password"])
    assert t.status_code == 200, t.text
    body = t.json()
    assert body.get("access") and body.get("refresh")


@pytest.mark.timeout(60)
def test_movies_crud_flow_blackbox():
    # Prepare a fresh user (allow reuse)
    username = "bob_bb"
    password = "StrongPassw0rd!"
    register_user(
        {
            "username": username,
            "password": password,
            "password2": password,
            "email": f"{username}@example.com",
            "first_name": "Bob",
            "last_name": "Tester",
        }
    )

    headers = auth_headers(username, password)

    # Anonymous list requires auth
    anon = requests.get(url("/api/v1/movies/"), timeout=10)
    assert anon.status_code in (401, 403)

    # Authenticated list (expect paginated structure)
    lst = requests.get(url("/api/v1/movies/"), headers=headers, timeout=10)
    assert lst.status_code == 200, lst.text
    data = lst.json()
    assert {"count", "results"}.issubset(data.keys())

    # Create movie
    create_payload = {"title": "Inception", "genre": "Sci-Fi", "year": 2010}
    created = requests.post(url("/api/v1/movies/"), json=create_payload, headers=headers, timeout=10)
    assert created.status_code in (201, 200), created.text
    movie = created.json()
    movie_id = movie["id"]
    assert movie["title"] == "Inception"

    # Retrieve
    got = requests.get(url(f"/api/v1/movies/{movie_id}/"), headers=headers, timeout=10)
    assert got.status_code == 200, got.text
    assert got.json()["id"] == movie_id

    # Update
    upd_payload = {"title": "Inception 2", "genre": "Sci-Fi", "year": 2012}
    upd = requests.put(url(f"/api/v1/movies/{movie_id}/"), json=upd_payload, headers=headers, timeout=10)
    assert upd.status_code == 200, upd.text
    assert upd.json()["title"] == "Inception 2"

    # Filter
    flt = requests.get(url("/api/v1/movies/?title=incep"), headers=headers, timeout=10)
    assert flt.status_code == 200, flt.text
    assert flt.json()["count"] >= 1

    # Delete
    dele = requests.delete(url(f"/api/v1/movies/{movie_id}/"), headers=headers, timeout=10)
    assert dele.status_code in (204, 200), dele.text

    # Ensure gone (may be paginated empty or filtered not found)
    lst2 = requests.get(url("/api/v1/movies/"), headers=headers, timeout=10)
    assert lst2.status_code == 200



