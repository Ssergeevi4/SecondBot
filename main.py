# main.py
from aiogram import Bot, Dispatcher
from config.config import TOKEN
from handlers.catalog import router as catalog_router
from handlers.cart import router as cart_router
from aiogram.types import Message
from aiogram.filters import Command

async def main():
    print('Бот запущен...')
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(catalog_router)
    dp.include_router(cart_router)

    # Приветственное сообщение (можно вынести в отдельный handler)
    @dp.message(Command("start"))
    async def send_welcome(message: Message):
        await message.reply("Добро пожаловать! Нажмите /catalog, чтобы посмотреть товары.")

    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())