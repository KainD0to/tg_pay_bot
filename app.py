import asyncio
import logging
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN
from payments import create_payment, check_payment

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Бот и диспетчер (без прокси!)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот для тестирования платежей.\n"
        "Напиши /buy чтобы купить тестовую услугу за 100 руб."
    )


@dp.message(Command("buy"))
async def buy_command(message: types.Message):
    try:
        payment_id, payment_url = create_payment(
            amount=100.0,
            description="Тестовая подписка",
            user_id=message.from_user.id
        )

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text="💳 Оплатить 100₽",
                url=payment_url
            )],
            [types.InlineKeyboardButton(
                text="🔄 Проверить оплату",
                callback_data=f"check_{payment_id}"
            )]
        ])

        await message.answer(
            "🧾 Счёт на оплату:\n"
            "Тестовая услуга — 100₽\n\n"
            "Нажмите кнопку «Оплатить» и введите тестовые данные карты.\n"
            "После оплаты нажмите «Проверить оплату»",
            reply_markup=keyboard
        )

    except Exception as e:
        logging.error(f"Ошибка создания платежа: {e}")
        await message.answer("❌ Не удалось создать платёж. Попробуйте позже.")


@dp.callback_query(lambda c: c.data.startswith('check_'))
async def check_payment_handler(callback: types.CallbackQuery):
    payment_id = callback.data.split('_')[1]

    status = check_payment(payment_id)

    if status == 'succeeded':
        await callback.message.edit_text(
            "✅ Оплата прошла успешно!\n"
            "Спасибо за покупку!",
            reply_markup=None
        )
    elif status == 'canceled':
        await callback.message.edit_text(
            "❌ Платёж отменён.",
            reply_markup=None
        )
    else:
        await callback.answer(
            "⏳ Платёж ещё не получен. Попробуйте через несколько секунд.",
            show_alert=True
        )


# ========== ЗАПУСК ==========

async def start_bot():
    logging.info("Запускаю бота через Long Polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logging.warning(f"Не удалось удалить webhook: {e}")
    
    await dp.start_polling(bot)


app = FastAPI()


@app.get("/")
async def root():
    return {"status": "Бот работает (polling mode)"}


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())