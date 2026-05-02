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

# ТВОИ ДАННЫЕ (ПРОВЕРЬ ИХ)
BOT_TOKEN = "8716589061:AAEz8Zi_E5ThRchDslu7vn7LL1Tq2V5qDl8"
CRYPTO_TOKEN = "575772:AAP15HrAvUKOG7yw9Fp05ZPKieCeCANfIF3" 

# ВНИМАНИЕ: Если токен от @CryptoTestnetBot — добавь 'testnet-' в начало ссылки!
API_URL = "https://pay.cryptometrika.io/api" 

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_week = types.InlineKeyboardButton("Неделя — $1.5", callback_data="buy_1.5_week")
    btn_month = types.InlineKeyboardButton("Месяц — $3", callback_data="buy_3_month")
    btn_year = types.InlineKeyboardButton("Год — $10", callback_data="buy_10_year")
    markup.add(btn_week, btn_month, btn_year)
    bot.send_message(message.chat.id, "🛒 **Kairo Store**\nВыберите срок подписки:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        _, amount, plan = call.data.split("_")
        headers = {'Crypto-Pay-API-Token': CRYPTO_TOKEN}
        payload = {'asset': 'USDT', 'amount': amount, 'description': f'Kairo: {plan}'}
        
        try:
            # Печатаем ответ от API в консоль Render, чтобы ты видел ошибку, если она будет
            response = requests.post(f"{API_URL}/createInvoice", json=payload, headers=headers)
            resp = response.json()
            
            if resp.get('ok'):
                pay_url = resp['result']['pay_url']
                inv_id = resp['result']['invoice_id']
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Оплатить (USDT)", url=pay_url))
                markup.add(types.InlineKeyboardButton("Проверить", callback_data=f"check_{inv_id}_{plan}"))
                bot.edit_message_text(f"💳 Счет на {amount} USDT готов!", call.message.chat.id, call.message.message_id, reply_markup=markup)
            else:
                # Если API вернул ошибку, бот напишет её причину
                error_msg = resp.get('error', {}).get('name', 'Unknown Error')
                bot.send_message(call.message.chat.id, f"❌ Ошибка API: {error_msg}\nПроверь токен и URL!")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Ошибка связи с сервером оплаты.")

    elif call.data.startswith("check_"):
        _, inv_id, plan = call.data.split("_")
        headers = {'Crypto-Pay-API-Token': 575772:AAP15HrAvUKOG7yw9Fp05ZPKieCeCANfIF3}
        try:
            res = requests.get(f"{API_URL}/getInvoices?invoice_ids={inv_id}", headers=headers).json()
            if res['result']['items'][0]['status'] == 'paid':
                bot.send_message(call.message.chat.id, f"🎉 Подписка {plan} активирована!")
            else:
                bot.answer_callback_query(call.id, "❌ Оплата не найдена.", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "Ошибка проверки.")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()
    bot.polling(none_stop=True)
