import json
import os
import re
from typing import Dict, Any

import pytest

try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

try:
    import jsonschema
except Exception:  # pragma: no cover
    jsonschema = None  # type: ignore


BASE_URL = os.getenv("SYNAPSE_BASE_URL", "http://localhost:8080")


@pytest.mark.skipif(jsonschema is None, reason="jsonschema is required for contract validation")
def test_readme_present_and_sections():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    assert os.path.exists(readme_path), "README.md must exist"
    content = open(readme_path, "r", encoding="utf-8").read()

    required_sections = [
        "Service Information",
        "Interface Overview",
        "Input and Output Schemas",
        "Evaluation Metrics",
        "Testing Instructions",
    ]
    for section in required_sections:
        assert section in content, f"README should include section: {section}"


@pytest.mark.skipif(jsonschema is None, reason="jsonschema is required for contract validation")
def test_json_schemas_are_valid_json():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    text = open(readme_path, "r", encoding="utf-8").read()

    code_blocks = re.findall(r"```json\n([\s\S]*?)\n```", text)
    assert code_blocks, "At least one JSON schema code block is required"

    for block in code_blocks:
        # Ensure valid JSON
        schema = json.loads(block)
        assert isinstance(schema, dict), "Schema must be a JSON object"
        # Basic $schema presence
        assert "$schema" in schema, "Each schema should declare $schema"


@pytest.mark.skipif(requests is None or jsonschema is None, reason="requests and jsonschema required")
def test_healthcheck_contract_or_skip_if_unavailable():
    # Extract HealthCheck output schema from README
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    text = open(readme_path, "r", encoding="utf-8").read()
    blocks = re.findall(r"1\) HealthCheck Output Schema\n```json\n([\s\S]*?)\n```", text)
    assert blocks, "HealthCheck output schema must be documented"
    schema = json.loads(blocks[0])

    url = f"{BASE_URL}/health"
    try:
        resp = requests.get(url, timeout=2)
    except Exception:
        pytest.skip("Service not available; skipping live contract check")

    assert resp.status_code == 200
    payload = resp.json()
    jsonschema.validate(instance=payload, schema=schema)


@pytest.mark.skipif(requests is None or jsonschema is None, reason="requests and jsonschema required")
def test_auth_flow_contract_shapes_defined():
    # Ensure RegisterUser and LoginUser schemas exist and are valid JSON
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    text = open(readme_path, "r", encoding="utf-8").read()

    reg_in = re.findall(r"2\) RegisterUser Input Schema\n```json\n([\s\S]*?)\n```", text)
    reg_out = re.findall(r"RegisterUser Output Schema\n```json\n([\s\S]*?)\n```", text)
    log_in = re.findall(r"3\) LoginUser Input Schema\n```json\n([\s\S]*?)\n```", text)
    log_out = re.findall(r"LoginUser Output Schema\n```json\n([\s\S]*?)\n```", text)

    for name, blocks in {
        "RegisterUser Input": reg_in,
        "RegisterUser Output": reg_out,
        "LoginUser Input": log_in,
        "LoginUser Output": log_out,
    }.items():
        assert blocks, f"Missing schema block: {name}"
        json.loads(blocks[0])  # validates JSON


def _load_schema_by_title(readme_text: str, heading_regex: str) -> Dict[str, Any]:
    blocks = re.findall(heading_regex + r"\n```json\n([\s\S]*?)\n```", readme_text)
    assert blocks, f"Schema not found for heading regex: {heading_regex}"
    return json.loads(blocks[0])


@pytest.mark.skipif(requests is None or jsonschema is None, reason="requests and jsonschema required")
def test_message_contract_schemas_present():
    readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")
    text = open(readme_path, "r", encoding="utf-8").read()

    send_in = _load_schema_by_title(text, r"4\) SendMessage Input Schema")
    send_out = _load_schema_by_title(text, r"SendMessage Output Schema")
    list_out = _load_schema_by_title(text, r"5\) ListMessages Output Schema")

    assert send_in.get("type") == "object"
    assert send_out.get("type") == "object"
    assert list_out.get("type") == "object"


