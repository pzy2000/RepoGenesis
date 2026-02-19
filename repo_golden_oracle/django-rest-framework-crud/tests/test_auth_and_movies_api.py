from typing import Dict


def register_user(client, payload: Dict[str, str]):
    return client.post("/api/v1/auth/register/", payload, format="json")


def obtain_token(client, username: str, password: str):
    return client.post(
        "/api/v1/auth/token/",
        {"username": username, "password": password},
        format="json",
    )


def test_register_and_obtain_token(api_client, user_data):
    # Register
    resp = register_user(api_client, user_data)
    assert resp.status_code == 201
    assert resp.data["username"] == user_data["username"]

    # Obtain token with same creds
    tok = obtain_token(api_client, user_data["username"], user_data["password"])
    assert tok.status_code == 200
    assert "access" in tok.data and tok.data["access"]
    assert "refresh" in tok.data and tok.data["refresh"]


def auth_headers(client, username: str, password: str):
    token_resp = obtain_token(client, username, password)
    access = token_resp.data["access"]
    return {"HTTP_AUTHORIZATION": f"Bearer {access}"}


def test_movies_crud_flow(api_client, create_user):
    # Create existing user to login with JWT
    user = create_user("bob", "StrongPassw0rd!")

    # List movies should require auth
    resp_anon = api_client.get("/api/v1/movies/")
    assert resp_anon.status_code in (401, 403)

    # Authenticated list is empty
    headers = auth_headers(api_client, "bob", "StrongPassw0rd!")
    resp_list = api_client.get("/api/v1/movies/", **headers)
    assert resp_list.status_code == 200
    assert resp_list.data["count"] == 0

    # Create a movie
    create_payload = {"title": "Inception", "genre": "Sci-Fi", "year": 2010}
    resp_create = api_client.post("/api/v1/movies/", create_payload, format="json", **headers)
    assert resp_create.status_code == 201
    movie_id = resp_create.data["id"]
    assert resp_create.data["title"] == "Inception"
    assert resp_create.data["creator"] == user.username

    # Retrieve movie
    resp_get = api_client.get(f"/api/v1/movies/{movie_id}/", **headers)
    assert resp_get.status_code == 200
    assert resp_get.data["id"] == movie_id
    assert resp_get.data["title"] == "Inception"

    # Update movie
    update_payload = {"title": "Inception 2", "genre": "Sci-Fi", "year": 2012}
    resp_update = api_client.put(
        f"/api/v1/movies/{movie_id}/",
        update_payload,
        format="json",
        **headers,
    )
    assert resp_update.status_code == 200
    assert resp_update.data["title"] == "Inception 2"

    # Filter support: by title icontains
    resp_filter = api_client.get("/api/v1/movies/?title=incep", **headers)
    assert resp_filter.status_code == 200
    assert resp_filter.data["count"] == 1

    # Delete movie
    resp_delete = api_client.delete(f"/api/v1/movies/{movie_id}/", **headers)
    assert resp_delete.status_code in (204, 200)

    # Ensure it's gone
    resp_list_after = api_client.get("/api/v1/movies/", **headers)
    assert resp_list_after.data["count"] == 0


