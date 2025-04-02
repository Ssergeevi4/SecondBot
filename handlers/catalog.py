# handlers/catalog.py
import random
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config.config import LIMIT
from sheet.sheets import get_products, add_to_cart, get_cart, get_user_role, create_order, remove_from_cart

router = Router()


class Order(StatesGroup):
    CONFIRMED_ORDER = State()

async def delayed_remove_from_cart(user_id, product_id=None):
    """Фоновая задача для удаления товаров из корзины."""
    try:
        await asyncio.sleep(0.1)  # Даём время на ответ
        remove_from_cart(user_id, product_id)
    except Exception as e:
        print(f"Error in delayed_remove_from_cart: {e}")

@router.message(Command("catalog"))
async def show_catalog(message: types.Message):
    role = get_user_role(message.from_user.id)
    if role in ["buyer", "admin", "seller"]:
        await send_products(message, offset=0)
    else:
        await message.reply("Эта команда доступна только покупателям и администраторам.")


async def send_products(message: types.Message, offset):
    products = get_products()
    total_products = len(products)

    if offset >= total_products:
        await message.reply("Лента закончилась!")
        return

    # Карточки
    for product in products[offset:offset + LIMIT]:
        # Формируем текст карточки
        card_text = (
            f"<b>{product.get('Name', '')}</b>\n"
            f"{product.get('Description', '')}\n"
            f"Цена: {product.get('Price', 0)} руб.\n"
        )
        if "Sizes" in product:
            card_text += f"Размеры: {product['Sizes']}\n"
        if "Dimensions" in product:
            card_text += f"Габариты: {product['Dimensions']}\n"
        card_text += f"В наличии: {product.get('Availability', 'Не указано')}\n"

        # Кнопки для количества и добавления
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        product_id = str(product.get('ID', '0')).replace('=', '')
        quantity_button = [
            InlineKeyboardButton(text="-1", callback_data=f"dec_{product_id}_1"),
            InlineKeyboardButton(text="1", callback_data="noop"),
            InlineKeyboardButton(text="+1", callback_data=f"inc_{product_id}_1"),
        ]
        add_button = InlineKeyboardButton(
            text="Добавить", callback_data=f"add_{product_id}_1"
        )
        keyboard.inline_keyboard.append(quantity_button)
        keyboard.inline_keyboard.append([add_button])

        image_url = product.get('Image_URL')
        if image_url:
            try:
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=image_url,
                    caption=card_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                await message.reply(f"Ошибка загрузки изображения: {e}\n\n{card_text}", reply_markup=keyboard,
                                    parse_mode="HTML")
        else:
            await message.reply(card_text, reply_markup=keyboard, parse_mode="HTML")

    if offset + LIMIT < total_products:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        next_button = InlineKeyboardButton(text="Далее",
                                           callback_data=f"more_{offset + LIMIT}")  # Исправлено mroe_ на more_
        keyboard.inline_keyboard.append([next_button])
        await message.reply("Продолжить?", reply_markup=keyboard)

    # Добавляем корзину внизу
    await update_cart_message(message, message.from_user.id)


@router.callback_query(lambda c: c.data.startswith(
    ("add_", "more_", "inc_", "qty_", "dec_", "checkout_", "confirm_order_", "cancel_order_", "remove_")))
async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    user_id = callback_query.from_user.id
    role = get_user_role(user_id)

    if role not in ["buyer", "admin"]:
        await callback_query.bot.answer_callback_query(callback_query.id,
                                                       text="Эта команда доступна только покупателям и администраторам.")
        return

    if data == "noop":
        await callback_query.bot.answer_callback_query(callback_query.id,
                                                       text="Нажмите -1 или +1 для изменения количества.")
        return

    if data.startswith("add_"):
        try:
            product_id, quantity = map(int, data.split("_")[1:3])
            add_to_cart(user_id, product_id, quantity)
            await callback_query.bot.answer_callback_query(callback_query.id, text="Товар добавлен в корзину!")
            await update_cart_message(callback_query.message, user_id)
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка при добавлении товара: {e}")

    elif data.startswith("remove_"):
        product_id = data.split("_")[1]
        asyncio.create_task(delayed_remove_from_cart(user_id, product_id))
        await callback_query.bot.answer_callback_query(callback_query.id, text="Товар удалён из корзины!")
        await update_cart_message(callback_query.message, user_id)

    elif data.startswith("more_"):
        try:
            offset = int(data.split("_")[1])
            await send_products(callback_query.message, offset)
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка: {e}")

    elif data.startswith("inc_") or data.startswith("dec_"):
        try:
            action, product_id, current_qty = data.split("_")
            product_id = int(product_id.replace('=', ''))
            current_qty = int(current_qty)
            change = 1 if action == "inc" else -1
            new_quantity = max(1, current_qty + change)

            if new_quantity == current_qty:
                await callback_query.bot.answer_callback_query(
                    callback_query.id,
                    text="Количество не может быть меньше 1!" if action == "dec" else "Количество не изменилось!"
                )
            else:
                updated = False
                for row in callback_query.message.reply_markup.inline_keyboard:
                    for button in row:
                        if button.callback_data == "noop":
                            if button.text != str(new_quantity):
                                button.text = str(new_quantity)
                                updated = True
                        elif button.callback_data.startswith(f"add_{product_id}_"):
                            if button.callback_data != f"add_{product_id}_{new_quantity}":
                                button.callback_data = f"add_{product_id}_{new_quantity}"
                                updated = True
                        elif button.callback_data.startswith(f"inc_{product_id}_"):
                            if button.callback_data != f"inc_{product_id}_{new_quantity}":
                                button.callback_data = f"inc_{product_id}_{new_quantity}"
                                updated = True
                        elif button.callback_data.startswith(f"dec_{product_id}_"):
                            if button.callback_data != f"dec_{product_id}_{new_quantity}":
                                button.callback_data = f"dec_{product_id}_{new_quantity}"
                                updated = True

                if updated:
                    try:
                        await callback_query.message.edit_reply_markup(reply_markup=callback_query.message.reply_markup)
                    except Exception as e:
                        await callback_query.bot.answer_callback_query(callback_query.id,
                                                                       text=f"Ошибка при обновлении клавиатуры: {e}")

                await callback_query.bot.answer_callback_query(callback_query.id,
                                                               text=f"Количество изменено: {new_quantity}")
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка: {e}")

    elif data.startswith("checkout_"):
        try:
            cart = get_cart()
            user_cart = [row for row in cart if str(row.get('User_ID')) == str(user_id)]
            if not user_cart:
                await callback_query.bot.answer_callback_query(callback_query.id, text="Корзина пуста!")
                return

            products = get_products()
            order_text = "<b>Ваш заказ:</b>\n"
            total_cost = 0

            for item in user_cart:
                product = next((p for p in products if
                                str(p.get('ID', '0')).replace('=', '') == str(item.get('Product_ID', '0')).replace('=',
                                                                                                                   '')),
                               None)
                if product:
                    quantity = int(item.get('Quantity', 0))
                    price = float(product.get('Price', 0))
                    total_cost += price * quantity
                    order_text += f"{product.get('Name', 'Не указано')} - {quantity} шт. x {price} руб. = {quantity * price} руб.\n"

            # Выносим "Итого" и "Подтвердить заказ?" за цикл
            order_text += f"\n<b>Итого:</b> {total_cost} руб.\n\nПодтвердить заказ?"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[])
            confirm_button = InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_order_{user_id}")
            cancel_button = InlineKeyboardButton(text="Отменить", callback_data=f"cancel_order_{user_id}")
            keyboard.inline_keyboard.append([confirm_button, cancel_button])

            # Сохраняем данные корзины в состоянии
            await state.update_data(user_cart=user_cart, total_cost=total_cost)
            await callback_query.message.reply(order_text, parse_mode="HTML", reply_markup=keyboard)
            await state.set_state(Order.CONFIRMED_ORDER)
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка при оформлении заказа: {e}")

    elif data.startswith("confirm_order_"):
        try:
            # Получаем данные из состояния
            order_data = await state.get_data()
            user_cart = order_data.get('user_cart', [])
            total_cost = order_data.get('total_cost', 0)

            if not user_cart:
                await callback_query.bot.answer_callback_query(callback_query.id, text="Корзина пуста!")
                await state.clear()
                return

            # Генерируем номер заказа
            order_number = random.randint(100000, 999999)

            asyncio.create_task(delayed_remove_from_cart(user_id))  # Удаляем все товары пользователя

            # Создаём заказы
            for item in user_cart:
                product_id66 = item.get('Product_ID')
                quantity = int(item.get('Quantity', 0))
                create_order(user_id, product_id66, quantity, order_number)

            # Очищаем корзину после оформления заказа
            for item in user_cart:
                remove_from_cart(user_id, item.get('Product_ID'))

            # Отправляем уведомление пользователю
            await callback_query.bot.answer_callback_query(callback_query.id,
                                                           text=f"Заказ №{order_number} оформлен! Сумма: {total_cost} руб.")
            await callback_query.message.reply(f"Ваш заказ №{order_number} на сумму {total_cost} руб. оформлен!")

            # Отправляем уведомление администратору
            admin_id = "499989726"  # ID администратора
            admin_text = f"Новый заказ №{order_number} от пользователя {user_id}:\n"
            products = get_products()
            for item in user_cart:
                product = next((p for p in products if
                                str(p.get('ID', '0')).replace('=', '') == str(item.get('Product_ID', '0')).replace('=',
                                                                                                                   '')),
                               None)
                if product:
                    quantity = int(item.get('Quantity', 0))
                    price = float(product.get('Price', 0))
                    admin_text += f"{product.get('Name', 'Не указано')} - {quantity} шт. x {price} руб. = {quantity * price} руб.\n"
            admin_text += f"\nИтого: {total_cost} руб."
            try:
                await callback_query.bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
            except Exception as e:
                print(f"Ошибка при отправке уведомления администратору: {e}")

            # Обновляем корзину
            await update_cart_message(callback_query.message, user_id)
            await state.clear()
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id,
                                                           text=f"Ошибка при подтверждении заказа: {e}")

    elif data.startswith("cancel_order_"):
        try:
            await callback_query.bot.answer_callback_query(callback_query.id, text="Оформление заказа отменено.")
            await callback_query.message.reply("Оформление заказа отменено.")
            await state.clear()
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка при отмене заказа: {e}")

    elif data.startswith("remove_"):
        try:
            product_id = int(data.split("_")[1])
            remove_from_cart(user_id, product_id)
            await callback_query.bot.answer_callback_query(callback_query.id, text="Товар удалён из корзины!")
            await update_cart_message(callback_query.message, user_id)
        except Exception as e:
            await callback_query.bot.answer_callback_query(callback_query.id, text=f"Ошибка при удалении товара: {e}")

    await callback_query.bot.answer_callback_query(callback_query.id)


async def update_cart_message(message: types.Message, user_id):
    """Обновляем сообщение с корзиной."""
    try:
        products = get_products()
        cart = get_cart()
        user_cart = [row for row in cart if str(row.get('User_ID')) == str(user_id)]  # Приводим к строке для сравнения
        if user_cart:
            cart_text = "<b>Содержимое корзины:</b>\n"
            for item in user_cart:
                product = next((p for p in products if
                                str(p.get('ID', '0')).replace('=', '') == str(item.get('Product_ID', '0')).replace('=',
                                                                                                                   '')),
                               None)
                if product:
                    cart_text += f"{product.get('Name', 'Не указано')} - {item.get('Quantity', 0)} шт. "
                    cart_text += f"(<a href='tg://btn/remove_{item.get('Product_ID')}'>Удалить</a>)\n"
            if cart_text != "<b>Содержимое корзины:</b>\n":
                cart_text += f"<b>Общая стоимость:</b> {sum(int(item.get('Quantity', 0)) * float(next(p.get('Price', 0) for p in products if str(p.get('ID', '0')).replace('=', '') == str(item.get('Product_ID', '0')).replace('=', ''))) for item in user_cart)} руб.\n"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                checkout_button = InlineKeyboardButton(text="Оформить заказ", callback_data="checkout_")
                keyboard.inline_keyboard.append([checkout_button])
                cart_text += "\n<a href='tg://btn/checkout_'>Оформить заказ</a>"
                await message.reply(cart_text, parse_mode="HTML", reply_markup=keyboard)
        else:
            await message.reply("Корзина пуста!", parse_mode="HTML")
    except Exception as e:
        await message.reply(f"Ошибка при обновлении корзины: {e}", parse_mode="HTML")