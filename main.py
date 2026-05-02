import os
import threading
import requests
from flask import Flask
import telebot
from telebot import types

# --- 1. ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Kairo Bot is online!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. НАСТРОЙКИ БОТА И ПЛАТЕЖКИ ---
# Токены взяты из твоих последних логов и сообщений
BOT_TOKEN = "8716589061:AAEz8Zi_E5ThRchDslu7vn7LL1Tq2V5qDl8"
CRYPTO_TOKEN = "575772:AAP15HrAvUKOG7yw9Fp05ZPKieCeCANfIF3" 

# Используем MAINNET, так как токен похож на реальный
API_URL = "https://pay.cryptometrika.io/api" 

bot = telebot.TeleBot(BOT_TOKEN)

# --- 3. ЛОГИКА МАГАЗИНА ---
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    btn_week = types.InlineKeyboardButton("Неделя — $1.5", callback_data="buy_1.5_week")
    btn_month = types.InlineKeyboardButton("Месяц — $3", callback_data="buy_3_month")
    btn_year = types.InlineKeyboardButton("Год — $10", callback_data="buy_10_year")
    
    markup.add(btn_week, btn_month, btn_year)
    
    bot.send_message(
        message.chat.id, 
        "🛒 **Kairo Store**\nВыберите срок подписки (Оплата через CryptoPay):", 
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("buy_"):
        _, amount, plan = call.data.split("_")
        
        # ИСПРАВЛЕНО: Теперь CRYPTO_TOKEN передается правильно в кавычках
        headers = {'Crypto-Pay-API-Token': CRYPTO_TOKEN}
        payload = {
            'asset': 'USDT',
            'amount': amount,
            'description': f'Kairo Client: {plan}',
            'allow_comments': False
        }
        
        try:
            resp = requests.post(f"{API_URL}/createInvoice", json=payload, headers=headers).json()
            if resp.get('ok'):
                pay_url = resp['result']['pay_url']
                inv_id = resp['result']['invoice_id']
                
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("Оплатить (USDT)", url=pay_url))
                markup.add(types.InlineKeyboardButton("Проверить оплату", callback_data=f"check_{inv_id}_{plan}"))
                
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"💳 **Счет на {amount} USDT готов!**\nСрок: {plan}\n\nНажмите кнопку ниже для оплаты. После перевода нажмите «Проверить».",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                # Если API вернул ошибку (например, неверный токен)
                error_code = resp.get('error', {}).get('name', 'Unknown Error')
                bot.send_message(call.message.chat.id, f"❌ Ошибка API: {error_code}\nПроверь, активен ли API токен в @CryptoBot")
        except Exception as e:
            bot.send_message(call.message.chat.id, "Ошибка при создании счета. Попробуй позже.")

    elif call.data.startswith("check_"):
        _, inv_id, plan = call.data.split("_")
        headers = {'Crypto-Pay-API-Token': CRYPTO_TOKEN}
        
        try:
            res = requests.get(f"{API_URL}/getInvoices?invoice_ids={inv_id}", headers=headers).json()
            status = res['result']['items'][0]['status']
            
            if status == 'paid':
                bot.send_message(
                    call.message.chat.id, 
                    f"🎉 **Успешно!**\nТвоя подписка на **{plan}** активирована."
                )
            else:
                bot.answer_callback_query(call.id, "❌ Оплата еще не найдена.", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "Ошибка проверки статуса.")

# --- 4. ЗАПУСК ---
if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()

    print("Kairo Bot is running!")
    bot.polling(none_stop=True)
