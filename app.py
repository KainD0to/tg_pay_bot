import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN

# Создаём объект бота - "клиент" для общения с API Telegram
bot = Bot(token=BOT_TOKEN)

# Диспетчер - мозг бота, который решает, как реагировать на сообщения
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Я твой первый бот. Напиши /help")

# Обработчик команды /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("Я пока умею только здороваться. Скоро научусь большему!")

# Обработчик обычных сообщений (без команды)
@dp.message()
async def echo(message: types.Message):
    # Просто отвечаем тем же текстом
    await message.answer(f"Ты написал: {message.text}")

# Точка входа - запускаем бесконечный опрос Telegram
async def main():
    print("Бот запущен! Жду сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())