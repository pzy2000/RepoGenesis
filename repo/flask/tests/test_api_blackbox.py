import json
import typing as t

import pytest
from flask import Flask, jsonify, request


def create_minimal_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> t.Any:
        return jsonify({"status": "ok"}), 200

    @app.post("/echo")
    def echo() -> t.Any:
        if not request.is_json:
            return jsonify({"error": "invalid content-type"}), 400
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or "message" not in data or not isinstance(data["message"], str):
            return jsonify({"error": "invalid payload"}), 400
        message: str = data["message"]
        return jsonify({"message": message, "length": len(message)}), 200

    @app.get("/sum")
    def sum_view() -> t.Any:
        a = request.args.get("a")
        b = request.args.get("b")
        try:
            a_int = int(a) if a is not None else None
            b_int = int(b) if b is not None else None
        except (TypeError, ValueError):
            return jsonify({"error": "parameters must be integers"}), 400
        if a_int is None or b_int is None:
            return jsonify({"error": "missing parameters"}), 400
        return jsonify({"result": a_int + b_int}), 200

    return app


@pytest.fixture()
def client():
    app = create_minimal_app()
    app.testing = True
    with app.test_client() as c:
        yield c


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"status": "ok"}


def test_echo_ok(client):
    payload = {"message": "hello"}
    resp = client.post("/echo", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"message": "hello", "length": 5}


def test_echo_invalid_content_type(client):
    resp = client.post("/echo", data="message=hello")
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert "error" in body


def test_echo_missing_message(client):
    resp = client.post("/echo", data=json.dumps({}), content_type="application/json")
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert "error" in body


def test_sum_ok(client):
    resp = client.get("/sum?a=2&b=3")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"result": 5}


def test_sum_missing_params(client):
    resp = client.get("/sum?a=2")
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert "error" in body


def test_sum_invalid_params(client):
    resp = client.get("/sum?a=x&b=3")
    assert resp.status_code == 400
    assert resp.is_json
    body = resp.get_json()
    assert "error" in body



