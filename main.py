# main.py
from aiogram import Bot, Dispatcher
from config.config import TOKEN
from handlers.catalog import router as catalog_router
from handlers import invite, add_product
from handlers.admin import router as admin_router
from handlers.seller import router as seller_router
from handlers.cart import router as cart_router
from aiogram.types import Message
from aiogram.filters import Command
import asyncio


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(catalog_router)
    dp.include_router(cart_router)
    dp.include_router(admin_router)
    dp.include_router(invite.router)
    dp.include_router(add_product.router)

    # Приветственное сообщение (можно вынести в отдельный handler)
    @dp.message(Command("start"))
    async def send_welcome(message: Message):
        await message.reply("Добро пожаловать!\n"
                            "Покупатели: /catalog\n"
                            "Администраторы: /add_product\n"
                            "Продавцы: /orders")

    print("Бот запущен...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен пользователем.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")