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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- ЖЕСТКИЕ НАСТРОЙКИ ---
BOT_TOKEN = "8716589061:AAFI52set5odaESDkcR9bokrXk0u_z_uzy0"
CRYPTO_TOKEN = "576413:AAyvNq1n2VLIRrZy85jqOIQXqsKpTu5Gk8S"

# Обходим DNS: используем прямой IP и заголовок Host
API_URL = "https://104.26.11.164/api" # Прямой IP сервера cryptopay.me
HEADERS = {
    'Crypto-Pay-API-Token': CRYPTO_TOKEN,
    'Host': 'pay.cryptopay.me' # Обязательно для работы через IP
}
# -------------------------

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("Неделя — $1.5", callback_data="buy_1.5_week"),
        types.InlineKeyboardButton("Месяц — $3", callback_data="buy_3_month"),
        types.InlineKeyboardButton("Год — $10", callback_data="buy_10_year")
    )
    bot.send_message(message.chat.id, "🛒 **Kairo Store**\nВыберите подписку:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        _, amount, plan = call.data.split("_")
        payload = {'asset': 'USDT', 'amount': amount, 'description': f'Kairo: {plan}'}
        
        try:
            # Делаем запрос, игнорируя проверку SSL (потому что идем по IP)
            resp = requests.post(f"{API_URL}/createInvoice", json=payload, headers=HEADERS, verify=False).json()
            if resp.get('ok'):
                pay_url = resp['result']['pay_url']
                inv_id = resp['result']['invoice_id']
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("💳 Оплатить", url=pay_url))
                markup.add(types.InlineKeyboardButton("✅ Проверить", callback_data=f"check_{inv_id}_{plan}"))
                bot.edit_message_text(f"Счет на {amount} USDT создан!", call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, f"Ошибка API: {resp.get('error', {}).get('name')}")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ Прямое подключение не удалось: {e}")

    elif call.data.startswith("check_"):
        _, inv_id, plan = call.data.split("_")
        try:
            res = requests.get(f"{API_URL}/getInvoices?invoice_ids={inv_id}", headers=HEADERS, verify=False).json()
            if res.get('ok') and res['result']['items'][0]['status'] == 'paid':
                bot.send_message(call.message.chat.id, f"🎉 Подписка {plan} активна!")
            else:
                bot.answer_callback_query(call.id, "❌ Не оплачено.", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "Ошибка проверки.")

if __name__ == "__main__":
    try:
        bot.stop_polling()
    except:
        pass
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.polling(none_stop=True)
