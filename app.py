import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from config import BOT_TOKEN, WEBHOOK_URL
from payments import create_payment, check_payment

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ========== ОБРАБОТЧИКИ КОМАНД ==========

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


# ========== НАСТРОЙКА ВЕБ-СЕРВЕРА ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Устанавливаю webhook...")
    await bot.set_webhook(
        url=WEBHOOK_URL,
        allowed_updates=dp.resolve_used_update_types()
    )
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")
    yield
    logging.info("Удаляю webhook...")
    await bot.delete_webhook()
    await bot.session.close()


# Создаём FastAPI приложение
app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Ошибка обработки webhook: {e}")
        return {"status": "error", "detail": str(e)}


@app.get("/")
async def root():
    return {"status": "Бот работает!", "webhook_url": WEBHOOK_URL}