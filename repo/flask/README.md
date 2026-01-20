Flask Microservice Benchmark

Description

This benchmark is used to evaluate the capabilities of a simple Flask-based web microservice. The service provides three interfaces: health check, string echo, and sum calculation. The implementation is not restricted, but it must satisfy the following external interface contract. The requirement documentation does not include specific function names; it only defines the microservice listening port, interface names, and input/output conventions.

Service Constraints

Port

The service listens on port 5000 by default.

API Definitions

GET /health

Semantics: Health check.

Input: None.

Output (application/json):

{
  "status": "ok"
}

Status Code: 200.

POST /echo

Semantics: Echoes the message in the request body and returns its length.

Input (application/json):

{
  "message": "<string>"
}

Output (application/json):

{
  "message": "<string>",
  "length": <int>
}

Status Code: 200. Should return 400 (application/json, including error reason) if input is missing or of an incorrect type.

GET /sum

Semantics: Sums two integers.

Input (query): a=<int>&b=<int>

Output (application/json):

{
  "result": <int>
}

Status Code: 200. Should return 400 (application/json, including error reason) if parameters are missing or not integers.

Testing Instructions

The tests directory provides black-box tests:

- Construct requests and assert response behavior based on the API contract.
- Use the Flask test client to construct a minimal application to verify the API contract and boundary conditions (missing input, type errors, etc.).

How to Run

Execute the following command in the repository root:

pytest -q repo_ori/flask/tests
