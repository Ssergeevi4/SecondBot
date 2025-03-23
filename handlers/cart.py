# handlers/cart.py
from aiogram import Router, types
from aiogram.filters import Command
from sheet.sheets import get_cart, get_products

router = Router()

@router.message(Command("cart"))
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    cart = get_cart()
    products = get_products()

    user_cart = [row for row in cart if row['User_ID'] == user_id]
    if not user_cart:
        await message.reply("Ваша корзина пуста!")
        return

    response = "Ваша корзина:\n"
    for item in user_cart:
        product = next(p for p in products if p['ID'] == item['Product_ID'])
        response += f"{product['Name']} - {item['Quantity']} шт. - {product['Price']} руб.\n"

    await message.reply(response)