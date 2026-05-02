import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;

public class Main { // Твой основной класс бота

    public static void main(String[] args) {
        // 1. Запуск "живого" порта для Render
        startHealthCheckServer();

        // 2. Твоя логика запуска бота
        System.out.println("Kairo Bot starting...");
        // Здесь должен быть твой код запуска (например, TelegramBotsApi)
    }

    private static void startHealthCheckServer() {
        try {
            // Берем порт из переменной окружения Render, иначе 8080
            int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));
            
            HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", port), 0);
            server.createContext("/", exchange -> {
                String response = "Kairo Bot is online!";
                exchange.sendResponseHeaders(200, response.length());
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(response.getBytes());
                }
            });
            
            server.setExecutor(Executors.newSingleThreadExecutor());
            server.start();
            System.out.println("Health check server started on port " + port);
        } catch (Exception e) {
            System.err.println("Failed to start health check server: " + e.getMessage());
        }
    }
}
