package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class TermApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetTerm() {
        String termJson = "{ \"name\": \"2024-Fall\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }";

        int termId = given()
            .contentType(ContentType.JSON)
            .body(termJson)
        .when()
            .post("/api/terms")
        .then()
            .statusCode(200)
            .body("name", equalTo("2024-Fall"))
            .extract().path("id");

        given()
        .when()
            .get("/api/terms/" + termId)
        .then()
            .statusCode(200)
            .body("name", equalTo("2024-Fall"));
    }

    @Test
    public void testListTerms() {
        given()
        .when()
            .get("/api/terms")
        .then()
            .statusCode(200)
            .body("$", not(empty()));
    }

    @Test
    public void testUpdateTerm() {
        String termJson = "{ \"name\": \"2025-Spring\", \"startDate\": \"2025-02-01\", \"endDate\": \"2025-06-15\" }";
        int termId = given().contentType(ContentType.JSON).body(termJson).post("/api/terms").then().extract().path("id");

        String updateJson = "{ \"name\": \"2025-Spring-Updated\", \"startDate\": \"2025-02-01\", \"endDate\": \"2025-06-20\" }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/terms/" + termId)
        .then()
            .statusCode(200)
            .body("name", equalTo("2025-Spring-Updated"));
    }

    @Test
    public void testDeleteTerm() {
        String termJson = "{ \"name\": \"ToDelete\", \"startDate\": \"2025-01-01\", \"endDate\": \"2025-02-01\" }";
        int termId = given().contentType(ContentType.JSON).body(termJson).post("/api/terms").then().extract().path("id");

        given()
        .when()
            .delete("/api/terms/" + termId)
        .then()
            .statusCode(200);

        given()
        .when()
            .get("/api/terms/" + termId)
        .then()
            .statusCode(404);
    }
}
