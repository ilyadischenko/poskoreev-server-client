import time
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response, HTTPException

from app.app.response import getResponseBody
from app.orders.models import Order, OrderLog, CartItem, OrderPayType
from app.restaurants.models import RestaurantPayType, PayType
from app.promocodes.models import PromoCode
from app.users.models import User


class CookieCheckerOrder:
    async def __call__(self, request: Request):
        if '_oi' not in request.cookies: raise HTTPException(status_code=200, detail=getResponseBody(
            status=False,
            errorCode=502,
            errorMessage='Сначала нужно добавить что-нибудь в корзину'
        ))

        return int(request.cookies['_oi'])


CCO = CookieCheckerOrder()


async def OrderCheckOrCreate(cookies, response, restaurant_id, address, user_id=None):
    if '_oi' not in cookies:
        order = await Order.create(restaurant_id=restaurant_id, address=address,
                                   user_id=user_id
                                   )
        response.set_cookie('_oi', value=order.id, httponly=True, secure=True, samesite='none')
        return order
    order = await Order.get_or_none(id=cookies['_oi'],
                                    # user=user_id
                                    )
    if not order:
        order = await Order.create(restaurant_id=restaurant_id, address=address,
                                   user_id=user_id
                                   )
        response.set_cookie('_oi', order.id, httponly=True, secure=True, samesite='none')
    tomorrow = datetime.now(tz=timezone.utc) - timedelta(days=1)
    if order.created_at <= tomorrow:
        order = await Order.create(restaurant_id=restaurant_id, address=address, user_id=user_id,
                                   created_at=datetime.now(tz=timezone.utc))
        response.set_cookie('_oi', order.id, httponly=True, secure=True, samesite='none')
    return order


async def check_order_payment_type(order):
    opt = await OrderPayType.get_or_none(order_id=order.id)
    if not opt: raise HTTPException(status_code=200, detail=getResponseBody(
        status=False,
        errorCode=503,
        errorMessage='Выберите способ оплаты'
    ))

    rpt = await RestaurantPayType.get_or_none(available=True, id=opt.restaurant_pay_type_id).prefetch_related(
        'pay_type')
    if not rpt: raise HTTPException(status_code=200, detail=getResponseBody(
        status=False,
        errorCode=208,
        errorMessage='К сожалению, этот способ оплаты сейчас не доступен'
    ))
    return rpt.pay_type


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
    order.sum = int(sum)
    await order.save()


async def GetOrderInJSON(order):
    cart_list = []
    items = await CartItem.filter(order_id=order.id).prefetch_related('product', 'menu').order_by('id')
    for item in items:
        cart_list.append({'id': item.menu_id,
                          'title': item.product.title,
                          'img': item.product.img,
                          'quantity': item.quantity,
                          'unit': item.menu.unit,
                          'size': item.menu.size,
                          'sum': item.sum,
                          'bonuses': item.bonuses})
    return {
        'items': cart_list,
        'bonuses': order.added_bonuses,
        'product_count': order.products_count,
        'sum': order.sum,
        # 'promocode': order.promocode,
        # 'valid': order.promocode_applied,
        'total_sum': order.sum if not order.total_sum else order.total_sum
    }


async def GetOrderSnapshotInJSON(order, paytype):
    cart_list = []
    items = await CartItem.filter(order_id=order.id).prefetch_related('product', 'menu').order_by('id')
    for item in items:
        cart_list.append({'id': item.menu_id,
                          'title': item.product.title,
                          'img': item.product.img,
                          'quantity': item.quantity,
                          'unit': item.menu.unit,
                          'size': item.menu.size,
                          'sum': item.sum,
                          'bonuses': item.bonuses})
    return {
        'user': order.user.id,
        'restaurant': order.restaurant.id,
        'address': {
            'street': order.address,
            'entrance': order.entrance,
            'floor': order.floor,
            'apartment': order.apartment,
            # 'points': points
        },
        'promocode': {
            'promocode': order.promocode,
            'promocode_applied': order.promocode_applied,
            'promocode_linked': order.promocode_linked
        },
        'comment': order.comment,
        'type': order.type,
        'items': cart_list,
        'bonuses': order.added_bonuses,
        'product_count': order.products_count,
        'sum': order.sum,
        'paytype': paytype.name,
        'total_sum': order.sum if not order.total_sum else order.total_sum
    }


async def validate_menu(order):
    listt = []
    items = await CartItem.filter(order_id=order.id).prefetch_related('product', 'menu')
    if not items: raise HTTPException(status_code=200, detail=getResponseBody(
        status=False,
        errorCode=504,
        errorMessage='Невозможно оформить пустой заказ'
    ))
    print(items)
    for item in items:
        if not item.menu.in_stock or not item.menu.visible:
            listt.append({'id': item.menu_id})
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                errorCode=402,
                errorMessage=f'К сожалению, {listt} сейчас на стопе :('
            ))
    return


async def AddPromocode(order, input_promocode, restaurant_id, user_id=0):
    short_promocode = input_promocode
    if short_promocode is None or short_promocode == '':
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        return {
            'promocode': '',
            'applied': False,
            'linked': False,
            'message': '',
        }
    short_promocode = short_promocode.lower()
    promocode = await PromoCode.get_or_none(short_name=short_promocode, is_active=True)

    if not promocode:
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        return {
            'promocode': short_promocode,
            'applied': False,
            'linked': False,
            'message': 'Такого промокода не существует',
        }
    if promocode.restaurant_id is not None and promocode.restaurant_id != restaurant_id:
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        return {
            'promocode': short_promocode,
            'applied': False,
            'linked': False,
            'message': 'Такого промокода не существует',
        }

    # Проверка на привязку промокода юзеру если он не для всех
    if not promocode.for_all:
        user = await User.get(id=user_id).prefetch_related('promocodes')
        user_promocode = await user.promocodes.filter(id=promocode.id)
        if len(user_promocode) == 0:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode = None
            order.promocode_linked = False
            await order.save()
            return {
                'promocode': short_promocode,
                'applied': False,
                'linked': False,
                'message': 'Такого промокода не существует',
            }
    if promocode.count == 0 or promocode.end_day < datetime.now(timezone.utc) or promocode.start_day > datetime.now(
            timezone.utc):
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        return {
            'promocode': short_promocode,
            'applied': False,
            'linked': False,
            'message': 'Промокод недействителен',
        }
    if promocode.min_sum > order.sum:
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = short_promocode
        order.promocode_linked = True
        await order.save()
        return {
            'promocode': short_promocode,
            'applied': False,
            'linked': True,
            'message': f'Минимальная сумма заказа для применения промокода {promocode.min_sum}р',
        }

    if promocode.type == 2:
        total = round(order.sum * (1 - promocode.effect * 0.01), 0)
        if total >= 1:
            order.total_sum = total
            order.promocode_applied = True
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return {
                'promocode': short_promocode,
                'applied': True,
                'linked': True,
                'message': 'Промокод применён',
            }
        else:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return {
                'promocode': short_promocode,
                'applied': False,
                'linked': True,
                'message': 'Промокод не может понизить сумму заказа ниже одного рубля'
            }
    elif promocode.type == 3:
        total = order.sum - promocode.effect
        if total >= 1:
            order.total_sum = total
            order.promocode_applied = True
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return {
                'promocode': short_promocode,
                'applied': True,
                'linked': True,
                'message': 'Промокод применён',
            }
        else:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return {
                'promocode': short_promocode,
                'applied': False,
                'linked': True,
                'message': 'Промокод не может понизить сумму заказа ниже одного рубля'
            }


async def validate_promocode(order, promocode, user_id):
    short_promocode = promocode
    promocode = await PromoCode.get_or_none(short_name=promocode)
    if not promocode:
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        raise HTTPException(status_code=200, detail=getResponseBody(
            status=False,
            data={
                'promocode': short_promocode,
                'applied': False,
                'linked': False,
            },
            errorCode=301,
            errorMessage='Такого промокода не существует'

        ))

    # Проверка на привязку промокода юзеру если он не для всех
    if not promocode.for_all:
        user = await User.get(id=user_id).prefetch_related('promocodes')
        user_promocode = await user.promocodes.filter(id=promocode.id)
        if len(user_promocode) == 0:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode = None
            order.promocode_linked = False
            await order.save()
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                data={
                    'promocode': short_promocode,
                    'applied': False,
                    'linked': False,
                },
                errorCode=302,
                errorMessage='Такого промокода не существует'

            ))

    if promocode.count == 0 or promocode.end_day < datetime.now(timezone.utc) or promocode.start_day > datetime.now(
            timezone.utc):
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = None
        order.promocode_linked = False
        await order.save()
        raise HTTPException(status_code=200, detail=getResponseBody(
            status=False,
            data={
                'promocode': short_promocode,
                'applied': False,
                'linked': False,
            },
            errorCode=303,
            errorMessage='Промокод недействителен'
        ))

    if promocode.min_sum > order.sum:
        order.total_sum = order.sum
        order.promocode_applied = False
        order.promocode = short_promocode
        order.promocode_linked = True
        await order.save()
        raise HTTPException(status_code=200, detail=getResponseBody(
            status=False,
            data={
                'promocode': short_promocode,
                'applied': False,
                'linked': True,
            },
            errorCode=304,
            errorMessage=f'Минимальная сумма заказа для применения промокода {promocode.min_sum}р'
        ))

    if promocode.type == 2:
        total = round(order.sum * (1 - promocode.effect * 0.01), 0)
        if total >= 1:
            order.total_sum = total
            order.promocode_applied = True
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return
        else:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                data={
                    'promocode': short_promocode,
                    'applied': False,
                    'linked': True,
                },
                errorCode=305,
                errorMessage='Промокод не может понизить сумму заказа ниже одного рубля'
            ))

    elif promocode.type == 3:
        total = order.sum - promocode.effect
        if total >= 1:
            order.total_sum = total
            order.promocode_applied = True
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            return
        else:
            order.total_sum = order.sum
            order.promocode_applied = False
            order.promocode_linked = True
            order.promocode = short_promocode
            await order.save()
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                data={
                    'promocode': short_promocode,
                    'applied': False,
                    'linked': True,
                },
                errorCode=305,
                errorMessage='Промокод не может понизить сумму заказа ниже одного рубля'
            ))

