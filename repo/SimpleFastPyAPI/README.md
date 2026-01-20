SimpleFastPyAPI Benchmark Spec

Overview
This benchmark targets a user management web microservice based on FastAPI and SQLite. It only provides requirement documentation and black-box test cases to evaluate implementations in a test-driven manner.

Running Environment
- Service default listening port: 8000 (can be run via container or process)
- Base URL: `http://127.0.0.1:8000`

API Definition (Users Microservice)
- API Name: `Users`
- Listening port: 8000
- Routes and contracts:
  - GET `/users/`
    - Input: No request body
    - Output: `User[]` list
  - GET `/users/{user_id}`
    - Input: Path parameter `user_id: integer`
    - Output: `User`
    - Error: `404 {"detail": "User not found"}`
  - POST `/users/`
    - Input: `UserCreate`
    - Output: `User` (including server-assigned `id`)
  - PUT `/users/{user_id}`
    - Input: Path parameter `user_id: integer`, request body `UserUpdate`
    - Output: `{"message": "User updated successfully"}`
    - Error: `404 {"detail": "User not found"}`
  - DELETE `/users/{user_id}`
    - Input: Path parameter `user_id: integer`
    - Output: `{"message": "User deleted successfully"}`
    - Error: `404 {"detail": "User not found"}`

Data Models (Schema)
- UserCreate
  - `name: string`
  - `email: string`
  - `password: string`
- UserUpdate
  - `name: string`
  - `email: string`
- User (response object)
  - `id: integer`
  - `name: string`
  - `email: string`
  - `password: string`


Testing Instructions
- Tests are black-box HTTP tests, only depending on running service instances.
- Specify the service under test address through environment variable `SERVICE_BASE_URL`, default `http://127.0.0.1:8000`.

Example Running
Service process (illustration):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Run tests (execute pytest in the directory above `repo_ori/SimpleFastPyAPI`):
```bash
pytest -q repo_ori/SimpleFastPyAPI/tests
```

Notes
- This benchmark document does not expose internal implementation details (does not include specific function names).
- Tests strictly follow the above interfaces, ports, and data contracts.
