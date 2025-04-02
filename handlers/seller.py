from math import lgamma

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sheet.sheets import get_user_role, get_orders, update_order_status, get_products

router = Router()

@router.message(Command("orders"))
async def orders(message: types.Message):
    role = get_user_role(message.from_user.id)
    if role not in ["admin", "seller"]:
        await message.answer("Эта команда доступна только продавцам.")
        return
    orders = get_orders()
    if orders:
        await message.reply("Заказов нет.")
        return
    products = get_products()
    orders_text = "<b>Список заказов:</b>\n"
    for order in orders:
        products = next((p for p in products if str(p.get('ID', '0')).strip('=') == str(order.get('Product_ID', '0')).strip('=')), None)
        if products:
            orders_text += (
                f"Заказ #{order.get('Order_ID')}: {products.get('Name', 'Не указано')} - {order.get('Quantity', 0)} шт.\n"
                f"Статус: {order.get('Status', 'Pending')}\n"
                f"(<a href='tg://btn/ship_{order.get('Order_ID')}'>Отправить</a> | "
                f"<a href='tg://btn/cancel_{order.get('Order_ID')}'>Отменить</a>)\n\n"
            )
    await message.reply(orders_text, parse_mode="html")

@router.callback_query(lambda c: c.data.startswith(("ship_", "cancel_")))
async def cancel_order(callback_query: types.CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    role = get_user_role(user_id)
    if role != "seller":
        await callback_query.bot.answer_callback_query(callback_query.id, text="Эта команда доступна только продавцам.")
        return

    order_id = data.split("_")[1]
    new_status = "Shipped" if data.startswith("ship_") else "Cancelled"
    if update_order_status(order_id, new_status):
        await callback_query.bot.answer_callback_query(callback_query.id, text=f"Статус заказа #{order_id} обновлён на {new_status}!")
    else:
        await callback_query.bot.answer_callback_query(callback_query.id, text="Ошибка при обновлении статуса заказа.")