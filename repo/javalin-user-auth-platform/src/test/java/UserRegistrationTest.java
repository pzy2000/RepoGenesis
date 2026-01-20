import io.restassured.RestAssured;
import io.restassured.http.ContentType;
import org.junit.jupiter.api.*;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class UserRegistrationTest {

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static final String REGISTER_ENDPOINT = "/api/users/register";

    @BeforeAll
    public static void setup() {
        app = com.example.auth.Main.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
        RestAssured.baseURI = BASE_URL;
    }

    @Test
    @Order(1)
    @DisplayName("Test successful user registration with valid data")
    public void testSuccessfulRegistration() {
        String requestBody = """
                {
                    "username": "testuser001",
                    "email": "testuser001@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(201)
                .body("success", equalTo(true))
                .body("message", equalTo("User registered successfully"))
                .body("userId", notNullValue())
                .body("userId", matchesPattern("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"));
    }

    @Test
    @Order(2)
    @DisplayName("Test registration with duplicate username")
    public void testDuplicateUsername() {
        String requestBody = """
                {
                    "username": "testuser001",
                    "email": "different@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(3)
    @DisplayName("Test registration with duplicate email")
    public void testDuplicateEmail() {
        String requestBody = """
                {
                    "username": "testuser002",
                    "email": "testuser001@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(4)
    @DisplayName("Test registration with invalid email format")
    public void testInvalidEmailFormat() {
        String requestBody = """
                {
                    "username": "testuser003",
                    "email": "invalid-email",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("email"));
    }

    @Test
    @Order(5)
    @DisplayName("Test registration with short password")
    public void testShortPassword() {
        String requestBody = """
                {
                    "username": "testuser004",
                    "email": "testuser004@example.com",
                    "password": "12345"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("password"));
    }

    @Test
    @Order(6)
    @DisplayName("Test registration with short username")
    public void testShortUsername() {
        String requestBody = """
                {
                    "username": "ab",
                    "email": "testuser005@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(7)
    @DisplayName("Test registration with long username")
    public void testLongUsername() {
        String requestBody = """
                {
                    "username": "thisusernameiswaytoolongandexceedstwentycharacters",
                    "email": "testuser006@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", containsStringIgnoringCase("username"));
    }

    @Test
    @Order(8)
    @DisplayName("Test registration with missing username")
    public void testMissingUsername() {
        String requestBody = """
                {
                    "email": "testuser007@example.com",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(9)
    @DisplayName("Test registration with missing email")
    public void testMissingEmail() {
        String requestBody = """
                {
                    "username": "testuser008",
                    "password": "password123"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @Test
    @Order(10)
    @DisplayName("Test registration with missing password")
    public void testMissingPassword() {
        String requestBody = """
                {
                    "username": "testuser009",
                    "email": "testuser009@example.com"
                }
                """;

        given()
                .contentType(ContentType.JSON)
                .body(requestBody)
                .when()
                .post(REGISTER_ENDPOINT)
                .then()
                .statusCode(400)
                .body("success", equalTo(false))
                .body("message", notNullValue());
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }
}
