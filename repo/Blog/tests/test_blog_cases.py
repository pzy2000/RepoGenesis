from fastapi import status
from app.models.post import PostStatus

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "user_id" in data

def test_register_existing_user(client, test_user):
    """Test registering an existing user."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user["data"]["username"],
            "email": "another@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"

def test_login_user(client, test_user):
    """Test user login."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user["data"]["username"],
            "password": test_user["data"]["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user["data"]["username"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

def test_create_category(client, test_user):
    """Test creating a category."""
    response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={
            "name": "Technology",
            "description": "Tech news and reviews"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Technology"
    assert data["description"] == "Tech news and reviews"

def test_create_category_unauthorized(client):
    """Test creating a category without authentication."""
    response = client.post(
        "/api/v1/categories/",
        json={
            "name": "Technology",
            "description": "Tech news and reviews"
        }
    )
    assert response.status_code == 403

def test_get_categories(client, test_user):
    """Test retrieving categories."""
    # Create a category first
    client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Tech", "description": "Tech stuff"}
    )
    
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["categories"]) >= 1
    assert data["categories"][0]["name"] == "Tech"

def test_create_post(client, test_user):
    """Test creating a post."""
    # Create category first
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Coding", "description": "Coding stuff"}
    )
    category_id = cat_response.json()["id"]
    
    response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "My First Post",
            "content": "This is the content.",
            "excerpt": "This is the excerpt.",
            "category_id": category_id,
            "status": "published",
            "tags": ["python", "fastapi"]
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My First Post"
    assert data["author_id"] == test_user["user"].id

def test_create_post_invalid_category(client, test_user):
    """Test creating a post with invalid category."""
    response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "My First Post",
            "content": "This is the content.",
            "excerpt": "This is the excerpt.",
            "category_id": 999,
            "status": "published"
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"

def test_get_posts(client, test_user):
    """Test retrieving posts list."""
    # Create category and post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "News", "description": "News stuff"}
    )
    category_id = cat_response.json()["id"]
    
    client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "News Post",
            "content": "News content",
            "excerpt": "News excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    
    response = client.get("/api/v1/posts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) >= 1
    assert data["posts"][0]["title"] == "News Post"

def test_get_post_detail(client, test_user):
    """Test retrieving a single post."""
    # Create category and post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Detail", "description": "Detail stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Detail Post",
            "content": "Detail content",
            "excerpt": "Detail excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    post_id = post_response.json()["id"]
    
    response = client.get(f"/api/v1/posts/{post_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Detail Post"

def test_get_post_not_found(client):
    """Test retrieving a non-existent post."""
    response = client.get("/api/v1/posts/999")
    assert response.status_code == 404

def test_update_post(client, test_user):
    """Test updating a post."""
    # Create category and post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Update", "description": "Update stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Original Title",
            "content": "Original content",
            "excerpt": "Original excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    post_id = post_response.json()["id"]
    
    response = client.put(
        f"/api/v1/posts/{post_id}",
        headers=test_user["headers"],
        json={
            "title": "Updated Title",
            "content": "Updated content",
            "excerpt": "Updated excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

def test_update_post_unauthorized(client, test_user, test_user_2):
    """Test updating another user's post."""
    # User 1 creates post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Auth", "description": "Auth stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "User 1 Post",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    post_id = post_response.json()["id"]
    
    # User 2 tries to update
    response = client.put(
        f"/api/v1/posts/{post_id}",
        headers=test_user_2["headers"],
        json={
            "title": "Hacked Title",
            "content": "Hacked content",
            "excerpt": "Hacked excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "No permission to update this post"

def test_delete_post(client, test_user):
    """Test deleting a post."""
    # Create category and post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Delete", "description": "Delete stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Delete Post",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    post_id = post_response.json()["id"]
    
    response = client.delete(
        f"/api/v1/posts/{post_id}",
        headers=test_user["headers"]
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Post deleted successfully"
    
    # Verify deletion
    get_response = client.get(f"/api/v1/posts/{post_id}")
    assert get_response.status_code == 404

def test_delete_post_unauthorized(client, test_user, test_user_2):
    """Test deleting another user's post."""
    # User 1 creates post
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Delete Auth", "description": "Delete Auth stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "User 1 Post",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": category_id,
            "status": "published"
        }
    )
    post_id = post_response.json()["id"]
    
    # User 2 tries to delete
    response = client.delete(
        f"/api/v1/posts/{post_id}",
        headers=test_user_2["headers"]
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "No permission to delete this post"

def test_search_posts(client, test_user):
    """Test searching posts."""
    # Create category
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Search", "description": "Search stuff"}
    )
    category_id = cat_response.json()["id"]
    
    # Create posts
    client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Python Tutorial",
            "content": "Learn Python",
            "excerpt": "Python",
            "category_id": category_id,
            "status": "published"
        }
    )
    client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Java Tutorial",
            "content": "Learn Java",
            "excerpt": "Java",
            "category_id": category_id,
            "status": "published"
        }
    )
    
    response = client.get("/api/v1/posts/?search=Python")
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 1
    assert data["posts"][0]["title"] == "Python Tutorial"

def test_filter_posts_by_category(client, test_user):
    """Test filtering posts by category."""
    # Create categories
    cat1 = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Cat1", "description": "Cat1"}
    ).json()
    cat2 = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Cat2", "description": "Cat2"}
    ).json()
    
    # Create posts
    client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Post 1",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": cat1["id"],
            "status": "published"
        }
    )
    client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Post 2",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": cat2["id"],
            "status": "published"
        }
    )
    
    response = client.get(f"/api/v1/posts/?category_id={cat1['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["posts"]) == 1
    assert data["posts"][0]["title"] == "Post 1"

def test_get_draft_post_unauthorized(client, test_user, test_user_2):
    """Test that non-authors cannot see draft posts."""
    # User 1 creates draft
    cat_response = client.post(
        "/api/v1/categories/",
        headers=test_user["headers"],
        json={"name": "Draft", "description": "Draft stuff"}
    )
    category_id = cat_response.json()["id"]
    
    post_response = client.post(
        "/api/v1/posts/",
        headers=test_user["headers"],
        json={
            "title": "Draft Post",
            "content": "Content",
            "excerpt": "Excerpt",
            "category_id": category_id,
            "status": "draft"
        }
    )
    post_id = post_response.json()["id"]
    
    # User 2 tries to view
    response = client.get(
        f"/api/v1/posts/{post_id}",
        headers=test_user_2["headers"]
    )
    assert response.status_code == 404
