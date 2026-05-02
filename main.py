import asyncio
import time
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Твои токены
API_TOKEN = "8716589061:AAFlpEGmv6rYkhG7Nby-Fvbb3kptknDTj50"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Твои 5 приватных кодов
MASTER_KEYS = [
    "KAIRO-ADMIN-XP92-BR71",
    "KAIRO-OWNER-ML05-QV38",
    "KAIRO-TESTER-ZK14-PL90",
    "KAIRO-PRIVATE-WN63-DJ22",
    "KAIRO-ACCESS-RT87-GH44"
]

PRICES = {'week': 1.5, 'month': 3, 'year': 10}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Неделя — $1.5", callback_data="buy_week"))
    builder.row(types.InlineKeyboardButton(text="Месяц — $3", callback_data="buy_month"))
    builder.row(types.InlineKeyboardButton(text="Год — $10", callback_data="buy_year"))
    
    await message.answer("🛒 **Kairo Store**\nВыберите тариф:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔄 Проверить оплату (Мгновенно)", callback_data=f"check_master_{duration}"))
    
    await callback.message.edit_text(
        f"💳 Режим быстрой проверки для тарифа: {duration}\nНажми кнопку ниже для получения мастер-ключа.",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data.startswith("check_master_"))
async def give_master_key(callback: types.CallbackQuery):
    # Выдаем один из пяти ключей случайным образом для теста
    key = random.choice(MASTER_KEYS)
    await callback.message.edit_text(f"✅ Оплата принята!\nТвой приватный ключ:\n`{key}`", parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
