import os
import re

import pytest
import requests


BASE_URL = os.environ.get("SERVICE_BASE_URL", "http://127.0.0.1:5000")


def url(path: str) -> str:
    return f"{BASE_URL}{path}"


def assert_html_page(r: requests.Response) -> None:
    assert r.status_code == 200
    text = r.text.lower()
    assert "<html" in text or "<!doctype html" in text


@pytest.mark.timeout(30)
def test_index_serves_form():
    r = requests.get(url("/"), timeout=10)
    assert_html_page(r)
    assert "rock-paper-scissors app" in r.text.lower()
    assert '<form action="/results" method="POST"' in r.text or '<form action="/results" method="post"' in r.text
    assert 'name="choice"' in r.text
    for opt in ("rock", "paper", "scissors"):
        assert f'value="{opt}"' in r.text


@pytest.mark.timeout(30)
@pytest.mark.parametrize("choice", ["rock", "paper", "scissors"]) 
def test_results_get_with_valid_choice(choice):
    r = requests.get(url(f"/results?choice={choice}"), timeout=10)
    assert_html_page(r)
    assert f"You chose: {choice}" in r.text
    # Computer choice is one of the options
    assert re.search(r"The computer chose: (rock|paper|scissors)", r.text) is not None
    # Results line exists
    assert "Results:" in r.text


@pytest.mark.timeout(30)
def test_results_get_with_invalid_choice_defaults_to_rock():
    r = requests.get(url("/results?choice=invalid"), timeout=10)
    assert_html_page(r)
    assert "You chose: rock" in r.text


@pytest.mark.timeout(30)
@pytest.mark.parametrize("choice", ["rock", "paper", "scissors"]) 
def test_results_post_with_valid_choice(choice):
    r = requests.post(url("/results"), data={"choice": choice}, timeout=10)
    assert_html_page(r)
    assert f"You chose: {choice}" in r.text
    assert re.search(r"The computer chose: (rock|paper|scissors)", r.text) is not None
    assert "Results:" in r.text


@pytest.mark.timeout(30)
def test_results_post_without_choice_defaults_to_rock():
    r = requests.post(url("/results"), data={}, timeout=10)
    assert_html_page(r)
    assert "You chose: rock" in r.text



