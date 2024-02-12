from datetime import datetime, timedelta

from fastapi import Request, Response

from app.orders.models import Order, OrderLog, CartItem


async def OrderCheckOrCreate(cookies, user_id, response):
    if '_oi' not in cookies:
        order = await Order.create(user_id=user_id, created_at=datetime.now(),
                                   invalid_at=datetime.now() + timedelta(days=1))
        await OrderLog.create(order_id=order.pk, user_id=user_id)
        await order.save()
        response.set_cookie('_oi', order.id, httponly=True, samesite='none', secure=True)
        return order

    # тут нужна проверка на истечение срока ордера. т.е. если он был инициализован вчера, то нужно создать новый,
    # а вчерашний кинуть в истёкший

    order = await Order.get_or_none(id=cookies['_oi'], user=user_id)
    if not order:
        order = await Order.create(user_id=user_id, created_at=datetime.now(),
                                   invalid_at=datetime.now() + timedelta(days=1))
        await OrderLog.create(order_id=order.pk, user_id=user_id)
        response.set_cookie('_oi', order.id, httponly=True, samesite='none', secure=True)
    return order


async def CalculateOrder(order):
    sum = 0
    count = 0
    bonuses = 0
    items = await CartItem.filter(order_id=order.id).prefetch_related('product')
    for item in items:
        count += item.quantity
        sum += item.sum
        bonuses += item.bonuses
    order.products_count = count
    order.added_bonuses = bonuses
    order.sum = sum
    order.total_sum = sum
    await order.save()
    # return order


async def GetOrderInJSON(order):
    cart_list = []
    items = await CartItem.filter(order_id=order.id).prefetch_related('product', 'menu')
    for item in items:
        cart_list.append({'id': item.menu_id,
                          'title': item.product.title,
                          'img': item.product.img,
                          'quantity': item.quantity,
                          'unit': item.menu.unit,
                          'sum': item.sum,
                          'bonuses': item.bonuses})
    return {
        'items': cart_list,
        'bonuses': order.added_bonuses,
        'product_count': order.products_count,
        'sum': order.sum
    }
