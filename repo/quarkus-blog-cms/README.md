# Blog Content Management System (CMS) Backend

## Project Overview
This project is a simplified backend for a Blog Content Management System, built using the **Quarkus** framework. It provides RESTful APIs to manage blog posts, categories, comments, and authors.

## Functional Description
The system allows users to:
1.  **Manage Posts**: Create, read, update, and delete blog posts.
2.  **Manage Categories**: Create, read, update, and delete categories for posts.
3.  **Manage Comments**: Add comments to posts and delete them.
4.  **Manage Authors**: Register authors and view author details.
5.  **Tags**: Retrieve available tags.

## API Interface Definitions

The service listens on port `8080`. All APIs use JSON for request and response bodies.

### 1. Create Post
- **Endpoint**: `POST /api/posts`
- **Description**: Creates a new blog post.
- **Input Schema**:
  ```json
  {
    "title": "String",
    "content": "String",
    "authorId": "String",
    "categoryId": "String",
    "tags": ["String"]
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "String",
    "title": "String",
    "content": "String",
    "authorId": "String",
    "categoryId": "String",
    "tags": ["String"],
    "createdAt": "String (ISO-8601)",
    "updatedAt": "String (ISO-8601)"
  }
  ```

### 2. Get Post by ID
- **Endpoint**: `GET /api/posts/{id}`
- **Description**: Retrieves a specific post by its ID.
- **Input Schema**: None (Path parameter)
- **Output Schema**: Same as Create Post output.

### 3. Update Post
- **Endpoint**: `PUT /api/posts/{id}`
- **Description**: Updates an existing post.
- **Input Schema**:
  ```json
  {
    "title": "String",
    "content": "String",
    "categoryId": "String",
    "tags": ["String"]
  }
  ```
- **Output Schema**: Same as Create Post output.

### 4. Delete Post
- **Endpoint**: `DELETE /api/posts/{id}`
- **Description**: Deletes a post.
- **Input Schema**: None
- **Output Schema**: Empty (204 No Content)

### 5. List Posts
- **Endpoint**: `GET /api/posts`
- **Description**: Retrieves a list of posts with optional pagination.
- **Query Parameters**: `page` (int, default 0), `size` (int, default 10)
- **Input Schema**: None
- **Output Schema**:
  ```json
  {
    "data": [
      {
        "id": "String",
        "title": "String",
        "authorId": "String",
        "categoryId": "String",
        "createdAt": "String"
      }
    ],
    "total": "Integer",
    "page": "Integer",
    "size": "Integer"
  }
  ```

### 6. Create Category
- **Endpoint**: `POST /api/categories`
- **Description**: Creates a new category.
- **Input Schema**:
  ```json
  {
    "name": "String",
    "description": "String"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "String",
    "name": "String",
    "description": "String"
  }
  ```

### 7. List Categories
- **Endpoint**: `GET /api/categories`
- **Description**: Retrieves all categories.
- **Input Schema**: None
- **Output Schema**: Array of Category objects.

### 8. Update Category
- **Endpoint**: `PUT /api/categories/{id}`
- **Description**: Updates a category.
- **Input Schema**:
  ```json
  {
    "name": "String",
    "description": "String"
  }
  ```
- **Output Schema**: Updated Category object.

### 9. Delete Category
- **Endpoint**: `DELETE /api/categories/{id}`
- **Description**: Deletes a category.
- **Input Schema**: None
- **Output Schema**: Empty (204 No Content)

### 10. Add Comment
- **Endpoint**: `POST /api/comments`
- **Description**: Adds a comment to a post.
- **Input Schema**:
  ```json
  {
    "postId": "String",
    "authorName": "String",
    "content": "String"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "String",
    "postId": "String",
    "authorName": "String",
    "content": "String",
    "createdAt": "String"
  }
  ```

### 11. Get Comments for Post
- **Endpoint**: `GET /api/posts/{id}/comments`
- **Description**: Retrieves all comments for a specific post.
- **Input Schema**: None
- **Output Schema**: Array of Comment objects.

### 12. Delete Comment
- **Endpoint**: `DELETE /api/comments/{id}`
- **Description**: Deletes a comment.
- **Input Schema**: None
- **Output Schema**: Empty (204 No Content)

### 13. Create Author
- **Endpoint**: `POST /api/authors`
- **Description**: Registers a new author.
- **Input Schema**:
  ```json
  {
    "name": "String",
    "email": "String",
    "bio": "String"
  }
  ```
- **Output Schema**:
  ```json
  {
    "id": "String",
    "name": "String",
    "email": "String",
    "bio": "String"
  }
  ```

### 14. Get Author
- **Endpoint**: `GET /api/authors/{id}`
- **Description**: Retrieves author details.
- **Input Schema**: None
- **Output Schema**: Author object.

### 15. Get Tags
- **Endpoint**: `GET /api/tags`
- **Description**: Retrieves a list of all unique tags used in posts.
- **Input Schema**: None
- **Output Schema**:
  ```json
  [ "String", "String", ... ]
  ```

## Metrics
- **Test Case Pass Rate**: 100%
- **Repo Pass Rate**: 100%
