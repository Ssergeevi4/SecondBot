import random
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from sheet.sheets import create_invite_code, get_invite_code, register_user, get_user_role
from aiogram.types import Message

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_code(message: Message):

    invite_code = message.get_args()

    if not invite_code:
        await message.reply("Привет! Используй ссылку с кодом приглашения, чтобы зарегистрироваться как продавец.")
        return

    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    try:
        # Проверяем, валиден ли код приглашения
        invite_data = get_invite_code(invite_code)  # Предполагаемая функция для проверки кода
        if not invite_data:
            await message.reply("Неверный код приглашения.")
            return

        # Регистрируем пользователя как продавца
        register_user(user_id, username, role="seller")  # Предполагаемая функция для регистрации
        await message.reply("Вы успешно зарегистрированы как продавец!")
    except Exception as e:
        await message.reply(f"Произошла ошибка при регистрации: {e}")


@router.message(CommandStart())
async def start_without_code(message: Message):
    await message.reply("Привет! Используй ссылку с кодом приглашения, чтобы зарегистрироваться как продавец.")

@router.message(Command("generate_invite"))
async def generate_invite(message: types.Message):
    user_id = message.from_user.id
    role = get_user_role(user_id)
    if role != "admin":
        await message.reply("Эта команда доступна только администраторам!")
        return

    invite_code = random.randint(100000, 999999)
    create_invite_code(invite_code, "saller")
    bot_username = "TG1magBot"
    invite_link = f"https://t.me/{bot_username}?start={invite_code}"
    await message.reply(invite_link)