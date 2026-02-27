package com.example.coursescheduling;

import io.restassured.http.ContentType;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

public class ScheduleApiTest extends BaseApiTest {

    @Test
    public void testAutoSchedule() {
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Auto\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");

        String autoJson = "{ \"termId\": " + termId + " }";

        given()
            .contentType(ContentType.JSON)
            .body(autoJson)
        .when()
            .post("/api/schedule/auto")
        .then()
            .statusCode(200)
            .body("status", notNullValue());
    }

    @Test
    public void testManualSchedule() {
        // Setup basic entities
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Manual\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");
        int deptId = given().contentType(ContentType.JSON).body("{ \"name\": \"CS\" }").post("/api/departments").then().extract().path("id");
        int teacherId = given().contentType(ContentType.JSON).body("{ \"name\": \"T_Man\", \"departmentId\": " + deptId + " }").post("/api/teachers").then().extract().path("id");
        int courseId = given().contentType(ContentType.JSON).body("{ \"name\": \"C_Man\", \"credits\": 3, \"departmentId\": " + deptId + " }").post("/api/courses").then().extract().path("id");
        int offeringId = given().contentType(ContentType.JSON).body(String.format("{ \"courseId\": %d, \"termId\": %d, \"teacherId\": %d, \"maxCapacity\": 50 }", courseId, termId, teacherId)).post("/api/offerings").then().extract().path("id");
        int classroomId = given().contentType(ContentType.JSON).body("{ \"name\": \"Room 101\", \"capacity\": 50, \"type\": \"NORMAL\" }").post("/api/classrooms").then().extract().path("id");

        String manualJson = String.format(
            "{ \"offeringId\": %d, \"classroomId\": %d, \"dayOfWeek\": 1, \"period\": 1 }",
            offeringId, classroomId
        );

        given()
            .contentType(ContentType.JSON)
            .body(manualJson)
        .when()
            .post("/api/schedule/manual")
        .then()
            .statusCode(200)
            .body("success", equalTo(true));
    }

    @Test
    public void testGetSchedules() {
        int termId = given().contentType(ContentType.JSON).body("{ \"name\": \"2024-Get\", \"startDate\": \"2024-09-01\", \"endDate\": \"2025-01-15\" }").post("/api/terms").then().extract().path("id");
        
        given()
        .when()
            .get("/api/schedule/term/" + termId)
        .then()
            .statusCode(200);
    }
}
