import os
from typing import Dict

import pytest
import requests


BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://127.0.0.1:5001")


def url(path: str) -> str:
    return f"{BASE_URL}{path}"


def create_person(payload: Dict[str, str]):
    return requests.post(url("/people"), json=payload, timeout=10)


def get_person(person_id: str):
    return requests.get(url(f"/people/{person_id}"), timeout=10)


def update_person(person_id: str, payload: Dict[str, str], etag: str):
    headers = {"If-Match": etag}
    return requests.put(url(f"/people/{person_id}"), json=payload, headers=headers, timeout=10)


def delete_person(person_id: str, etag: str):
    headers = {"If-Match": etag}
    return requests.delete(url(f"/people/{person_id}"), headers=headers, timeout=10)


@pytest.mark.timeout(30)
def test_people_collection_get_blackbox():
    r = requests.get(url("/people"), timeout=10)
    assert r.status_code == 200, r.text
    data = r.json()
    # Eve-style list: expect _items array
    assert isinstance(data.get("_items"), list)


@pytest.mark.timeout(60)
def test_people_crud_with_etag_blackbox():
    # Create
    payload = {"firstname": "Ada", "lastname": "Lovelace", "role": "admin"}
    created = create_person(payload)
    assert created.status_code in (201, 200), created.text
    body = created.json()
    person_id = body.get("_id") or body.get("id")
    assert person_id is not None

    # ETag available via header or body _etag
    etag = created.headers.get("ETag") or body.get("_etag")
    assert etag, f"missing ETag header/body: headers={created.headers} body={body}"

    # Retrieve
    got = get_person(str(person_id))
    assert got.status_code == 200, got.text
    b2 = got.json()
    assert (b2.get("_id") or b2.get("id")) == person_id
    etag2 = got.headers.get("ETag") or b2.get("_etag")
    assert etag2

    # Update requires If-Match
    upd_missing = requests.put(url(f"/people/{person_id}"), json={"role": "user"}, timeout=10)
    assert upd_missing.status_code in (428, 400, 412)

    upd = update_person(str(person_id), {"role": "user"}, etag2)
    assert upd.status_code == 200, upd.text
    b3 = upd.json()
    assert b3.get("role") == "user"
    etag3 = upd.headers.get("ETag") or b3.get("_etag")
    assert etag3 and etag3 != etag2

    # Delete requires If-Match
    del_missing = requests.delete(url(f"/people/{person_id}"), timeout=10)
    assert del_missing.status_code in (428, 400, 412)

    dele = delete_person(str(person_id), etag3)
    assert dele.status_code in (204, 200)

    # Ensure gone (implementation may return 404 or 410)
    after = get_person(str(person_id))
    assert after.status_code in (404, 410)


