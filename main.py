import asyncio
import sqlite3
import random
import string
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiocryptopay import AioCryptoPay

# --- НАЛАШТУВАННЯ ---
# Твій новий токен, який ти надіслав
API_TOKEN = "576355:AAxkBEag3mJdLyyIqHe0hUT0OOP0vYbPAoY"
# ВСТАВ СВІЙ ТОКЕН З @CryptoBot (My Apps) ТУТ:
CRYPTO_TOKEN = "576355:AAxkBEag3mJdLyyIqHe0hUT0OOP0vYbPAoY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
crypto = CryptoPay(token=CRYPTO_TOKEN)

# --- БАЗА ДАНИХ (sqlite3) ---
def init_db():
    conn = sqlite3.connect('kairo.db')
    cursor = conn.cursor()
    # Зберігаємо ID користувача, час закінчення та унікальний ключ
    cursor.execute('''CREATE TABLE IF NOT EXISTS subs 
                      (user_id INTEGER PRIMARY KEY, end_time DATETIME, generated_key TEXT)''')
    conn.commit()
    conn.close()

def generate_new_key(prefix="KAIRO"):
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{random_part}"

# --- ЛОГІКА ОПЛАТИ ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Неделя — $1.5", callback_data="buy_week"))
    builder.row(types.InlineKeyboardButton(text="Месяц — $3", callback_data="buy_month"))
    builder.row(types.InlineKeyboardButton(text="Год — $10", callback_data="buy_year"))
    
    await message.answer("🛒 **Kairo Store**\nВыбери срок подписки (Оплата через CryptoBot):", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    prices = {'week': 1.5, 'month': 3, 'year': 10}
    amount = prices[duration]
    
    # Створюємо інвойс у CryptoBot (USDT)
    invoice = await crypto.create_invoice(asset='USDT', amount=amount)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Оплатить USDT", url=invoice.pay_url))
    builder.row(types.InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"check_{invoice.invoice_id}_{duration}"))
    
    await callback.message.edit_text(
        f"💎 Тариф: **{duration}**\n💰 Сумма до оплаты: **{amount} USDT**\n\nНажми кнопку ниже для оплаты, затем нажми 'Проверить'.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    _, inv_id, duration = callback.data.split("_")
    
    # Перевіряємо статус рахунку через API
    invoices = await crypto.get_invoices(invoice_ids=inv_id)
    if invoices and invoices.status == 'paid':
        user_id = callback.from_user.id
        
        # Визначаємо термін згідно вибору
        days = {'week': 7, 'month': 30, 'year': 365}[duration]
        expire_date = datetime.now() + timedelta(days=days)
        
        # Генеруємо новий унікальний ключ для клієнта
        new_key = generate_new_key(prefix=f"KAIRO-{duration.upper()}")

        # Записуємо покупця в базу
        conn = sqlite3.connect('kairo.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO subs (user_id, end_time, generated_key) VALUES (?, ?, ?)",
                       (user_id, expire_date, new_key))
        conn.commit()
        conn.close()

        await callback.message.edit_text(
            f"✅ **Оплата прошла успешно!**\n\n🔑 Твой ключ: `{new_key}`\n⏳ Действует до: {expire_date.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Через {days} дн. бот автоматически аннулирует этот ключ.",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Оплата еще не подтверждена. Попробуйте через минуту.", show_alert=True)

# --- АВТОМАТИЧЕСКОЕ УДАЛЕНИЕ ---
async def check_loop():
    while True:
        try:
            conn = sqlite3.connect('kairo.db')
            cursor = conn.cursor()
            now = datetime.now()
            
            # Знаходимо всі прострочені підписки
            cursor.execute("SELECT user_id, generated_key FROM subs WHERE end_time < ?", (now,))
            expired = cursor.fetchall()
            
            for user in expired:
                uid, old_key = user
                try:
                    await bot.send_message(uid, f"🚫 **Время подписки истекло!**\nТвой ключ `{old_key}` удален из базы. Купи новый в /start")
                except: pass
                
                # Видаляємо з бази
                cursor.execute("DELETE FROM subs WHERE user_id = ?", (uid,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error checking subs: {e}")
            
        await asyncio.sleep(60) # Перевірка кожну хвилину

async def main():
    init_db()
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
