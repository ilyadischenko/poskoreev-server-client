from datetime import datetime, timedelta, timezone

from fastapi import Request, Response, HTTPException

from app.orders.models import Order, OrderLog, CartItem
from app.promocodes.models import PromoCode

async def OrderCheckOrCreate(cookies, user_id, response):
    if '_oi' not in cookies:
        order = await Order.create(user_id=user_id,
                                   invalid_at=datetime.now() + timedelta(days=1))
        await OrderLog.create(order_id=order.pk)
        await order.save()
        response.set_cookie('_oi', value=order.id, httponly=True, samesite='none', secure=True)
        return order
    order = await Order.get_or_none(id=cookies['_oi'], user=user_id)
    if not order:
        order = await Order.create(user_id=user_id,
                                   invalid_at=datetime.now() + timedelta(days=1))
        await OrderLog.create(order_id=order.pk)
        response.set_cookie('_oi', order.id, httponly=True, samesite='none', secure=True)
    if order.invalid_at <= datetime.now(tz=timezone.utc):
        log=await OrderLog.get(order_id=order.id)
        log.status=3
        await log.save()
        order = await Order.create(user_id=user_id,
                                   invalid_at=datetime.now() + timedelta(days=1))
        await OrderLog.create(order_id=order.pk)
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
        'sum': order.sum,
        'promocode': order.promocode,
        'valid': order.promocode_valid,
        'total sum': order.sum if not order.total_sum else order.total_sum
    }
async def check_promocode(order):
    promocode = await PromoCode.get(short_name=order.promocode)
    if promocode.min_sum <= order.sum and promocode.end_day > datetime.now(timezone.utc) and promocode.count != 0:
        order.promocode_valid = True
        await order.save()
    else:
        order.promocode_valid = False
        order.total_sum = order.sum
        await order.save()
    if (not order.promocode) or (not order.promocode_valid):
        order.total_sum=order.sum
        await order.save()
        return
    if promocode.type == 2:
        order.total_sum = round(order.sum * (1 - promocode.effect * 0.01), 2)
    elif promocode.type == 3:
        order.total_sum = order.sum - promocode.effect
    if order.total_sum >= 0:
        await order.save()
        return
    else: raise HTTPException(status_code=405, detail="that wasnt suppose to happen")
