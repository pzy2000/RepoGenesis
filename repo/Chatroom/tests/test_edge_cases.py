import pytest
import requests


@pytest.mark.api
def test_unauthorized_access(api_base_url):
    r = requests.post(f"{api_base_url}/rooms", json={"name": "private"})
    assert r.status_code in (401, 403)


@pytest.mark.api
def test_duplicate_room_conflict(api_base_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    name = "unique_room"
    r1 = requests.post(f"{api_base_url}/rooms", json={"name": name}, headers=headers)
    assert r1.status_code in (201, 409)
    r2 = requests.post(f"{api_base_url}/rooms", json={"name": name}, headers=headers)
    assert r2.status_code == 409


@pytest.mark.api
def test_send_without_join_forbidden(api_base_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    # create a new room to minimize flakiness
    name = "temp_room"
    cr = requests.post(f"{api_base_url}/rooms", json={"name": name}, headers=headers)
    if cr.status_code == 201:
        room_id = cr.json()["id"]
    else:
        rooms = requests.get(f"{api_base_url}/rooms?page=1&page_size=100").json().get("rooms", [])
        room_id = next((r["id"] for r in rooms if r.get("name") == name), None)
    assert room_id

    s = requests.post(f"{api_base_url}/rooms/{room_id}/messages", json={"content": "x"}, headers=headers)
    assert s.status_code == 403


@pytest.mark.api
def test_unicode_and_length_limits(api_base_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    cr = requests.post(f"{api_base_url}/rooms", json={"name": "i18n"}, headers=headers)
    room_id = cr.json().get("id") if cr.status_code == 201 else None
    if not room_id:
        rooms = requests.get(f"{api_base_url}/rooms").json().get("rooms", [])
        room_id = next((r["id"] for r in rooms if r.get("name") == "i18n"), None)
    assert room_id

    requests.post(f"{api_base_url}/rooms/{room_id}/join", headers=headers)

    ok = requests.post(
        f"{api_base_url}/rooms/{room_id}/messages",
        json={"content": "Hello, world 🌍"},
        headers=headers,
    )
    assert ok.status_code in (200, 201)

    too_long = "a" * 1001
    bad = requests.post(
        f"{api_base_url}/rooms/{room_id}/messages",
        json={"content": too_long},
        headers=headers,
    )
    assert bad.status_code == 400


@pytest.mark.api
def test_pagination_bounds(api_base_url):
    r = requests.get(f"{api_base_url}/rooms?page=0&page_size=1000")
    assert r.status_code == 400


