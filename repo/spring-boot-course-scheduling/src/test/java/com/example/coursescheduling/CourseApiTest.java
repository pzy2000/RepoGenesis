package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class CourseApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetCourse() {
        String deptJson = "{ \"name\": \"Science\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");

        String courseJson = "{ \"name\": \"Intro to Java\", \"credits\": 3, \"departmentId\": " + deptId + " }";

        int courseId = given()
            .contentType(ContentType.JSON)
            .body(courseJson)
        .when()
            .post("/api/courses")
        .then()
            .statusCode(200)
            .body("name", equalTo("Intro to Java"))
            .extract().path("id");

        given()
        .when()
            .get("/api/courses/" + courseId)
        .then()
            .statusCode(200)
            .body("credits", equalTo(3));
    }

    @Test
    public void testDeleteCourse() {
        String deptJson = "{ \"name\": \"Arts\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");
        String courseJson = "{ \"name\": \"Art History\", \"credits\": 2, \"departmentId\": " + deptId + " }";
        int courseId = given().contentType(ContentType.JSON).body(courseJson).post("/api/courses").then().extract().path("id");

        given()
        .when()
            .delete("/api/courses/" + courseId)
        .then()
            .statusCode(200);
    }
}
