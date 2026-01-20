Web Microservice Benchmark Case (rest-framework-crud)

Functionality Description

The application provides JWT-based movie resource management capabilities. Unauthenticated users cannot access movie resources. Authenticated users can create, query, update, and delete their own movie resources, with support for fuzzy filtering by title and pagination.

API Endpoints

Service listening port: 8000 (HTTP)

Namespace prefix: /api/v1

Authentication

POST /api/v1/auth/register/
Input schema
{
  "username": string,
  "password": string,
  "password2": string,
  "email": string,
  "first_name": string,
  "last_name": string
}
Output schema (201)
{
  "id": integer,
  "username": string,
  "email": string,
  "first_name": string,
  "last_name": string
}

POST /api/v1/auth/token/
Input schema
{
  "username": string,
  "password": string
}
Output schema (200)
{
  "access": string,
  "refresh": string
}

POST /api/v1/auth/refresh/
Input schema
{
  "refresh": string
}
Output schema (200)
{
  "access": string
}

Movie Resources

GET /api/v1/movies/
Headers: Authorization: Bearer <access>
Query parameters (optional): title=string (case-insensitive contains match), page=integer
Output schema (200, paginated)
{
  "count": integer,
  "next": string|null,
  "previous": string|null,
  "results": [
    {"id": integer, "title": string, "genre": string, "year": integer, "creator": string}
  ]
}

POST /api/v1/movies/
Headers: Authorization: Bearer <access>
Input schema
{
  "title": string,
  "genre": string,
  "year": integer
}
Output schema (201)
{"id": integer, "title": string, "genre": string, "year": integer, "creator": string}

GET /api/v1/movies/{id}/
Headers: Authorization: Bearer <access>
Output schema (200)
{"id": integer, "title": string, "genre": string, "year": integer, "creator": string}

PUT /api/v1/movies/{id}/
Headers: Authorization: Bearer <access>
Input schema same as POST /api/v1/movies/
Output schema (200) same as GET /api/v1/movies/{id}/

DELETE /api/v1/movies/{id}/
Headers: Authorization: Bearer <access>
Output: 204 No Content


Running Instructions (Benchmark Environment)
Prerequisites: The service under test is already running on local port 8000 (development framework such as Django).

Execute in this directory:
pip install -r requirements.txt  # if needed
pytest -q
