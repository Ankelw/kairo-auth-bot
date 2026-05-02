import os
import threading
import requests
from flask import Flask
import telebot
from telebot import types

app = Flask(__name__)

@app.route('/')
def health_check():
    return "Kairo Bot is online!", 200

def run_web_server():
    # Render передает порт через переменную окружения
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- НАСТРОЙКИ (ВСТАВЬ СВОИ ДАННЫЕ) ---
BOT_TOKEN = "8716589061:AAFI52set5odaESDkcR9bokrXk0u_z_uzy0"
CRYPTO_TOKEN = "576413:AAyvNqln2VLIrrZy85jqOIQXqsKpTu5Gk8S"

# Актуальный адрес API (работает стабильнее)
API_URL = "https://pay.cryptopay.me/api" 
# ---------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Неделя — $1.5", callback_data="buy_1.5_week"),
        types.InlineKeyboardButton("Месяц — $3", callback_data="buy_3_month"),
        types.InlineKeyboardButton("Год — $10", callback_data="buy_10_year")
    )
    bot.send_message(
        message.chat.id, 
        "🛒 **Kairo Store**\nВыберите подходящий тариф подписки:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        _, amount, plan = call.data.split("_")
        headers = {'Crypto-Pay-API-Token': CRYPTO_TOKEN}
        payload = {
            'asset': 'USDT', 
            'amount': amount, 
            'description': f'Подписка Kairo: {plan}'
        }
        
        try:
            resp = requests.post(f"{API_URL}/createInvoice", json=payload, headers=headers).json()
            if resp.get('ok'):
                pay_url = resp['result']['pay_url']
                inv_id = resp['result']['invoice_id']
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💳 Оплатить (USDT)", url=pay_url))
                markup.add(types.InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_{inv_id}_{plan}"))
                
                bot.edit_message_text(
                    f"✨ Счет на {amount} USDT создан!\nПосле оплаты нажмите кнопку проверки.", 
                    call.message.chat.id, 
                    call.message.message_id, 
                    reply_markup=markup
                )
            else:
                err_msg = resp.get('error', {}).get('name', 'Unknown Error')
                bot.send_message(call.message.chat.id, f"❌ Ошибка Crypto Pay: {err_msg}")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ Ошибка соединения: {e}")

    elif call.data.startswith("check_"):
        _, inv_id, plan = call.data.split("_")
        headers = {'Crypto-Pay-API-Token': CRYPTO_TOKEN}
        try:
            res = requests.get(f"{API_URL}/getInvoices?invoice_ids={inv_id}", headers=headers).json()
            if res.get('ok') and res['result']['items'][0]['status'] == 'paid':
                bot.send_message(call.message.chat.id, f"🎉 Ура! Подписка **{plan}** успешно активирована!")
            else:
                bot.answer_callback_query(call.id, "❌ Оплата еще не поступила.", show_alert=True)
        except Exception:
            bot.answer_callback_query(call.id, "🚫 Ошибка при проверке счета.", show_alert=True)

if __name__ == "__main__":
    # Закрываем старые соединения перед стартом
    try:
        bot.stop_polling()
    except:
        pass
    
    # Запуск веб-сервера для Render в отдельном потоке
    threading.Thread(target=run_web_server, daemon=True).start()
    
    print("Бот Kairo запущен и готов к покупкам!")
    bot.polling(none_stop=True)
