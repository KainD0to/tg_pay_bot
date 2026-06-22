import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from config import BOT_TOKEN, WEBHOOK_URL
from payments import create_payment, check_payment
from services import SERVICES, get_service

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Бот и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("catalog"))
async def show_catalog(message: types.Message):
    try:
        # Строим клавиатуру из всех сервисов
        buttons = []
        for service in SERVICES.values():
            buttons.append([
                types.InlineKeyboardButton(
                    text=f"{service.description} — {service.price}₽",
                    callback_data=f"buy_{service.name}"
                )
            ])
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.answer(
            "Каталог услуг:\n"
            "Выберите подписку, чтобы перейти к оплате.",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка каталога: {e}")
        await message.answer("Не удалось загрузить каталог.")
        
@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def buy_service(callback: types.CallbackQuery):
    # Парсим имя сервиса из callback_data
    service_name = callback.data.split('_')[1]
    
    # Получаем объект сервиса
    current_service = get_service(service_name)
    
    if current_service is None:
        await callback.answer("Сервис не найден", show_alert=True)
        return
    
    # Создаём платёж
    try:
        payment_id, payment_url = create_payment(
            amount=current_service.price,
            description=current_service.description,
            user_id=callback.from_user.id
        )
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(
                text=f"Оплатить {current_service.price}₽",
                url=payment_url
            )],
            [types.InlineKeyboardButton(
                text="Проверить оплату",
                callback_data=f"check_{payment_id}"
            )]
        ])
        
        await callback.message.edit_text(
            f"{current_service.description}\n"
            f"Сумма: {current_service.price}₽\n\n"
            "Нажмите «Оплатить» и введите тестовые данные карты.",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logging.error(f"Ошибка создания платежа: {e}")
        await callback.answer("Не удалось создать платёж", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith('check_'))
async def check_payment_handler(callback: types.CallbackQuery):
    payment_id = callback.data.split('_')[1]

    status = check_payment(payment_id)

    if status == 'succeeded':
        await callback.message.edit_text(
            "Оплата прошла успешно!\n"
            "Спасибо за покупку!",
            reply_markup=None
        )
    elif status == 'canceled':
        await callback.message.edit_text(
            "Платёж отменён.",
            reply_markup=None
        )
    else:
        await callback.answer(
            "Платёж ещё не получен. Попробуйте через несколько секунд.",
            show_alert=True
        )

# ========== WEBHOOK ==========

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


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def webhook(request: Request):
    try:
        json_data = await request.json()
        update = Update.model_validate(json_data)
        await dp.feed_update(bot, update)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Ошибка webhook: {e}")
        return {"status": "error", "detail": str(e)}


@app.get("/")
async def root():
    return {"status": "Бот работает!", "webhook": WEBHOOK_URL}