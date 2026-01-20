package tests;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;
import com.example.micronautcistatus.Application;

import static org.assertj.core.api.Assertions.assertThat;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ApiTest {

    private static String BASE_URL;
    private static HttpClient client;
    private static ApplicationContext context;
    private static EmbeddedServer server;
    private static String projectId;
    private static String buildId;
    private static String agentId;
    private static String userId;

    @BeforeAll
    static void setup() {
        context = Application.start(0);
        server = context.getBean(EmbeddedServer.class);
        BASE_URL = "http://localhost:" + server.getPort();
        client = HttpClient.newHttpClient();
    }

    @AfterAll
    static void tearDown() {
        if (server != null) {
            server.stop();
        }
        if (context != null) {
            context.close();
        }
    }

    private HttpResponse<String> sendRequest(HttpRequest request) throws Exception {
        return client.send(request, HttpResponse.BodyHandlers.ofString());
    }

    @Test
    @Order(1)
    void testCreateProject() throws Exception {
        String json = "{\"name\": \"test-project\", \"repoUrl\": \"http://github.com/test/repo\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(201);
        assertThat(response.body()).contains("\"name\":\"test-project\"");

        // Extract ID for future tests (simple extraction assuming JSON structure)
        projectId = response.body().split("\"id\":\"")[1].split("\"")[0];
    }

    @Test
    @Order(2)
    void testListProjects() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("test-project");
    }

    @Test
    @Order(3)
    void testGetProjectDetails() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects/" + projectId))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(projectId);
    }

    @Test
    @Order(4)
    void testUpdateProject() throws Exception {
        String json = "{\"name\": \"updated-project\", \"repoUrl\": \"http://github.com/test/repo\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects/" + projectId))
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("updated-project");
    }

    @Test
    @Order(5)
    void testTriggerBuild() throws Exception {
        String json = "{\"branch\": \"main\", \"commitHash\": \"abc1234\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects/" + projectId + "/builds"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(201);
        assertThat(response.body()).contains("QUEUED");

        buildId = response.body().split("\"id\":\"")[1].split("\"")[0];
    }

    @Test
    @Order(6)
    void testListBuildsForProject() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects/" + projectId + "/builds"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(buildId);
    }

    @Test
    @Order(7)
    void testGetBuildDetails() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/builds/" + buildId))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(buildId);
    }

    @Test
    @Order(8)
    void testGetBuildStatus() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/builds/" + buildId + "/status"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("status");
    }

    @Test
    @Order(9)
    void testGetBuildLogs() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/builds/" + buildId + "/logs"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("logs");
    }

    @Test
    @Order(10)
    void testListBuildArtifacts() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/builds/" + buildId + "/artifacts"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        // Assuming empty list or some default artifacts
    }

    @Test
    @Order(11)
    void testCancelBuild() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/builds/" + buildId + "/cancel"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("CANCELLED");
    }

    @Test
    @Order(12)
    void testRegisterAgent() throws Exception {
        String json = "{\"name\": \"agent-1\", \"capabilities\": [\"java\", \"docker\"]}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/agents"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(201);
        assertThat(response.body()).contains("agent-1");

        agentId = response.body().split("\"id\":\"")[1].split("\"")[0];
    }

    @Test
    @Order(13)
    void testListAgents() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/agents"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(agentId);
    }

    @Test
    @Order(14)
    void testGetAgentDetails() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/agents/" + agentId))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(agentId);
    }

    @Test
    @Order(15)
    void testUpdateAgentStatus() throws Exception {
        String json = "{\"status\": \"BUSY\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/agents/" + agentId + "/status"))
                .header("Content-Type", "application/json")
                .PUT(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("BUSY");
    }

    @Test
    @Order(16)
    void testGetBuildQueue() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/queue"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
    }

    @Test
    @Order(17)
    void testCreateUser() throws Exception {
        String json = "{\"username\": \"testuser\", \"email\": \"test@example.com\", \"role\": \"USER\"}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/users"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(201);
        assertThat(response.body()).contains("testuser");

        userId = response.body().split("\"id\":\"")[1].split("\"")[0];
    }

    @Test
    @Order(18)
    void testListUsers() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/users"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains(userId);
    }

    @Test
    @Order(19)
    void testGetUserDetails() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/users/" + userId))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("testuser");
    }

    @Test
    @Order(20)
    void testGetDailyStatistics() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/statistics/daily"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("totalBuilds");
    }

    @Test
    @Order(21)
    void testSystemHealth() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/system/health"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("UP");
    }

    @Test
    @Order(22)
    void testSystemVersion() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/system/version"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("version");
    }

    @Test
    @Order(23)
    void testGitWebhook() throws Exception {
        String json = "{\"ref\": \"refs/heads/main\", \"repository\": {\"url\": \"http://github.com/test/repo\"}}";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/webhooks/git"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("received");
    }

    @Test
    @Order(24)
    void testGetLatestReport() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/reports/latest"))
                .GET()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(200);
        assertThat(response.body()).contains("reportId");
    }

    @Test
    @Order(25)
    void testDeleteProject() throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/projects/" + projectId))
                .DELETE()
                .build();

        HttpResponse<String> response = sendRequest(request);
        assertThat(response.statusCode()).isEqualTo(204);
    }
}
