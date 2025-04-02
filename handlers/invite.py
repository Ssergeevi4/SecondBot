import random

import requests
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from sheet.sheets import create_invite_code, get_invite_code, register_user, get_user_role

router = Router()

@router.message(CommandStart(deep_link=True))
async def handle_invite(message: types.Message):
    invite_code = message.get_args()

    if not invite_code:
        await message.reply("Используйте /catalog, чтобы просмотреть товары.")
        return
    try:
        invite = get_invite_code(invite_code)
        if not invite:
            await message.reply("Неверный код")
        return

        role = invite.get("Role")
        user_id = message.from_user.id

        current_role = get_user_role(user_id)

        register_user(user_id, role)
        await message.reply(f"Вы успешно зарегистрированы как {role}! Используйте /catalog, чтобы начать работу.")
    except Exception as e:
        await message.reply(str(e))

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