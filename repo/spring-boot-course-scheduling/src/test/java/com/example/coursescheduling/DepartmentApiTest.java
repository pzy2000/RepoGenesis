package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class DepartmentApiTest extends BaseApiTest {

    @Test
    public void testCreateAndListDepartments() {
        String json = "{ \"name\": \"Computer Science\" }";

        given()
            .contentType(ContentType.JSON)
            .body(json)
        .when()
            .post("/api/departments")
        .then()
            .statusCode(200)
            .body("name", equalTo("Computer Science"));

        given()
        .when()
            .get("/api/departments")
        .then()
            .statusCode(200)
            .body("name", hasItem("Computer Science"));
    }

    @Test
    public void testDeleteDepartment() {
        String json = "{ \"name\": \"Physics\" }";
        int id = given().contentType(ContentType.JSON).body(json).post("/api/departments").then().extract().path("id");

        given()
        .when()
            .delete("/api/departments/" + id)
        .then()
            .statusCode(200);
    }
}
