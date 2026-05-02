import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Твій токен зі Screenshot_278.png
API_TOKEN = "8716589061:AAF1pEGmv6rYkhG7Nby-Fvbb3kptknDTj50"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Ціни
PRICES = {'week': 1.5, 'month': 3, 'year': 10}

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Неділя — $1.5", callback_data="buy_week"))
    builder.row(types.InlineKeyboardButton(text="Місяць — $3", callback_data="buy_month"))
    builder.row(types.InlineKeyboardButton(text="Рік — $10", callback_data="buy_year"))

    await message.answer("🛒 **Kairo Store**\nВиберіть тариф:", reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buy_"))
async def create_invoice(callback: types.CallbackQuery):
    duration = callback.data.split("_")[1]
    price = PRICES.get(duration)
    
    builder = InlineKeyboardBuilder()
    # ТУТ ЗАМІНИ ПОСИЛАННЯ НА СВОЄ (CryptoBot, Mono, або посилання на твій профіль для оплати)
    builder.row(types.InlineKeyboardButton(text="💳 Оплатити", url="https://t.me/твій_юзернейм")) 
    builder.row(types.InlineKeyboardButton(text="✅ Я оплатив (Перевірка)", callback_data=f"wait_admin_{duration}"))

    await callback.message.edit_text(
        f"💎 Режим оплати для тарифу: **{duration}**\n💰 Ціна: **{price}$**\n\nНатисніть кнопку нижче для оплати, а потім кнопку перевірки.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("wait_admin_"))
async def wait_admin(callback: types.CallbackQuery):
    await callback.answer("⏳ Перевірка триває... Адмін перевірить оплату протягом 15 хвилин.", show_alert=True)
    # Тепер бот не віддає ключ автоматично!
    await callback.message.answer("📩 Ваша заявка надіслана. Очікуйте повідомлення від адміна з вашим ключем.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
