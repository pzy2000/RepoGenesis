Web Microservice Benchmark Case (Eve)

Overview
This benchmark targets a RESTful microservice built with an Eve-like API style backed by a document store. It provides only requirement documentation and black-box test cases to evaluate implementations using test-driven practices (no internal function names are exposed).

Service Information
- Listening port: 5001 (HTTP)
- Base URL: `http://127.0.0.1:5001`
- Namespace prefix: none (resources at root level)

Resources and API Contracts

Resource: `people`
- Collection endpoint: `/people`
- Item endpoint: `/people/{id}` where `{id}` is a server-generated identifier (string or integer). The server returns and expects ETag/If-Match headers for concurrency control on updates and deletes.

Schema (request/response)
- PeopleCreate (request body for POST `/people`)
  - `firstname: string`
  - `lastname: string`
  - `role: string` (e.g., admin, user)

- People (response object)
  - `_id: string|integer` (server-generated identifier)
  - `_etag: string` (entity tag used for concurrency)
  - `firstname: string`
  - `lastname: string`
  - `role: string`
  
Note: Some implementations may use `id` instead of `_id`. Clients should accept either `_id` or `id` as the identifier field.

Endpoints
- GET `/people`
  - Input: optional query parameters (implementation-defined filtering is allowed)
  - Output (200):
    - JSON document with at minimum an `_items` array containing `People` objects

- POST `/people`
  - Input: `PeopleCreate`
  - Output (201 or 200): `People` (includes identifier and ETag)
    - Identifier available as `_id` (preferred) or `id`
    - ETag available via response header `ETag` or body field `_etag`

- GET `/people/{id}`
  - Input: path parameter `id`
  - Output (200): `People`

- PUT `/people/{id}`
  - Headers: `If-Match: <etag>` (required)
  - Input: any subset or full set of updatable fields (`firstname`, `lastname`, `role`)
  - Output (200): updated `People` (with new `_etag`)
  - Errors (If-Match/ETag handling):
    - Missing `If-Match`: `428 Precondition Required` (or `400` in some implementations)
    - ETag mismatch: `412 Precondition Failed`

- DELETE `/people/{id}`
  - Headers: `If-Match: <etag>` (required)
  - Output: `204 No Content` (or `200 OK` in some implementations)
  - After successful deletion, a subsequent `GET /people/{id}` returns `404 Not Found` (or `410 Gone`)

Notes on Headers
- Responses for item resources include ETag header (e.g., `ETag: "abc123"`). The same value is also available as `_etag` property in the JSON body. Clients must provide `If-Match` with the correct ETag when issuing PUT or DELETE to prevent lost updates.

Testing Instructions
- Tests are black-box HTTP tests and assume the service is running and accessible.
- Service address is configured via environment variable `SERVICE_BASE_URL`, default `http://127.0.0.1:5001`.
- Run:
  - `pytest -q repo_ori/eve/tests`
