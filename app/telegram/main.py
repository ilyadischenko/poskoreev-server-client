import asyncio

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = '7111584139:AAFQnB7tfYY0_iTv8MoZnNry29J6L3kX3Ao'
# CHANEL_ID = '-1001860241017'

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(f'Привет, {html.bold(message.from_user.id)}!')


async def send_access_call_message(usernumber):
    await bot.send_message('840481448', text=f'Пользователю: {usernumber}\n'
                                             f'Отправлен звонок\n')


async def send_error_auth_message(usernumber, error_id):
    message = ''
    if error_id == 1:
        message = 'Неверные параметры.'
    elif error_id == 2:
        message = 'Неверный формат номер телефона.'
    elif error_id == 3:
        message = 'Неверная комбинация `service_id` и `secret_key`.'
    elif error_id == 4:
        message = 'Возникла ошибка при инициализации звонка.'
    elif error_id == 6:
        message = 'По данным параметрам ничего не найдено.'
    elif error_id == 7:
        message = 'Пополните счёт для звонков.'
    elif error_id == 8:
        message = 'Пакет звонков закончился.'
    elif error_id == 9:
        message = 'Звонок уже идёт на этот номер.'
    elif error_id == 10:
        message = 'Не удалось дозвониться.'
    elif error_id == 11:
        message = 'Превышен лимит вызовов на данный номер.'
    elif error_id == 12:
        message = 'Номер находится в чёрном списке.'

    await bot.send_message('840481448', text=f'Ошибка авторизации у: {usernumber}\n'
                                             f'{message}\n')
