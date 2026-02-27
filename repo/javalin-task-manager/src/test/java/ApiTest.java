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

    private static io.javalin.Javalin app;
    private static String BASE_URL;
    private static String userToken;
    private static int userId;
    private static int projectId;
    private static int taskId;

    @BeforeAll
    public static void setup() {
        app = com.example.javalintaskmanager.App.start(0);
        int port = app.port();
        BASE_URL = "http://localhost:" + port;
    }

    @AfterAll
    public static void tearDown() {
        app.stop();
    }

    @Test
    @Order(1)
    public void testRegisterUser() {
        JSONObject user = new JSONObject();
        user.put("username", "testuser");
        user.put("email", "test@example.com");
        user.put("password", "password123");

        HttpResponse<JsonNode> response = Unirest.post(BASE_URL + "/users")
                .header("Content-Type", "application/json")
                .body(user)
                .asJson();

        assertEquals(201, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertNotNull(body.get("id"));
        assertEquals("testuser", body.get("username"));
        assertEquals("test@example.com", body.get("email"));
        userId = body.getInt("id");
    }

    @Test
    @Order(2)
    public void testLoginUser() {
        JSONObject credentials = new JSONObject();
        credentials.put("email", "test@example.com");
        credentials.put("password", "password123");

        HttpResponse<JsonNode> response = Unirest.post(BASE_URL + "/users/login")
                .header("Content-Type", "application/json")
                .body(credentials)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertTrue(body.has("token"));
        userToken = body.getString("token");
    }

    @Test
    @Order(3)
    public void testCreateProject() {
        JSONObject project = new JSONObject();
        project.put("name", "Test Project");
        project.put("description", "A project for testing");

        HttpResponse<JsonNode> response = Unirest.post(BASE_URL + "/projects")
                .header("Authorization", "Bearer " + userToken)
                .header("Content-Type", "application/json")
                .body(project)
                .asJson();

        assertEquals(201, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertNotNull(body.get("id"));
        assertEquals("Test Project", body.get("name"));
        assertEquals(userId, body.getInt("ownerId"));
        projectId = body.getInt("id");
    }

    @Test
    @Order(4)
    public void testListProjects() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/projects")
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONArray body = response.getBody().getArray();
        assertTrue(body.length() > 0);
        boolean found = false;
        for (int i = 0; i < body.length(); i++) {
            JSONObject p = body.getJSONObject(i);
            if (p.getInt("id") == projectId) {
                found = true;
                break;
            }
        }
        assertTrue(found);
    }

    @Test
    @Order(5)
    public void testGetProjectDetails() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/projects/" + projectId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertEquals(projectId, body.getInt("id"));
        assertEquals("Test Project", body.getString("name"));
    }

    @Test
    @Order(6)
    public void testUpdateProject() {
        JSONObject update = new JSONObject();
        update.put("name", "Updated Project");
        update.put("description", "Updated description");

        HttpResponse<JsonNode> response = Unirest.put(BASE_URL + "/projects/" + projectId)
                .header("Authorization", "Bearer " + userToken)
                .header("Content-Type", "application/json")
                .body(update)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertEquals("Updated Project", body.getString("name"));
        assertEquals("Updated description", body.getString("description"));
    }

    @Test
    @Order(7)
    public void testCreateTask() {
        JSONObject task = new JSONObject();
        task.put("title", "Test Task");
        task.put("description", "Do something important");
        task.put("assigneeId", userId);

        HttpResponse<JsonNode> response = Unirest.post(BASE_URL + "/projects/" + projectId + "/tasks")
                .header("Authorization", "Bearer " + userToken)
                .header("Content-Type", "application/json")
                .body(task)
                .asJson();

        assertEquals(201, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertNotNull(body.get("id"));
        assertEquals("Test Task", body.getString("title"));
        assertEquals(projectId, body.getInt("projectId"));
        taskId = body.getInt("id");
    }

    @Test
    @Order(8)
    public void testGetTasksForProject() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/projects/" + projectId + "/tasks")
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONArray body = response.getBody().getArray();
        assertTrue(body.length() > 0);
        assertEquals(taskId, body.getJSONObject(0).getInt("id"));
    }

    @Test
    @Order(9)
    public void testGetTaskDetails() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/tasks/" + taskId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertEquals(taskId, body.getInt("id"));
        assertEquals("Test Task", body.getString("title"));
    }

    @Test
    @Order(10)
    public void testUpdateTask() {
        JSONObject update = new JSONObject();
        update.put("title", "Updated Task");
        update.put("description", "Updated task description");
        update.put("status", "IN_PROGRESS");
        update.put("assigneeId", userId);

        HttpResponse<JsonNode> response = Unirest.put(BASE_URL + "/tasks/" + taskId)
                .header("Authorization", "Bearer " + userToken)
                .header("Content-Type", "application/json")
                .body(update)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertEquals("Updated Task", body.getString("title"));
        assertEquals("IN_PROGRESS", body.getString("status"));
    }

    @Test
    @Order(11)
    public void testAddComment() {
        JSONObject comment = new JSONObject();
        comment.put("content", "This is a comment");

        HttpResponse<JsonNode> response = Unirest.post(BASE_URL + "/tasks/" + taskId + "/comments")
                .header("Authorization", "Bearer " + userToken)
                .header("Content-Type", "application/json")
                .body(comment)
                .asJson();

        assertEquals(201, response.getStatus());
        JSONObject body = response.getBody().getObject();
        assertNotNull(body.get("id"));
        assertEquals("This is a comment", body.getString("content"));
        assertEquals(taskId, body.getInt("taskId"));
    }

    @Test
    @Order(12)
    public void testGetComments() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/tasks/" + taskId + "/comments")
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONArray body = response.getBody().getArray();
        assertTrue(body.length() > 0);
        assertEquals("This is a comment", body.getJSONObject(0).getString("content"));
    }

    @Test
    @Order(13)
    public void testGetUserTasks() {
        HttpResponse<JsonNode> response = Unirest.get(BASE_URL + "/users/" + userId + "/tasks")
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(200, response.getStatus());
        JSONArray body = response.getBody().getArray();
        assertTrue(body.length() > 0);
        // Should find the task we assigned to this user
        boolean found = false;
        for(int i=0; i<body.length(); i++) {
            if(body.getJSONObject(i).getInt("id") == taskId) {
                found = true;
                break;
            }
        }
        assertTrue(found);
    }

    @Test
    @Order(14)
    public void testDeleteTask() {
        HttpResponse<JsonNode> response = Unirest.delete(BASE_URL + "/tasks/" + taskId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(204, response.getStatus());

        // Verify it's gone
        HttpResponse<JsonNode> check = Unirest.get(BASE_URL + "/tasks/" + taskId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();
        assertEquals(404, check.getStatus());
    }

    @Test
    @Order(15)
    public void testDeleteProject() {
        HttpResponse<JsonNode> response = Unirest.delete(BASE_URL + "/projects/" + projectId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();

        assertEquals(204, response.getStatus());

        // Verify it's gone
        HttpResponse<JsonNode> check = Unirest.get(BASE_URL + "/projects/" + projectId)
                .header("Authorization", "Bearer " + userToken)
                .asJson();
        assertEquals(404, check.getStatus());
    }
}
