# Javalin Online Judge Benchmark

## Functional Description
This project is a benchmark for an Online Code Evaluation Service (Online Judge) built with the Javalin framework. It simulates a platform where users can register, view coding problems, submit solutions, and participate in contests.

The system manages:
- **Users**: Registration, authentication, and profile management.
- **Problems**: Creating, reading, updating, and deleting coding problems.
- **Submissions**: Submitting code for problems and viewing results.
- **Contests**: Organizing problems into timed contests and tracking standings.

## Interfaces

The web service listens on port **7000**.

### Input/Output Schemas

Common types:
- `User`: `{ "id": "string", "username": "string", "email": "string", "role": "USER|ADMIN" }`
- `Problem`: `{ "id": "string", "title": "string", "description": "string", "difficulty": "EASY|MEDIUM|HARD", "timeLimit": number, "memoryLimit": number }`
- `Submission`: `{ "id": "string", "userId": "string", "problemId": "string", "code": "string", "language": "JAVA|PYTHON|CPP", "status": "PENDING|ACCEPTED|WRONG_ANSWER|TLE|MLE", "timestamp": number }`
- `Contest`: `{ "id": "string", "title": "string", "startTime": number, "endTime": number, "problemIds": ["string"] }`

### API Endpoints

#### Authentication
- `POST /api/auth/register`
    - Input: `{ "username": "string", "email": "string", "password": "string" }`
    - Output: `User` (201 Created)
- `POST /api/auth/login`
    - Input: `{ "username": "string", "password": "string" }`
    - Output: `{ "token": "string" }` (200 OK)

#### Users
- `GET /api/users/{id}`
    - Output: `User` (200 OK)
- `PATCH /api/users/{id}`
    - Input: `{ "email": "string" }` (optional fields)
    - Output: `User` (200 OK)

#### Problems
- `POST /api/problems` (Admin only)
    - Input: `Problem` (without ID)
    - Output: `Problem` (201 Created)
- `GET /api/problems`
    - Output: `[Problem]` (200 OK)
- `GET /api/problems/{id}`
    - Output: `Problem` (200 OK)
- `PUT /api/problems/{id}` (Admin only)
    - Input: `Problem`
    - Output: `Problem` (200 OK)
- `DELETE /api/problems/{id}` (Admin only)
    - Output: 204 No Content

#### Submissions
- `POST /api/submissions`
    - Input: `{ "problemId": "string", "code": "string", "language": "string" }`
    - Output: `Submission` (201 Created)
- `GET /api/submissions`
    - Query Params: `?userId={id}&problemId={id}`
    - Output: `[Submission]` (200 OK)
- `GET /api/submissions/{id}`
    - Output: `Submission` (200 OK)

#### Contests
- `POST /api/contests` (Admin only)
    - Input: `Contest` (without ID)
    - Output: `Contest` (201 Created)
- `GET /api/contests`
    - Output: `[Contest]` (200 OK)
- `GET /api/contests/{id}`
    - Output: `Contest` (200 OK)
- `POST /api/contests/{id}/join`
    - Output: 200 OK
- `GET /api/contests/{id}/standings`
    - Output: `[{ "userId": "string", "score": number }]` (200 OK)

#### Admin
- `POST /api/admin/users/{id}/ban`
    - Output: 200 OK

## Metrics
- **Test Case Pass Rate**: Percentage of API tests passed.
- **Repo Pass Rate**: Percentage of total requirements implemented correctly.

## Test Cases
The `tests/ApiTest.java` file contains JUnit 5 tests that verify the API implementation. The tests assume the server is running on `http://localhost:7000`.
