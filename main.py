import asyncio
import sqlite3
import random
import string
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- НАЛАШТУВАННЯ ---
API_TOKEN = "8716589061:AAEz8Zi_E5ThRchDslu7vn7LL1Tq2V5qDl8"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- БАЗА ДАНИХ ---
def init_db():
    conn = sqlite3.connect('kairo.db')
    cursor = conn.cursor()
    # Зберігаємо ID, час закінчення та сам згенерований ключ
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
    
    await message.answer("🛒 **Kairo Store**\nВыбери срок подписки:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    
    builder = InlineKeyboardBuilder()
    # Кнопка підтвердження оплати
    builder.row(types.InlineKeyboardButton(text="✅ Я оплатил (Проверить)", callback_data=f"confirm_{duration}"))
    
    await callback.message.edit_text(
        f"💎 Выбран тариф: **{duration}**\n\nНажми кнопку ниже после оплаты, чтобы получить персональный ключ.", 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("confirm_"))
async def auto_give_key(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    user_id = callback.from_user.id
    
    # ЛОГІКА ТЕРМІНІВ (Не плутаємо!)
    if duration == 'week':
        days = 7
        label = "Неделя"
    elif duration == 'month':
        days = 30
        label = "Месяц"
    elif duration == 'year':
        days = 365
        label = "Год"
    else:
        days = 0
        label = "Ошибка"

    expire_date = datetime.now() + timedelta(days=days)
    new_key = generate_new_key(prefix=f"KAIRO-{duration.upper()}")

    # Записуємо в базу конкретний термін для конкретного юзера
    conn = sqlite3.connect('kairo.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO subs (user_id, end_time, generated_key) VALUES (?, ?, ?)",
                   (user_id, expire_date, new_key))
    conn.commit()
    conn.close()

    await callback.message.edit_text(
        f"✅ **Оплата принята!**\n\n🔑 Твой персональный ключ: `{new_key}`\n📅 Тариф: **{label}**\n⏳ Действует до: {expire_date.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Бот автоматически удалит этот ключ из базы через {days} дн.",
        parse_mode="Markdown"
    )

# --- АВТО-ВИДАЛЕННЯ ---
async def check_loop():
    while True:
        try:
            conn = sqlite3.connect('kairo.db')
            cursor = conn.cursor()
            now = datetime.now()
            
            # Вибираємо всіх, у кого end_time вже в минулому
            cursor.execute("SELECT user_id, generated_key FROM subs WHERE end_time < ?", (now,))
            expired = cursor.fetchall()
            
            for user in expired:
                uid, old_key = user
                try:
                    await bot.send_message(uid, f"🚫 **Срок подписки истёк!**\nТвой ключ `{old_key}` удалён из системы. Для продления используй /start")
                except: pass
                
                cursor.execute("DELETE FROM subs WHERE user_id = ?", (uid,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")
            
        await asyncio.sleep(60) # Перевірка раз на хвилину

async def main():
    init_db()
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
