from aiogram import Bot, Dispatcher


from app.config import order_sender_bot_key, chanel_id

TOKEN = order_sender_bot_key
CHANEL_ID = chanel_id

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def send_order_to_tg(order, user_number):
    await bot.send_message(chanel_id, text=f'Новый заказ!\n'
                                           f'{order.created_at}\n'
                                           f'На {order.items['total_sum']}р\n'
                                           f'Пользователю +7{user_number}'
                           )


async def send_access_call_message(usernumber):
    await bot.send_message('840481448', text=f'Пользователю: {usernumber}\n'
                                             f'Отправлена смс\n')


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

async def send_error_sms_auth_message(usernumber, error):

    await bot.send_message('840481448', text=f'Ошибка авторизации у: {usernumber}\n'
                                             f'{error}\n')

