import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserProfileTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String PROFILE_ENDPOINT = "/api/users/profile";

    private static String sessionToken;
    private static String userId;
    private static String username = "profiletest001";
    private static String email = "profiletest001@example.com";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;

        // Register a test user
        String registerBody = String.format("""
                {
                    "username": "%s",
                    "email": "%s",
                    "password": "testpass123"
                }
                """, username, email);

        Response registerResponse = given()
                .contentType(ContentType.JSON)
                .body(registerBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .extract().response();

        userId = registerResponse.jsonPath().getString("userId");

        // Login to get session token
        String loginBody = String.format("""
                {
                    "username": "%s",
                    "password": "testpass123"
                }
                """, username);

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
    @DisplayName("Test get profile with valid session token")
    public void testGetProfileSuccess() {
        given()
                .header("Authorization", "Bearer " + sessionToken)
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("user.userId", equalTo(userId))
                .body("user.username", equalTo(username))
                .body("user.email", equalTo(email))
                .body("user.createdAt", notNullValue())
                .body("user.createdAt", matchesPattern("^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}.*"));
    }

    @Test
    @Order(2)
    @DisplayName("Test get profile without authorization header")
    public void testGetProfileWithoutAuth() {
        given()
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(3)
    @DisplayName("Test get profile with invalid session token")
    public void testGetProfileWithInvalidToken() {
        given()
                .header("Authorization", "Bearer invalid-token-12345")
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(4)
    @DisplayName("Test update profile with valid email")
    public void testUpdateProfileSuccess() {
        String newEmail = "newemail@example.com";
        String requestBody = String.format("""
                {
                    "email": "%s"
                }
                """, newEmail);

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("message", equalTo("Profile updated successfully"));

        // Verify the email was updated
        given()
                .header("Authorization", "Bearer " + sessionToken)
                .when()
                .get(PROFILE_ENDPOINT)
                .then()
                .statusCode(200)
                .body("user.email", equalTo(newEmail));
    }

    @Test
    @Order(5)
    @DisplayName("Test update profile with invalid email format")
    public void testUpdateProfileInvalidEmail() {
        String requestBody = """
                {
                    "email": "invalid-email-format"
                }
                """;

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(6)
    @DisplayName("Test update profile without authorization")
    public void testUpdateProfileWithoutAuth() {
        String requestBody = """
                {
                    "email": "unauthorized@example.com"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(7)
    @DisplayName("Test update profile with empty request body")
    public void testUpdateProfileEmptyBody() {
        String requestBody = "{}";

        given()
                .header("Authorization", "Bearer " + sessionToken)
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .put(PROFILE_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}
