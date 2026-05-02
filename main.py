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
API_TOKEN = "8716589061:AAEz8Zi_E5ThRchDslu7vn7LL1Tq2V5qDl8"
CRYPTO_TOKEN = "576355:AAxkBEag3mJdLyyIqHe0hUT0OOP0vYbPAoY"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
crypto = None 

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect('kairo.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subs 
                      (user_id INTEGER PRIMARY KEY, end_time DATETIME, generated_key TEXT)''')
    conn.commit()
    conn.close()

def generate_new_key(prefix="KAIRO"):
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{random_part}"

# --- ЛОГІКА БОТА ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Неделя — $1.5", callback_data="buy_week"))
    builder.row(types.InlineKeyboardButton(text="Месяц — $3", callback_data="buy_month"))
    builder.row(types.InlineKeyboardButton(text="Год — $10", callback_data="buy_year"))
    
    await message.answer("🛒 **Kairo Store**\nВиберіть термін підписки:", 
                         reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    prices = {'week': 1.5, 'month': 3, 'year': 10}
    amount = prices[duration]
    
    # Створюємо рахунок
    invoice = await crypto.create_invoice(asset='USDT', amount=amount)
    
    # ВИПРАВЛЕНО: Використовуємо bot_invoice_url замість pay_url
    payment_url = invoice.bot_invoice_url
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Оплатити через CryptoBot", url=payment_url))
    builder.row(types.InlineKeyboardButton(text="✅ Перевірити оплату", callback_data=f"check_{invoice.invoice_id}_{duration}"))
    
    await callback.message.edit_text(
        f"💎 Тариф: **{duration}**\n💰 Сума: **{amount} USDT**\n\nОплатіть за посиланням, потім натисніть кнопку перевірки.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    _, inv_id, duration = callback.data.split("_")
    
    invoices = await crypto.get_invoices(invoice_ids=inv_id)
    # Перевіряємо статус через список
    if invoices and invoices[0].status == 'paid':
        user_id = callback.from_user.id
        days = {'week': 7, 'month': 30, 'year': 365}[duration]
        expire_date = datetime.now() + timedelta(days=days)
        new_key = generate_new_key(prefix=f"KAIRO-{duration.upper()}")

        conn = sqlite3.connect('kairo.db')
        cursor = conn.cursor()
        expire_str = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT OR REPLACE INTO subs (user_id, end_time, generated_key) VALUES (?, ?, ?)",
                       (user_id, expire_str, new_key))
        conn.commit()
        conn.close()

        await callback.message.edit_text(
            f"✅ **Оплата підтверджена!**\n\n🔑 Твій ключ: `{new_key}`\n⏳ Діє до: {expire_str}",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Оплата ще не надійшла.", show_alert=True)

async def check_loop():
    while True:
        try:
            conn = sqlite3.connect('kairo.db')
            cursor = conn.cursor()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("SELECT user_id, generated_key FROM subs WHERE end_time < ?", (now,))
            expired = cursor.fetchall()
            for user in expired:
                uid, old_key = user
                try:
                    await bot.send_message(uid, f"🚫 Підписка на ключ `{old_key}` закінчилася.")
                except: pass
                cursor.execute("DELETE FROM subs WHERE user_id = ?", (uid,))
            conn.commit()
            conn.close()
        except: pass
        await asyncio.sleep(60)

async def main():
    global crypto
    init_db()
    crypto = AioCryptoPay(token=CRYPTO_TOKEN)
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
