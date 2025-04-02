from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sheet.sheets import add_product, get_user_role

router = Router()


# Определяем состояния для добавления товара
class AddProductStates(StatesGroup):
    NAME = State()
    DESCRIPTION = State()
    AVAILABILITY = State()
    PRICE = State()
    IMAGE_URL = State()
    CONFIRM = State()


@router.message(Command("add_product"))
async def add_product_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    role = get_user_role(user_id)

    # Разрешаем добавлять товары только администраторам
    if role not in ["admin", "seller"]:
        await message.reply("Эта команда доступна только администраторам!")
        return

    # Запрашиваем название товара
    await message.reply("Введите название товара:")
    await state.set_state(AddProductStates.NAME)


@router.message(AddProductStates.NAME)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith("/"):
        await message.reply("Пожалуйста, введите название товара (текст без команд).")
        return

    # Сохраняем название
    await state.update_data(name=message.text)
    await message.reply("Введите описание товара:")
    await state.set_state(AddProductStates.DESCRIPTION)


@router.message(AddProductStates.DESCRIPTION)
async def process_description(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith("/"):
        await message.reply("Пожалуйста, введите описание товара (текст без команд).")
        return

    # Сохраняем описание
    await state.update_data(description=message.text)
    await message.reply("Введите цену товара (число в рублях):")
    await state.set_state(AddProductStates.PRICE)


@router.message(AddProductStates.PRICE)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            await message.reply("Цена должна быть больше 0. Введите цену заново:")
            return
    except ValueError:
        await message.reply("Пожалуйста, введите корректное число для цены (например, 100.50).")
        return

    # Сохраняем цену
    await state.update_data(price=price)
    await message.reply("Укажите наличие товара (например, 'В наличии' или 'Нет в наличии'):")
    await state.set_state(AddProductStates.AVAILABILITY)


@router.message(AddProductStates.AVAILABILITY)
async def process_availability(message: types.Message, state: FSMContext):
    if not message.text or message.text.startswith("/"):
        await message.reply("Пожалуйста, укажите наличие товара (текст без команд).")
        return

    # Сохраняем наличие
    await state.update_data(availability=message.text)
    await message.reply("Введите URL изображения товара или напишите /skip, чтобы пропустить:")
    await state.set_state(AddProductStates.IMAGE_URL)


@router.message(AddProductStates.IMAGE_URL)
async def process_image_url(message: types.Message, state: FSMContext):
    if message.text == "/skip":
        await state.update_data(image_url=None)
    else:
        # Простая проверка, что это URL
        if not message.text.startswith("http"):
            await message.reply("Пожалуйста, введите корректный URL (начинается с http) или напишите /skip:")
            return
        await state.update_data(image_url=message.text)

    # Получаем все данные
    data = await state.get_data()
    name = data.get('name')
    description = data.get('description')
    availability = data.get('availability')
    price = data.get('price')
    image_url = data.get('image_url')

    # Формируем текст для подтверждения
    confirmation_text = (
        "<b>Подтвердите данные товара:</b>\n"
        f"Название: {name}\n"
        f"Описание: {description}\n"
        f"Наличие: {availability}\n"
        f"Цена: {price} руб.\n"
        f"URL изображения: {image_url if image_url else 'Не указано'}\n\n"
        "Отправьте /confirm для подтверждения или /cancel для отмены."
    )

    await message.reply(confirmation_text, parse_mode="HTML")
    await state.set_state(AddProductStates.CONFIRM)


@router.message(AddProductStates.CONFIRM, Command("confirm"))
async def confirm_product(message: types.Message, state: FSMContext):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        name = data.get('name')
        description = data.get('description')
        availability = data.get('availability')
        price = data.get('price')
        image_url = data.get('image_url')

        # Сохраняем товар в Google Таблицу
        add_product(name, description, price, availability, image_url)

        await message.reply("Товар успешно добавлен!")
        await state.clear()
    except Exception as e:
        await message.reply(f"Ошибка при добавлении товара: {e}")
        await state.clear()


@router.message(AddProductStates.CONFIRM, Command("cancel"))
async def cancel_product(message: types.Message, state: FSMContext):
    await message.reply("Добавление товара отменено.")
    await state.clear()


@router.message(AddProductStates.CONFIRM)
async def invalid_confirm(message: types.Message):
    await message.reply("Пожалуйста, отправьте /confirm для подтверждения или /cancel для отмены.")
