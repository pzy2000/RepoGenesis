import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class SessionManagementTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String LOGOUT_ENDPOINT = "/api/users/logout";
    private static final String VALIDATE_SESSION_ENDPOINT = "/api/users/validate-session";
    private static final String PROFILE_ENDPOINT = "/api/users/profile";
    
    private static String sessionToken;
    private static String userId;
    private static String username = "sessiontest001";

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
                "email": "sessiontest001@example.com",
                "password": "testpass123"
            }
            """, username);

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
    @DisplayName("Test validate session with valid token")
    public void testValidateSessionSuccess() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("valid", equalTo(true))
            .body("userId", equalTo(userId));
    }

    @Test
    @Order(2)
    @DisplayName("Test validate session without authorization header")
    public void testValidateSessionWithoutAuth() {
        given()
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false))
            .body("message", equalTo("Invalid or expired session"));
    }

    @Test
    @Order(3)
    @DisplayName("Test validate session with invalid token")
    public void testValidateSessionInvalidToken() {
        given()
            .header("Authorization", "Bearer invalid-token-xyz")
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false))
            .body("message", equalTo("Invalid or expired session"));
    }

    @Test
    @Order(4)
    @DisplayName("Test logout with valid session")
    public void testLogoutSuccess() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .post(LOGOUT_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Logout successful"));
    }

    @Test
    @Order(5)
    @DisplayName("Test session is invalid after logout")
    public void testSessionInvalidAfterLogout() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("valid", equalTo(false));
    }

    @Test
    @Order(6)
    @DisplayName("Test cannot access protected endpoint after logout")
    public void testProtectedEndpointAfterLogout() {
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(PROFILE_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(7)
    @DisplayName("Test logout without authorization")
    public void testLogoutWithoutAuth() {
        given()
        .when()
            .post(LOGOUT_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false));
    }

    @Test
    @Order(8)
    @DisplayName("Test new login creates new valid session after logout")
    public void testNewLoginAfterLogout() {
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
            .body("success", equalTo(true))
            .extract().response();

        String newSessionToken = loginResponse.jsonPath().getString("sessionToken");

        // Verify new session is valid
        given()
            .header("Authorization", "Bearer " + newSessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("valid", equalTo(true));

        // Verify old session is still invalid
        given()
            .header("Authorization", "Bearer " + sessionToken)
        .when()
            .get(VALIDATE_SESSION_ENDPOINT)
        .then()
            .statusCode(401)
            .body("valid", equalTo(false));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}
