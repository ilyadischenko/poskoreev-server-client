from aiogram import Bot, Dispatcher


from app.config import order_sender_bot_key, chanel_id

TOKEN = order_sender_bot_key
CHANEL_ID = chanel_id

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def send_order_to_tg(order, user_number):
    await bot.send_message(chanel_id, text=f'Новый заказ!\n'
                                           f'{order.created_at}\n'
                                           f'На {order.items["total_sum"]}р\n'
                                           f'Пользователю +7{user_number}'
                           )


async def send_access_call_message(usernumber):
    await bot.send_message('840481448', text=f'Пользователю: {usernumber}\n'
                                             f'Отправлен звонок\n')

async def send_error_sms_auth_message(usernumber, error):
    await bot.send_message('840481448', text=f'Ошибка авторизации у: {usernumber}\n'
                                             f'{error}\n')


