package me.andrii.kairo;

import static spark.Spark.*;
import java.io.*;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import org.json.*;

public class KairoBot {
    private static final String BOT_TOKEN = "8778508840:AAH_U3Sn-BYPrENXWK4LfPq9rxzH3lHLRXc";

    public static void main(String[] args) {
        // 1. Налаштування веб-порту для Render (з документації Screenshot_272.png)
        String portStr = System.getenv("PORT");
        int port = (portStr != null) ? Integer.parseInt(portStr) : 8080;
        
        ipAddress("0.0.0.0"); // Слухаємо зовнішні запити
        port(port);

        // Сторінка, яку Render буде перевіряти (Health Check)
        get("/", (req, res) -> "Kairo Bot Status: OK");

        System.out.println("Kairo Bot started on port " + port);

        // 2. Запуск логіки Telegram бота у окремому потоці
        new Thread(() -> {
            long lastUpdateId = 0;
            HttpClient client = HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(20))
                    .build();

            while (true) {
                try {
                    String url = "https://api.telegram.org/bot" + BOT_TOKEN + "/getUpdates?offset=" + (lastUpdateId + 1) + "&limit=10";
                    HttpRequest request = HttpRequest.newBuilder()
                            .uri(URI.create(url))
                            .timeout(Duration.ofSeconds(20))
                            .build();

                    HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

                    if (response.statusCode() == 200) {
                        JSONObject json = new JSONObject(response.body());
                        JSONArray updates = json.getJSONArray("result");
                        for (int i = 0; i < updates.length(); i++) {
                            JSONObject update = updates.getJSONObject(i);
                            lastUpdateId = update.getLong("update_id");

                            if (update.has("message")) {
                                JSONObject msg = update.getJSONObject("message");
                                if (msg.has("chat") && msg.has("text")) {
                                    String chatId = String.valueOf(msg.getJSONObject("chat").getLong("id"));
                                    sendMsg(chatId, "Бот Kairo офіційно активований на Render!");
                                }
                            }
                        }
                    }
                    Thread.sleep(2000); // Пауза між запитами
                } catch (Exception e) {
                    System.err.println("Bot loop error: " + e.getMessage());
                    try { Thread.sleep(5000); } catch (InterruptedException ie) {}
                }
            }
        }).start();
    }

    private static void sendMsg(String chatId, String text) {
        try {
            String url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage?chat_id=" + chatId + "&text=" + URLEncoder.encode(text, "UTF-8");
            HttpClient.newHttpClient().send(
                HttpRequest.newBuilder().uri(URI.create(url)).build(), 
                HttpResponse.BodyHandlers.ofString()
            );
        } catch (Exception e) {
            System.err.println("Send error: " + e.getMessage());
        }
    }
}
