# Django REST Framework CRUD

Token-secured CRUD API for movies using Django REST framework.

Endpoints:

- Auth: `POST /api/v1/auth/register/`, `POST /api/v1/auth/token/`, `POST /api/v1/auth/refresh/`
- Movies: `GET/POST /api/v1/movies/`, `GET/PUT/DELETE /api/v1/movies/{id}/`

Features:

- JWT via Simple JWT
- Filtering with django-filter (`?title=incep` etc.)
- Pagination with page_size
- Object-level permissions (owner can modify)

Quickstart (dev):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
pytest -q
```


