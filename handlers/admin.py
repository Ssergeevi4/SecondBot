from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sheet.sheets import get_user_role, get_products

router = Router()

@router.message(lambda message: message.text and "|" in message.text)
async def add_product(message: types.Message):
    role = get_user_role(message.from_user.id)
    if role == "admin":
        await message.reply("Эта команда доступна только администраторам.")
        return
    try:
        name, description, price, availability, sizes, dimensions, image_url = message.text.split("|")[1]
        name = name.strip()
        description = description.strip()
        price = float(price.strip())
        availability = availability.strip()
        sizes = sizes.strip()
        dimensions = dimensions.strip()
        image_url = image_url.strip()
        product_id = add_product(name, description, price, availability, sizes, dimensions, image_url)
        await message.reply(f"Товар добавлен с ID: {product_id}")
    except Exception as e:
        await message.reply(f"Ошибка при добавлении товара: {e}\nФормат: Название | Описание | Цена | Наличие | Размеры | Габариты | URL_изображения")