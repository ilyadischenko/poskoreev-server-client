from aiogram import Bot, Dispatcher

from app.config import order_sender_bot_key, chanel_id
from app.restaurants.service import datetime_with_tz

TOKEN = order_sender_bot_key
CHANEL_ID = chanel_id

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def send_order_to_tg(order, user_number):
    def get_time_in_tz(time, tz):
        if time != None:
            return str(datetime_with_tz(time, tz).time())[:-10]
        return ''

    def get_street():
        street = order.items['address']['street']
        entrance = f", под. {order.items['address']['entrance']}" if order.items['address']['entrance'] != '' else ''
        floor = f", этаж {order.items['address']['floor']}" if order.items['address']['floor'] != '' else ''
        apartment = f", кв {order.items['address']['apartment']}" if order.items['address']['apartment'] != '' else ''
        return f'{street}{entrance}{floor}{apartment}'

    await bot.send_message(chanel_id, text=f'Новый заказ!\n'
                                           f'{get_time_in_tz(order.created_at, "Europe/Moscow")}\n'
                                           f'{get_street()}\n'
                                           f'На {order.items["total_sum"]}р\n'
                                           f'Пользователю +7{user_number}'
                           )


async def send_access_call_message(usernumber):
    await bot.send_message('840481448', text=f'Пользователю: {usernumber}\n'
                                             f'Отправлена смс\n')


async def send_error_sms_auth_message(usernumber, error):
    await bot.send_message('840481448', text=f'Ошибка авторизации у: {usernumber}\n'
                                             f'{error}\n')
