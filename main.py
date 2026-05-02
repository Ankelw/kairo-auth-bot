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

# Створюємо змінну для крипто, але не ініціалізуємо її одразу
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
    builder.row(types.InlineKeyboardButton(text="Неділя — $1.5", callback_data="buy_week"))
    builder.row(types.InlineKeyboardButton(text="Місяць — $3", callback_data="buy_month"))
    builder.row(types.InlineKeyboardButton(text="Рік — $10", callback_data="buy_year"))
    
    await message.answer("🛒 **Kairo Store**\nВиберіть термін підписки (Оплата USDT):", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    prices = {'week': 1.5, 'month': 3, 'year': 10}
    amount = prices[duration]
    
    # Використовуємо глобальний об'єкт крипто
    invoice = await crypto.create_invoice(asset='USDT', amount=amount)
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💳 Оплатити через CryptoBot", url=invoice.pay_url))
    builder.row(types.InlineKeyboardButton(text="✅ Перевірити оплату", callback_data=f"check_{invoice.invoice_id}_{duration}"))
    
    await callback.message.edit_text(
        f"💎 Тариф: **{duration}**\n💰 До сплати: **{amount} USDT**\n\nОплатіть за посиланням вище, потім натисніть кнопку перевірки.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    _, inv_id, duration = callback.data.split("_")
    
    invoices = await crypto.get_invoices(invoice_ids=inv_id)
    if invoices and invoices.status == 'paid':
        user_id = callback.from_user.id
        days = {'week': 7, 'month': 30, 'year': 365}[duration]
        expire_date = datetime.now() + timedelta(days=days)
        new_key = generate_new_key(prefix=f"KAIRO-{duration.upper()}")

        conn = sqlite3.connect('kairo.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO subs (user_id, end_time, generated_key) VALUES (?, ?, ?)",
                       (user_id, expire_date, new_key))
        conn.commit()
        conn.close()

        await callback.message.edit_text(
            f"✅ **Оплата пройшла!**\n\n🔑 Твій ключ: `{new_key}`\n⏳ Дійсний до: {expire_date.strftime('%d.%m.%Y %H:%M')}",
            parse_mode="Markdown"
        )
    else:
        await callback.answer("❌ Оплата ще не надійшла.", show_alert=True)

async def check_loop():
    while True:
        try:
            conn = sqlite3.connect('kairo.db')
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("SELECT user_id, generated_key FROM subs WHERE end_time < ?", (now,))
            expired = cursor.fetchall()
            for user in expired:
                uid, old_key = user
                try:
                    await bot.send_message(uid, f"🚫 Термін підписки на ключ `{old_key}` закінчився. Ключ видалено.")
                except: pass
                cursor.execute("DELETE FROM subs WHERE user_id = ?", (uid,))
            conn.commit()
            conn.close()
        except: pass
        await asyncio.sleep(60)

async def main():
    global crypto
    init_db()
    
    # Ініціалізуємо крипто ТІЛЬКИ ТУТ, всередині main
    crypto = AioCryptoPay(token=CRYPTO_TOKEN)
    
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
