import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserLoginTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";
    private static final String LOGIN_ENDPOINT = "/api/users/login";
    private static String testUserId;

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;

        // Register a test user for login tests
        String registerBody = """
                {
                    "username": "logintest001",
                    "email": "logintest001@example.com",
                    "password": "testpass123"
                }
                """;

        Response response = given()
                .contentType(ContentType.JSON)
                .body(registerBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .extract().response();

        testUserId = response.jsonPath().getString("userId");
    }

    @Test
    @Order(1)
    @DisplayName("Test successful login with valid credentials")
    public void testSuccessfulLogin() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .body("success", equalTo(true))
                .body("message", equalTo("Login successful"))
                .body("sessionToken", notNullValue())
                .body("userId", equalTo(testUserId));
    }

    @Test
    @Order(2)
    @DisplayName("Test login with incorrect password")
    public void testIncorrectPassword() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "wrongpassword"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Invalid credentials"));
    }

    @Test
    @Order(3)
    @DisplayName("Test login with non-existent username")
    public void testNonExistentUsername() {
        String requestBody = """
                {
                    "username": "nonexistentuser",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(401)
                .body("success", equalTo(false))
                .body("message", equalTo("Invalid credentials"));
    }

    @Test
    @Order(4)
    @DisplayName("Test login with missing username")
    public void testMissingUsername() {
        String requestBody = """
                {
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(5)
    @DisplayName("Test login with missing password")
    public void testMissingPassword() {
        String requestBody = """
                {
                    "username": "logintest001"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(6)
    @DisplayName("Test login with empty username")
    public void testEmptyUsername() {
        String requestBody = """
                {
                    "username": "",
                    "password": "testpass123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @Test
    @Order(7)
    @DisplayName("Test login with empty password")
    public void testEmptyPassword() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": ""
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false));
    }

    @Test
    @Order(8)
    @DisplayName("Test multiple successful logins generate different session tokens")
    public void testMultipleLoginsGenerateDifferentTokens() {
        String requestBody = """
                {
                    "username": "logintest001",
                    "password": "testpass123"
                }
                """;

        String token1 = given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .extract().jsonPath().getString("sessionToken");

        String token2 = given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(LOGIN_ENDPOINT)
                .then()
                .statusCode(200)
                .extract().jsonPath().getString("sessionToken");

        Assertions.assertNotEquals(token1, token2, "Session tokens should be unique for each login");
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}
