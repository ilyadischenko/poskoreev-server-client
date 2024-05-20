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


