# handlers/catalog.py
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import LIMIT
from sheet.sheets import get_products, add_to_cart, get_cart

router = Router()


@router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    await send_products(message, offset=0)


async def send_products(message: types.Message, offset):
    products = get_products()
    total_products = len(products)

    if offset >= total_products:
        await message.reply("Лента закончилась!")
        return

    # карточки
    for product in products[offset:offset + LIMIT]:
        # Формируем текст карточки
        card_text = (
            f"<b>{product['Name']}</b>\n"
            f"{product.get('Description', '')}\n"
            f"Цена: {product.get('Price', 0)} руб.\n"
        )
        if "Sizes" in product:
            card_text += f"Размеры: {product['Sizes']}\n"
        if "Dimensions" in product:
            card_text += f"Габариты: {product['Dimensions']}\n"
        card_text += f"В наличии: {product['Availability']}\n"

        # Кнопки для количества и добавления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        quantity_button = [
            InlineKeyboardButton(text="-1", callback_data=f"dec_={product['ID']}_0"),
            InlineKeyboardButton(text="1", callback_data=f"qty_={product['ID']}_1"),
            InlineKeyboardButton(text="+1", callback_data=f"inc_={product['ID']}_0"),
        ]
        add_button = InlineKeyboardButton(
            text="Добавить", callback_data=f"add_{product['ID']}_1"
        )
        keyboard.inline_keyboard.append(quantity_button)
        keyboard.inline_keyboard.append([add_button])

        await message.reply(card_text, reply_markup=keyboard, parse_mode="html")

    if offset + LIMIT < total_products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        next_button = InlineKeyboardButton(text="Далее", callback_data=f"mroe_{offset + LIMIT}")
        keyboard.inline_keyboard.append([next_button])
        await message.reply("Продолжить?", reply_markup=keyboard)


    # Добавляем корзину внизу
    cart = get_cart()
    user_cart = [row for row in cart if row['User_ID'] == message.from_user.id]
    if user_cart:
        card_text = "<b>Содержимое корзины:</b>\n"
        for item in user_cart:
            product = next(p for p in products if p['ID'] == item['Product_ID'])
            card_text += f"{product['Name']} - {item['Quantity']} шт.\n"
        card_text += f"<b>Общая стоимость:</b> {sum(item['Quantity'] * next(p['Price'] for p in products if p['ID'] == item['Product_ID']) for item in user_cart)} руб."
        await message.reply(card_text, parse_mode="HTML")


@router.callback_query(lambda c: c.data.startswith(("add_", "more_", "inc_", "qty_", "dec_")))
async def process_callback(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id

    if data.startswith("add_"):
        product_id, quantity = map(int, data.split("_")[1:3])
        add_to_cart(user_id, product_id, quantity)
        await callback_query.bot.answer_callback_query(callback_query.id, text="Товар добавлен в корзину!")

    elif data.startswith("more_"):
        offset = int(data.split("_")[1])
        await send_products(callback_query.message, offset)


    elif data.startswith("inc_") or data.startswith("dec_"):
        action, product_id, current_qty = data.split("_")
        product_id = int(product_id)
        current_qty = int(current_qty)
        change = 1 if action == "inc" else -1
        new_quantity = max(1, current_qty + change)

        # Обновляем текст кнопки количества
        for row in callback_query.message.reply_markup.inline_keyboard:
            for button in row:
                if button.callback_data.startswith(f"qty_{product_id}_"):
                    button.text = str(new_quantity)
                    button.callback_data = f"qty_{product_id}_{new_quantity}"
                elif button.callback_data.startswith(f"add_{product_id}_"):
                    button.callback_data = f"add_{product_id}_{new_quantity}"
                elif button.callback_data.startswith(f"inc_{product_id}_"):
                    button.callback_data = f"inc_{product_id}_{new_quantity}"
                elif button.callback_data.startswith(f"dec_{product_id}_"):
                    button.callback_data = f"dec_{product_id}_{new_quantity}"

        await callback_query.message.edit_reply_markup(reply_markup=callback_query.message.reply_markup)
        await callback_query.bot.answer_callback_query(callback_query.id)

    await callback_query.bot.answer_callback_query(callback_query.id)

async def update_cart_message(message: types.Message, user_id):
    """Обновляем сообщение с корзиной (ищем последнее сообщение с корзиной и редактируем его)."""
    products = get_products()
    cart = get_cart()
    user_cart = [row for row in cart if row['User_ID'] == user_id]
    if user_cart:
        cart_text = "<b>Содержимое корзины:</b>\n"
        for item in user_cart:
            product = next(p for p in products if p['ID'] == item['Product_ID'])
            cart_text += f"{product['Name']} - {item['Quantity']} шт.\n"
        cart_text += f"<b>Общая стоимость:</b> {sum(item['Quantity'] * next(p['Price'] for p in products if p['ID'] == item['Product_ID']) for item in user_cart)} руб."
        # Ищем последнее сообщение с корзиной
        async for msg in message.chat.get_history(limit=10):
            if msg.text and msg.text.startswith("<b>Содержимое корзины:</b>"):
                await msg.edit_text(cart_text, parse_mode="HTML")
                break
        else:
            await message.reply(cart_text, parse_mode="HTML")

