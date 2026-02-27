import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserDeletionTest {

        private static io.javalin.Javalin app;
        private static String BASE_URL;
        private static final String REGISTER_ENDPOINT = "/api/users/register";
        private static final String LOGIN_ENDPOINT = "/api/users/login";
        private static final String DELETE_USER_ENDPOINT = "/api/users/{userId}";
        private static final String PROFILE_ENDPOINT = "/api/users/profile";

        private static String sessionToken;
        private static String userId;
        private static String username = "deletetest001";

        @BeforeAll
        public static void setup() {
                app = com.example.auth.Main.start(0);
                int port = app.port();
                BASE_URL = "http://localhost:" + port;
                RestAssured.baseURI = BASE_URL;
        }

        @BeforeEach
        public void setupEachTest() {
                // Register a new test user for each test with shorter unique identifier
                long timestamp = System.currentTimeMillis() % 10000; // Last 4 digits
                String registerBody = String.format("""
                                {
                                    "username": "%s%d",
                                    "email": "del%d@example.com",
                                    "password": "testpass123"
                                }
                                """, username, timestamp, timestamp);

                Response registerResponse = given()
                                .contentType(ContentType.JSON)
                                .body(registerBody)
                                .when()
                                .post(REGISTER_ENDPOINT)
                                .then()
                                .statusCode(201)
                                .extract().response();

                userId = registerResponse.jsonPath().getString("userId");

                // Login to get session token using the exact same username
                // Extract correct username from the register body we just sent
                String actualUsername = String.format("%s%d", username, timestamp);

                String loginBody = String.format("""
                                {
                                    "username": "%s",
                                    "password": "testpass123"
                                }
                                """, actualUsername);

                Response loginResponse = given()
                                .contentType(ContentType.JSON)
                                .body(loginBody)
                                .when()
                                .post(LOGIN_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .extract().response();

                sessionToken = loginResponse.jsonPath().getString("sessionToken");
        }

        @Test
        @Order(1)
        @DisplayName("Test successful user deletion")
        public void testSuccessfulUserDeletion() {
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .body("success", equalTo(true))
                                .body("message", equalTo("User deleted successfully"));
        }

        @Test
        @Order(2)
        @DisplayName("Test user deletion without authorization")
        public void testDeleteUserWithoutAuth() {
                given()
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", containsStringIgnoringCase("unauthorized"));
        }

        @Test
        @Order(3)
        @DisplayName("Test user deletion with invalid user ID")
        public void testDeleteUserInvalidId() {
                String invalidUserId = "00000000-0000-0000-0000-000000000000";

                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", invalidUserId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", containsStringIgnoringCase("unauthorized"));
        }

        @Test
        @Order(4)
        @DisplayName("Test cannot access profile after deletion")
        public void testProfileAccessAfterDeletion() {
                // Delete the user
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to access profile
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .when()
                                .get(PROFILE_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false));
        }

        @Test
        @Order(5)
        @DisplayName("Test cannot login after deletion")
        public void testLoginAfterDeletion() {
                // Get username before deletion
                Response profileResponse = given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .when()
                                .get(PROFILE_ENDPOINT)
                                .then()
                                .statusCode(200)
                                .extract().response();

                String deletedUsername = profileResponse.jsonPath().getString("user.username");

                // Delete the user
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to login
                String loginBody = String.format("""
                                {
                                    "username": "%s",
                                    "password": "testpass123"
                                }
                                """, deletedUsername);

                given()
                                .contentType(ContentType.JSON)
                                .body(loginBody)
                                .when()
                                .post(LOGIN_ENDPOINT)
                                .then()
                                .statusCode(401)
                                .body("success", equalTo(false))
                                .body("message", equalTo("Invalid credentials"));
        }

        @Test
        @Order(6)
        @DisplayName("Test delete already deleted user")
        public void testDeleteAlreadyDeletedUser() {
                // Delete the user first time
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(200);

                // Try to delete again
                given()
                                .header("Authorization", "Bearer " + sessionToken)
                                .pathParam("userId", userId)
                                .when()
                                .delete(DELETE_USER_ENDPOINT)
                                .then()
                                .statusCode(anyOf(equalTo(401), equalTo(404)))
                                .body("success", equalTo(false));
        }

        @AfterAll
        public static void tearDown() {
                app.stop();
        }
}
