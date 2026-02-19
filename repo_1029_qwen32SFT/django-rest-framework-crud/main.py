from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
import jwt
import datetime
import uuid

app = FastAPI()

# Configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Database simulation
users_db = {}
movies_db = {}
next_user_id = 1
next_movie_id = 1

# Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    password2: str
    email: str
    first_name: str
    last_name: str

class User(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str

class Token(BaseModel):
    access: str
    refresh: str

class TokenRefresh(BaseModel):
    access: str

class MovieCreate(BaseModel):
    title: str
    genre: str
    year: int

class Movie(MovieCreate):
    id: int
    creator: str

class MovieList(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Movie]

# Utility functions
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

# Authentication endpoints
@app.post("/api/v1/auth/register/", response_model=User)
def register_user(user: UserCreate):
    if user.password != user.password2:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    if user.username in [u["username"] for u in users_db.values()]:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    global next_user_id
    user_id = next_user_id
    next_user_id += 1
    
    users_db[user_id] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "password": user.password  # In a real app, this would be hashed
    }
    
    return users_db[user_id]

@app.post("/api/v1/auth/token/", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = next((u for u in users_db.values() if u["username"] == form_data.username), None)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    return {"access": access_token, "refresh": refresh_token}

@app.post("/api/v1/auth/refresh/", response_model=TokenRefresh)
def refresh_token(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)
    
    return {"access": access_token}

# Movie endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token/")

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    user = next((u for u in users_db.values() if u["username"] == username), None)
    if not user:
        raise credentials_exception
    return user

@app.get("/api/v1/movies/", response_model=MovieList)
def list_movies(title: Optional[str] = None, page: int = 1, current_user: User = Depends(get_current_user)):
    # Filter movies by title if provided
    filtered_movies = [m for m in movies_db.values() if current_user["id"] == m["creator_id"]]
    if title:
        filtered_movies = [m for m in filtered_movies if title.lower() in m["title"].lower()]
    
    # Pagination
    items_per_page = 10
    start = (page - 1) * items_per_page
    end = start + items_per_page
    paginated_movies = filtered_movies[start:end]
    
    # Build response
    return {
        "count": len(filtered_movies),
        "next": f"/api/v1/movies/?title={title}&page={page+1}" if end < len(filtered_movies) else None,
        "previous": f"/api/v1/movies/?title={title}&page={page-1}" if page > 1 else None,
        "results": paginated_movies
    }

@app.post("/api/v1/movies/", response_model=Movie, status_code=201)
def create_movie(movie: MovieCreate, current_user: User = Depends(get_current_user)):
    global next_movie_id
    movie_id = next_movie_id
    next_movie_id += 1
    
    movies_db[movie_id] = {
        "id": movie_id,
        "title": movie.title,
        "genre": movie.genre,
        "year": movie.year,
        "creator": current_user["username"],
        "creator_id": current_user["id"]
    }
    
    return movies_db[movie_id]

@app.get("/api/v1/movies/{movie_id}", response_model=Movie)
def get_movie(movie_id: int, current_user: User = Depends(get_current_user)):
    movie = movies_db.get(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if movie["creator_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this movie")
    return movie

@app.put("/api/v1/movies/{movie_id}", response_model=Movie)
def update_movie(movie_id: int, movie: MovieCreate, current_user: User = Depends(get_current_user)):
    if movie_id not in movies_db:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_data = movies_db[movie_id]
    if movie_data["creator_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this movie")
    
    movie_data.update({
        "title": movie.title,
        "genre": movie.genre,
        "year": movie.year
    })
    
    return movie_data

@app.delete("/api/v1/movies/{movie_id}", status_code=204)
def delete_movie(movie_id: int, current_user: User = Depends(get_current_user)):
    if movie_id not in movies_db:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    movie_data = movies_db[movie_id]
    if movie_data["creator_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this movie")
    
    del movies_db[movie_id]
    return {"detail": "Movie deleted successfully"}