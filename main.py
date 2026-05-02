import os
import threading
import requests
import dns.resolver # Нужно установить: pip install dnspython
from flask import Flask
import telebot
from telebot import types

app = Flask(__name__)

# Функция для получения "честного" IP адреса
def get_crypto_ip():
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '8.8.4.4'] # Спрашиваем у Google, а не у провайдера
        answer = resolver.resolve('pay.cryptopay.me', 'A')
        return str(answer[0])
    except:
        return "104.26.11.164" # Запасной IP

CRYPTO_IP = get_crypto_ip()
API_URL = f"https://{CRYPTO_IP}/api"

BOT_TOKEN = "8716589061:AAFI52set5odaESDkcR9bokrXk0u_z_uzy0"
CRYPTO_TOKEN = "576413:AAyvNq1n2VLIRrZy85jqOIQXqsKpTu5Gk8S"

bot = telebot.TeleBot(BOT_TOKEN)

# В хендлере оплаты замени строку с requests на эту (добавили Host обратно):
# resp = requests.post(f"{API_URL}/createInvoice", json=payload, headers={'Crypto-Pay-API-Token': CRYPTO_TOKEN, 'Host': 'pay.cryptopay.me'}, verify=False).json())

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
