import pytest
import requests


@pytest.mark.api
def test_health(api_base_url, wait_for_service):
    resp = requests.get(f"{api_base_url}/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "service" in data
    assert "version" in data


@pytest.mark.api
def test_register_and_login(api_base_url, wait_for_service):
    creds = {"username": "test_user_login", "password": "Password123!"}
    # register
    r1 = requests.post(f"{api_base_url}/auth/register", json=creds)
    assert r1.status_code in (201, 409)
    # login
    r2 = requests.post(f"{api_base_url}/auth/login", json=creds)
    assert r2.status_code == 200
    assert "access_token" in r2.json()


@pytest.mark.api
def test_create_and_list_rooms(api_base_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    room = {"name": "general"}
    r = requests.post(f"{api_base_url}/rooms", json=room, headers=headers)
    assert r.status_code in (201, 409)
    # list
    q = requests.get(f"{api_base_url}/rooms?page=1&page_size=20")
    assert q.status_code == 200
    data = q.json()
    assert "rooms" in data and isinstance(data["rooms"], list)


@pytest.mark.api
def test_join_leave_room_and_messaging_flow(api_base_url, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    # ensure room
    room_name = "dev"
    cr = requests.post(f"{api_base_url}/rooms", json={"name": room_name}, headers=headers)
    if cr.status_code == 201:
        room_id = cr.json()["id"]
    else:
        # find by listing
        lst = requests.get(f"{api_base_url}/rooms?page=1&page_size=50").json()["rooms"]
        room_id = next((r["id"] for r in lst if r.get("name") == room_name), None)
        assert room_id is not None

    # join
    j = requests.post(f"{api_base_url}/rooms/{room_id}/join", headers=headers)
    assert j.status_code in (200, 201)
    assert j.json().get("joined") is True

    # send message
    msg = {"content": "hello world"}
    s = requests.post(f"{api_base_url}/rooms/{room_id}/messages", json=msg, headers=headers)
    assert s.status_code in (200, 201)
    sent = s.json()
    assert sent.get("content") == "hello world"
    assert sent.get("room_id") == room_id

    # fetch
    f = requests.get(f"{api_base_url}/rooms/{room_id}/messages?limit=50", headers=headers)
    assert f.status_code == 200
    messages = f.json().get("messages", [])
    assert any(m.get("content") == "hello world" for m in messages)

    # leave
    l = requests.post(f"{api_base_url}/rooms/{room_id}/leave", headers=headers)
    assert l.status_code in (200, 201)
    assert l.json().get("left") is True


