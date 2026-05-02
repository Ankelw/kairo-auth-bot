package me.andrii.kairo;

import java.io.*;
import java.net.*;
import java.net.http.*;
import java.time.Duration;
import java.util.*;
import org.json.*;

public class KairoBot {
    private static final String BOT_TOKEN = "8778508840:AAH_U3Sn-BYPrENXWK4LfPq9rxzH3lHLRXc";
    
    public static void main(String[] args) throws Exception {
        System.out.println("Kairo Bot started on Render!");
        long lastUpdateId = 0;
        
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(20))
                .build();

        while (true) {
            try {
                String url = "https://api.telegram.org/bot" + BOT_TOKEN + "/getUpdates?offset=" + (lastUpdateId + 1) + "&limit=10";
                HttpRequest request = HttpRequest.newBuilder().uri(URI.create(url)).timeout(Duration.ofSeconds(20)).build();
                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
                
                if (response.statusCode() == 200) {
                    JSONObject json = new JSONObject(response.body());
                    if (json.has("result")) {
                        JSONArray updates = json.getJSONArray("result");
                        for (int i = 0; i < updates.length(); i++) {
                            JSONObject update = updates.getJSONObject(i);
                            lastUpdateId = update.getLong("update_id");
                            
                            if (update.has("message")) {
                                JSONObject msg = update.getJSONObject("message");
                                if (msg.has("chat") && msg.has("text")) {
                                    String chatId = String.valueOf(msg.getJSONObject("chat").getLong("id"));
                                    sendMsg(chatId, "Привіт! Бот Kairo тепер працює 24/7 на Render!");
                                }
                            }
                        }
                    }
                }
                Thread.sleep(3000); 
            } catch (Exception e) {
                System.err.println("Error: " + e.getMessage());
                Thread.sleep(10000);
            }
        }
    }

    private static void sendMsg(String chatId, String text) throws Exception {
        String url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage?chat_id=" + chatId + "&text=" + URLEncoder.encode(text, "UTF-8");
        HttpClient.newHttpClient().send(HttpRequest.newBuilder().uri(URI.create(url)).build(), HttpResponse.BodyHandlers.ofString());
    }
}
