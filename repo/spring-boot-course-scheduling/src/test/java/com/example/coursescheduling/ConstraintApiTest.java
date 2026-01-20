package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ConstraintApiTest extends BaseApiTest {

    @Test
    public void testAddAndListConstraints() {
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"Math\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T_Constraint\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");

        String constraintJson = String.format(
            "{ \"teacherId\": %d, \"dayOfWeek\": 5, \"period\": 3, \"type\": \"UNAVAILABLE\" }",
            teacherId
        );

        given()
            .contentType(ContentType.JSON)
            .body(constraintJson)
        .when()
            .post("/api/constraints")
        .then()
            .statusCode(200)
            .body("type", equalTo("UNAVAILABLE"));

        given()
        .when()
            .get("/api/constraints")
        .then()
            .statusCode(200)
            .body("type", hasItem("UNAVAILABLE"));
    }
}
