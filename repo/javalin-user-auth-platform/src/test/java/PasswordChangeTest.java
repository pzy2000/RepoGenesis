import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class PasswordChangeTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static final String CHANGE_PASSWORD_ENDPOINT = "/api/users/change-password";
    
    private static String sessionToken;
    private static String username = "passwordtest001";
    private static String originalPassword = "originalpass123";

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
                "email": "passwordtest001@example.com",
                "password": "%s"
            }
            """, username, originalPassword);

        given()
            .contentType(ContentType.JSON)
            .body(registerBody)
        .when()
            .post(REGISTER_ENDPOINT)
        .then()
            .statusCode(201);

        // Login to get session token
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "%s"
            }
            """, username, originalPassword);

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
    @DisplayName("Test successful password change")
    public void testSuccessfulPasswordChange() {
        String newPassword = "newpassword456";
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "%s"
            }
            """, originalPassword, newPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Password changed successfully"));

        // Verify login with new password works
        String loginBody = String.format("""
            {
                "username": "%s",
                "password": "%s"
            }
            """, username, newPassword);

        given()
            .contentType(ContentType.JSON)
            .body(loginBody)
        .when()
            .post(LOGIN_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true));

        // Update originalPassword for subsequent tests
        originalPassword = newPassword;
    }

    @Test
    @Order(2)
    @DisplayName("Test password change with incorrect current password")
    public void testIncorrectCurrentPassword() {
        String requestBody = """
            {
                "currentPassword": "wrongpassword",
                "newPassword": "newpassword789"
            }
            """;

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", containsStringIgnoringCase("current password"));
    }

    @Test
    @Order(3)
    @DisplayName("Test password change with short new password")
    public void testShortNewPassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "12345"
            }
            """, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", containsStringIgnoringCase("password"));
    }

    @Test
    @Order(4)
    @DisplayName("Test password change without authorization")
    public void testPasswordChangeWithoutAuth() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "newpassword999"
            }
            """, originalPassword);

        given()
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(401)
            .body("success", equalTo(false))
            .body("message", equalTo("Unauthorized"));
    }

    @Test
    @Order(5)
    @DisplayName("Test password change with missing current password")
    public void testMissingCurrentPassword() {
        String requestBody = """
            {
                "newPassword": "newpassword999"
            }
            """;

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", notNullValue());
    }

    @Test
    @Order(6)
    @DisplayName("Test password change with missing new password")
    public void testMissingNewPassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s"
            }
            """, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(400)
            .body("success", equalTo(false))
            .body("message", notNullValue());
    }

    @Test
    @Order(7)
    @DisplayName("Test password change with same password")
    public void testSamePassword() {
        String requestBody = String.format("""
            {
                "currentPassword": "%s",
                "newPassword": "%s"
            }
            """, originalPassword, originalPassword);

        given()
            .header("Authorization", "Bearer " + sessionToken)
            .contentType(ContentType.JSON)
            .body(requestBody)
        .when()
            .post(CHANGE_PASSWORD_ENDPOINT)
        .then()
            .statusCode(200)
            .body("success", equalTo(true))
            .body("message", equalTo("Password changed successfully"));
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}
