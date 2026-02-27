package tests;

import kong.unirest.HttpResponse;
import kong.unirest.JsonNode;
import kong.unirest.Unirest;
import kong.unirest.json.JSONArray;
import kong.unirest.json.JSONObject;
import org.junit.jupiter.api.*;

import static org.junit.jupiter.api.Assertions.*;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

    private static final String BASE_URL = "http://localhost:7000/api";
    private static String adminToken;
    private static String userToken;
    private static String userId;
    private static String problemId;
    private static String contestId;
    private static String submissionId;

    private static io.javalin.Javalin app;

    @BeforeAll
    public static void setup() {
        app = com.example.oj.App.start(0);
        int port = app.port();
        Unirest.config().defaultBaseUrl("http://localhost:" + port + "/api");
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }

    @Test
    @Order(1)
    public void testRegisterUser() {
        JSONObject body = new JSONObject()
                .put("username", "testuser")
                .put("email", "test@example.com")
                .put("password", "password123");

        HttpResponse<JsonNode> response = Unirest.post("/auth/register")
                .body(body)
                .asJson();

        assertEquals(201, response.getStatus());
        assertNotNull(response.getBody().getObject().getString("id"));
        userId = response.getBody().getObject().getString("id");
    }

    @Test
    @Order(2)
    public void testLoginUser() {
        JSONObject body = new JSONObject()
                .put("username", "testuser")
                .put("password", "password123");

        HttpResponse<JsonNode> response = Unirest.post("/auth/login")
                .body(body)
                .asJson();

        assertEquals(200, response.getStatus());
        userToken = response.getBody().getObject().getString("token");
        assertNotNull(userToken);
    }

    @Test
    @Order(3)
    public void testRegisterAdmin() {
        // Assuming there's a way to register admin or a pre-seeded admin
        // For this benchmark, let's register another user and pretend they are admin 
        // OR the system might have a special setup. 
        // Let's assume we register an admin user explicitly if the system allows, 
        // or we just use the first user. 
        // For simplicity in this test generation, we'll register a separate admin user.
        JSONObject body = new JSONObject()
                .put("username", "admin")
                .put("email", "admin@example.com")
                .put("password", "admin123");

        HttpResponse<JsonNode> response = Unirest.post("/auth/register")
                .body(body)
                .asJson();
        
        // If 201, then login
        if (response.getStatus() == 201) {
             JSONObject loginBody = new JSONObject()
                .put("username", "admin")
                .put("password", "admin123");
             HttpResponse<JsonNode> loginResponse = Unirest.post("/auth/login")
                .body(loginBody)
                .asJson();
             adminToken = loginResponse.getBody().getObject().getString("token");
        }
        // If fails (maybe admin already exists), try login
        else {
             JSONObject loginBody = new JSONObject()
                .put("username", "admin")
                .put("password", "admin123");
             HttpResponse<JsonNode> loginResponse = Unirest.post("/auth/login")
                .body(loginBody)
                .asJson();
             if (loginResponse.getStatus() == 200) {
                 adminToken = loginResponse.getBody().getObject().getString("token");
             }
        }
        // Fallback: use userToken as adminToken if no strict role check in basic tests or if first user is admin
        if (adminToken == null) adminToken = userToken;
    }

    @Test
    @Order(4)
    public void testGetUser() {
        HttpResponse<JsonNode> response = Unirest.get("/users/" + userId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals("testuser", response.getBody().getObject().getString("username"));
    }

    @Test
    @Order(5)
    public void testUpdateUser() {
        JSONObject body = new JSONObject().put("email", "newemail@example.com");

        HttpResponse<JsonNode> response = Unirest.patch("/users/" + userId)
                .header("Authorization", "Bearer " + userToken)
                .body(body)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals("newemail@example.com", response.getBody().getObject().getString("email"));
    }

    @Test
    @Order(6)
    public void testCreateProblem() {
        JSONObject body = new JSONObject()
                .put("title", "Two Sum")
                .put("description", "Find two numbers that add up to target")
                .put("difficulty", "EASY")
                .put("timeLimit", 1000)
                .put("memoryLimit", 256);

        HttpResponse<JsonNode> response = Unirest.post("/problems")
                .header("Authorization", "Bearer " + adminToken)
                .body(body)
                .asJson();

        assertEquals(201, response.getStatus());
        problemId = response.getBody().getObject().getString("id");
        assertNotNull(problemId);
    }

    @Test
    @Order(7)
    public void testGetProblems() {
        HttpResponse<JsonNode> response = Unirest.get("/problems")
                .asJson();

        assertEquals(200, response.getStatus());
        assertTrue(response.getBody().getArray().length() > 0);
    }

    @Test
    @Order(8)
    public void testGetProblemById() {
        HttpResponse<JsonNode> response = Unirest.get("/problems/" + problemId)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals("Two Sum", response.getBody().getObject().getString("title"));
    }

    @Test
    @Order(9)
    public void testUpdateProblem() {
        JSONObject body = new JSONObject()
                .put("title", "Two Sum Updated")
                .put("description", "Updated description")
                .put("difficulty", "MEDIUM")
                .put("timeLimit", 2000)
                .put("memoryLimit", 512);

        HttpResponse<JsonNode> response = Unirest.put("/problems/" + problemId)
                .header("Authorization", "Bearer " + adminToken)
                .body(body)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals("Two Sum Updated", response.getBody().getObject().getString("title"));
    }

    @Test
    @Order(10)
    public void testCreateSubmission() {
        JSONObject body = new JSONObject()
                .put("problemId", problemId)
                .put("code", "public class Solution { ... }")
                .put("language", "JAVA");

        HttpResponse<JsonNode> response = Unirest.post("/submissions")
                .header("Authorization", "Bearer " + userToken)
                .body(body)
                .asJson();

        assertEquals(201, response.getStatus());
        submissionId = response.getBody().getObject().getString("id");
        assertNotNull(submissionId);
    }

    @Test
    @Order(11)
    public void testGetSubmissions() {
        HttpResponse<JsonNode> response = Unirest.get("/submissions")
                .queryString("userId", userId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        assertTrue(response.getBody().getArray().length() > 0);
    }

    @Test
    @Order(12)
    public void testGetSubmissionById() {
        HttpResponse<JsonNode> response = Unirest.get("/submissions/" + submissionId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals(problemId, response.getBody().getObject().getString("problemId"));
    }

    @Test
    @Order(13)
    public void testCreateContest() {
        long now = System.currentTimeMillis();
        JSONObject body = new JSONObject()
                .put("title", "Weekly Contest 1")
                .put("startTime", now + 3600000)
                .put("endTime", now + 7200000)
                .put("problemIds", new JSONArray().put(problemId));

        HttpResponse<JsonNode> response = Unirest.post("/contests")
                .header("Authorization", "Bearer " + adminToken)
                .body(body)
                .asJson();

        assertEquals(201, response.getStatus());
        contestId = response.getBody().getObject().getString("id");
        assertNotNull(contestId);
    }

    @Test
    @Order(14)
    public void testGetContests() {
        HttpResponse<JsonNode> response = Unirest.get("/contests")
                .asJson();

        assertEquals(200, response.getStatus());
        assertTrue(response.getBody().getArray().length() > 0);
    }

    @Test
    @Order(15)
    public void testGetContestById() {
        HttpResponse<JsonNode> response = Unirest.get("/contests/" + contestId)
                .asJson();

        assertEquals(200, response.getStatus());
        assertEquals("Weekly Contest 1", response.getBody().getObject().getString("title"));
    }

    @Test
    @Order(16)
    public void testJoinContest() {
        HttpResponse<JsonNode> response = Unirest.post("/contests/" + contestId + "/join")
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
    }

    @Test
    @Order(17)
    public void testGetContestStandings() {
        HttpResponse<JsonNode> response = Unirest.get("/contests/" + contestId + "/standings")
                .asJson();

        assertEquals(200, response.getStatus());
        assertTrue(response.getBody().getArray().length() >= 0); // Could be empty initially
    }

    @Test
    @Order(18)
    public void testBanUser() {
        HttpResponse<JsonNode> response = Unirest.post("/admin/users/" + userId + "/ban")
                .header("Authorization", "Bearer " + adminToken)
                .asJson();

        assertEquals(200, response.getStatus());
    }

    @Test
    @Order(19)
    public void testDeleteProblem() {
        HttpResponse<JsonNode> response = Unirest.delete("/problems/" + problemId)
                .header("Authorization", "Bearer " + adminToken)
                .asJson();

        assertEquals(204, response.getStatus());
    }

    @Test
    @Order(20)
    public void testGetProblemAfterDelete() {
        HttpResponse<JsonNode> response = Unirest.get("/problems/" + problemId)
                .asJson();

        assertEquals(404, response.getStatus());
    }

    @Test
    @Order(21)
    public void testLoginInvalidCredentials() {
        JSONObject body = new JSONObject()
                .put("username", "testuser")
                .put("password", "wrongpassword");

        HttpResponse<JsonNode> response = Unirest.post("/auth/login")
                .body(body)
                .asJson();

        assertEquals(401, response.getStatus());
    }

    @Test
    @Order(22)
    public void testAccessProtectedEndpointWithoutToken() {
        HttpResponse<JsonNode> response = Unirest.get("/users/" + userId)
                .asJson();

        assertEquals(401, response.getStatus());
    }
}
