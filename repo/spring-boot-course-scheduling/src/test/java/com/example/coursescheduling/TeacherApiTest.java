package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class TeacherApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetTeacher() {
        // Ensure dept exists
        String deptJson = "{ \"name\": \"Math\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");

        String teacherJson = "{ \"name\": \"John Doe\", \"departmentId\": " + deptId + " }";

        int teacherId = given()
            .contentType(ContentType.JSON)
            .body(teacherJson)
        .when()
            .post("/api/teachers")
        .then()
            .statusCode(200)
            .body("name", equalTo("John Doe"))
            .extract().path("id");

        given()
        .when()
            .get("/api/teachers/" + teacherId)
        .then()
            .statusCode(200)
            .body("departmentId", equalTo(deptId));
    }

    @Test
    public void testUpdateTeacher() {
        String deptJson = "{ \"name\": \"History\" }";
        int deptId = given().contentType(ContentType.JSON).body(deptJson).post("/api/departments").then().extract().path("id");
        String teacherJson = "{ \"name\": \"Jane Smith\", \"departmentId\": " + deptId + " }";
        int teacherId = given().contentType(ContentType.JSON).body(teacherJson).post("/api/teachers").then().extract().path("id");

        String updateJson = "{ \"name\": \"Jane Doe\", \"departmentId\": " + deptId + " }";
        given()
            .contentType(ContentType.JSON)
            .body(updateJson)
        .when()
            .put("/api/teachers/" + teacherId)
        .then()
            .statusCode(200)
            .body("name", equalTo("Jane Doe"));
    }
}
