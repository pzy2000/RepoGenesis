package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ClassroomApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetClassroom() {
        String json = "{ \"name\": \"Building A 101\", \"capacity\": 50, \"type\": \"MULTIMEDIA\" }";

        int id = given()
            .contentType(ContentType.JSON)
            .body(json)
        .when()
            .post("/api/classrooms")
        .then()
            .statusCode(200)
            .body("name", equalTo("Building A 101"))
            .extract().path("id");

        given()
        .when()
            .get("/api/classrooms/" + id)
        .then()
            .statusCode(200)
            .body("capacity", equalTo(50));
    }

    @Test
    public void testListClassrooms() {
        given()
        .when()
            .get("/api/classrooms")
        .then()
            .statusCode(200);
    }

    @Test
    public void testUpdateClassroom() {
        String json = "{ \"name\": \"Room 202\", \"capacity\": 30, \"type\": \"NORMAL\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/classrooms").then().extract().path("id");

        String updateJson = "{ \"name\": \"Room 202\", \"capacity\": 35, \"type\": \"NORMAL\" }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/classrooms/" + id)
        .then()
            .statusCode(200)
            .body("capacity", equalTo(35));
    }

    @Test
    public void testDeleteClassroom() {
        String json = "{ \"name\": \"Room 303\", \"capacity\": 20, \"type\": \"LAB\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/classrooms").then().extract().path("id");

        given()
        .when()
            .delete("/api/classrooms/" + id)
        .then()
            .statusCode(200);
    }
}
