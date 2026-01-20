package com.example.blog;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@QuarkusTest
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

    private static String createdPostId;
    private static String createdCategoryId;
    private static String createdCommentId;
    private static String createdAuthorId;

    @Test
    @Order(1)
    public void testCreateAuthor() {
        String authorJson = "{\"name\": \"John Doe\", \"email\": \"john@example.com\", \"bio\": \"Tech Writer\"}";
        createdAuthorId = given()
                .contentType(ContentType.JSON)
                .body(authorJson)
                .when()
                .post("/api/authors")
                .then()
                .statusCode(200) // Assuming 200 OK or 201 Created
                .body("id", notNullValue())
                .body("name", equalTo("John Doe"))
                .extract().path("id");
    }

    @Test
    @Order(2)
    public void testGetAuthor() {
        given()
                .pathParam("id", createdAuthorId)
                .when()
                .get("/api/authors/{id}")
                .then()
                .statusCode(200)
                .body("id", equalTo(createdAuthorId))
                .body("name", equalTo("John Doe"));
    }

    @Test
    @Order(3)
    public void testCreateCategory() {
        String categoryJson = "{\"name\": \"Tech\", \"description\": \"Technology related posts\"}";
        createdCategoryId = given()
                .contentType(ContentType.JSON)
                .body(categoryJson)
                .when()
                .post("/api/categories")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("name", equalTo("Tech"))
                .extract().path("id");
    }

    @Test
    @Order(4)
    public void testGetCategories() {
        given()
                .when()
                .get("/api/categories")
                .then()
                .statusCode(200)
                .body("size()", greaterThan(0));
    }

    @Test
    @Order(5)
    public void testUpdateCategory() {
        String updateJson = "{\"name\": \"Technology\", \"description\": \"Updated description\"}";
        given()
                .contentType(ContentType.JSON)
                .body(updateJson)
                .pathParam("id", createdCategoryId)
                .when()
                .put("/api/categories/{id}")
                .then()
                .statusCode(200)
                .body("name", equalTo("Technology"));
    }

    @Test
    @Order(6)
    public void testCreatePost() {
        String postJson = "{\"title\": \"Quarkus Intro\", \"content\": \"Introduction to Quarkus\", \"authorId\": \"" + createdAuthorId + "\", \"categoryId\": \"" + createdCategoryId + "\", \"tags\": [\"java\", \"quarkus\"]}";
        createdPostId = given()
                .contentType(ContentType.JSON)
                .body(postJson)
                .when()
                .post("/api/posts")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("title", equalTo("Quarkus Intro"))
                .body("tags", hasItems("java", "quarkus"))
                .extract().path("id");
    }

    @Test
    @Order(7)
    public void testGetPost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .get("/api/posts/{id}")
                .then()
                .statusCode(200)
                .body("id", equalTo(createdPostId))
                .body("title", equalTo("Quarkus Intro"));
    }

    @Test
    @Order(8)
    public void testUpdatePost() {
        String updateJson = "{\"title\": \"Quarkus Deep Dive\", \"content\": \"Deep dive into Quarkus\", \"categoryId\": \"" + createdCategoryId + "\", \"tags\": [\"java\", \"quarkus\", \"cloud\"]}";
        given()
                .contentType(ContentType.JSON)
                .body(updateJson)
                .pathParam("id", createdPostId)
                .when()
                .put("/api/posts/{id}")
                .then()
                .statusCode(200)
                .body("title", equalTo("Quarkus Deep Dive"))
                .body("tags", hasItem("cloud"));
    }

    @Test
    @Order(9)
    public void testListPosts() {
        given()
                .queryParam("page", 0)
                .queryParam("size", 10)
                .when()
                .get("/api/posts")
                .then()
                .statusCode(200)
                .body("data.size()", greaterThan(0))
                .body("total", notNullValue());
    }

    @Test
    @Order(10)
    public void testAddComment() {
        String commentJson = "{\"postId\": \"" + createdPostId + "\", \"authorName\": \"Reader\", \"content\": \"Great post!\"}";
        createdCommentId = given()
                .contentType(ContentType.JSON)
                .body(commentJson)
                .when()
                .post("/api/comments")
                .then()
                .statusCode(200)
                .body("id", notNullValue())
                .body("content", equalTo("Great post!"))
                .extract().path("id");
    }

    @Test
    @Order(11)
    public void testGetCommentsForPost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .get("/api/posts/{id}/comments")
                .then()
                .statusCode(200)
                .body("size()", greaterThan(0))
                .body("[0].content", equalTo("Great post!"));
    }

    @Test
    @Order(12)
    public void testGetTags() {
        given()
                .when()
                .get("/api/tags")
                .then()
                .statusCode(200)
                .body("$", hasItems("java", "quarkus", "cloud"));
    }

    @Test
    @Order(13)
    public void testDeleteComment() {
        given()
                .pathParam("id", createdCommentId)
                .when()
                .delete("/api/comments/{id}")
                .then()
                .statusCode(204);
    }

    @Test
    @Order(14)
    public void testDeletePost() {
        given()
                .pathParam("id", createdPostId)
                .when()
                .delete("/api/posts/{id}")
                .then()
                .statusCode(204);
    }

    @Test
    @Order(15)
    public void testDeleteCategory() {
        given()
                .pathParam("id", createdCategoryId)
                .when()
                .delete("/api/categories/{id}")
                .then()
                .statusCode(204);
    }
}
