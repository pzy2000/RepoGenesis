package tests;

import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import com.example.chatgateway.ChatGatewayApplication;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT, classes = ChatGatewayApplication.class)
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

        @LocalServerPort
        private Integer port;

        private static String userId;
        private static String token;
        private static String groupId;
        private static String messageId;

        @BeforeEach
        public void setup() {
                RestAssured.port = port;
        }

        @Test
        @Order(1)
        public void testRegisterUser() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"testuser\",\n" +
                                                "  \"email\": \"test@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .statusCode(200)
                                .body("userId", notNullValue())
                                .body("username", equalTo("testuser"))
                                .body("createdAt", notNullValue())
                                .extract().path("userId");

                userId = response;
        }

        @Test
        @Order(2)
        public void testLoginUser() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"testuser\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/login")
                                .then()
                                .statusCode(200)
                                .body("token", notNullValue())
                                .body("userId", equalTo(userId))
                                .body("expiresIn", notNullValue())
                                .extract().path("token");

                token = response;
        }

        @Test
        @Order(3)
        public void testGetUserStatus() {
                given()
                                .pathParam("userId", userId)
                                .when()
                                .get("/api/users/{userId}/status")
                                .then()
                                .statusCode(200)
                                .body("userId", equalTo(userId))
                                .body("status", notNullValue())
                                .body("lastActive", notNullValue());
        }

        @Test
        @Order(4)
        public void testUpdateUserStatus() {
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("userId", userId)
                                .body("{\n" +
                                                "  \"status\": \"AWAY\"\n" +
                                                "}")
                                .when()
                                .put("/api/users/{userId}/status")
                                .then()
                                .statusCode(200)
                                .body("userId", equalTo(userId))
                                .body("status", equalTo("AWAY"))
                                .body("updatedAt", notNullValue());
        }

        @Test
        @Order(5)
        public void testSendPrivateMessage() {
                // Register a second user to receive message
                String recipientId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"recipient\",\n" +
                                                "  \"email\": \"recipient@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"senderId\": \"" + userId + "\",\n" +
                                                "  \"recipientId\": \"" + recipientId + "\",\n" +
                                                "  \"content\": \"Hello World\",\n" +
                                                "  \"type\": \"TEXT\"\n" +
                                                "}")
                                .when()
                                .post("/api/messages/send")
                                .then()
                                .statusCode(200)
                                .body("messageId", notNullValue())
                                .body("timestamp", notNullValue())
                                .body("status", equalTo("SENT"));
        }

        @Test
        @Order(6)
        public void testGetMessageHistory() {
                given()
                                .queryParam("userId1", userId)
                                .queryParam("userId2", "recipient_id_placeholder") // In a real scenario we'd use the ID
                                                                                   // from step 5
                                .when()
                                .get("/api/messages/history")
                                .then()
                                .statusCode(200)
                                .body("messages", notNullValue());
        }

        @Test
        @Order(7)
        public void testCreateGroup() {
                String response = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"creatorId\": \"" + userId + "\",\n" +
                                                "  \"name\": \"Test Group\",\n" +
                                                "  \"description\": \"A group for testing\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/create")
                                .then()
                                .statusCode(200)
                                .body("groupId", notNullValue())
                                .body("name", equalTo("Test Group"))
                                .body("createdAt", notNullValue())
                                .extract().path("groupId");

                groupId = response;
        }

        @Test
        @Order(8)
        public void testJoinGroup() {
                // Register a user to join
                String joinerId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"joiner\",\n" +
                                                "  \"email\": \"joiner@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + joinerId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/join")
                                .then()
                                .statusCode(200)
                                .body("groupId", equalTo(groupId))
                                .body("userId", equalTo(joinerId))
                                .body("role", equalTo("MEMBER"))
                                .body("joinedAt", notNullValue());
        }

        @Test
        @Order(9)
        public void testSendGroupMessage() {
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"senderId\": \"" + userId + "\",\n" +
                                                "  \"content\": \"Hello Group\",\n" +
                                                "  \"type\": \"TEXT\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/messages")
                                .then()
                                .statusCode(200)
                                .body("messageId", notNullValue())
                                .body("groupId", equalTo(groupId))
                                .body("timestamp", notNullValue());
        }

        @Test
        @Order(10)
        public void testListGroupMembers() {
                given()
                                .pathParam("groupId", groupId)
                                .when()
                                .get("/api/groups/{groupId}/members")
                                .then()
                                .statusCode(200)
                                .body("groupId", equalTo(groupId))
                                .body("members", hasSize(greaterThanOrEqualTo(1)));
        }

        @Test
        @Order(11)
        public void testLeaveGroup() {
                // Register a user to leave
                String leaverId = given()
                                .contentType(ContentType.JSON)
                                .body("{\n" +
                                                "  \"username\": \"leaver\",\n" +
                                                "  \"email\": \"leaver@example.com\",\n" +
                                                "  \"password\": \"password123\"\n" +
                                                "}")
                                .when()
                                .post("/api/users/register")
                                .then()
                                .extract().path("userId");

                // Join first
                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + leaverId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/join");

                given()
                                .contentType(ContentType.JSON)
                                .pathParam("groupId", groupId)
                                .body("{\n" +
                                                "  \"userId\": \"" + leaverId + "\"\n" +
                                                "}")
                                .when()
                                .post("/api/groups/{groupId}/leave")
                                .then()
                                .statusCode(200)
                                .body("success", equalTo(true));
        }

        @Test
        @Order(12)
        public void testSystemHealth() {
                given()
                                .when()
                                .get("/api/system/health")
                                .then()
                                .statusCode(200)
                                .body("status", equalTo("UP"))
                                .body("uptime", notNullValue())
                                .body("version", notNullValue());
        }
}
