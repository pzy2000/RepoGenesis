package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class OfferingApiTest extends BaseApiTest {

    @Test
    public void testCreateAndGetOffering() {
        // Setup dependencies
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-T1\", \"startDate\": \"2024-01-01\", \"endDate\": \"2024-05-01\" }").post("/api/terms").then().extract().path("id");
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"Eng\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T1\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");
        int courseId = given().contentType(ContentType.JSON).body("{ \"name\": \"C1\", \"credits\": 3, \"departmentId\": " + deptId + " }").post("/api/courses").then().extract().path("id");

        String offeringJson = String.format(
            "{ \"courseId\": %d, \"termId\": %d, \"teacherId\": %d, \"maxCapacity\": 50 }",
            courseId, termId, teacherId
        );

        int offeringId = given()
            .contentType(ContentType.JSON)
            .body(offeringJson)
        .when()
            .post("/api/offerings")
        .then()
            .statusCode(200)
            .body("maxCapacity", equalTo(50))
            .extract().path("id");

        given()
        .when()
            .get("/api/offerings/" + offeringId)
        .then()
            .statusCode(200)
            .body("courseId", equalTo(courseId));
    }
}
