import time
from datetime import datetime, timedelta, timezone

from fastapi import Request, Response, HTTPException

from app.app.response import getResponseBody
from app.orders.models import Order, OrderLog, CartItem, OrderPayType
from app.restaurants.models import RestaurantPayType, PayType
from app.promocodes.models import PromoCode, PromocodeProduct
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


async def OrderCheckOrCreate(cookies, response, restaurant_id, user_id=None):
    if '_oi' not in cookies:
        order = await Order.create(restaurant_id=restaurant_id, user_id=user_id)
        response.set_cookie('_oi', value=order.id, httponly=True, secure=True, samesite='none')
        return order
    order = await Order.get_or_none(id=cookies['_oi'])
    if not order:
        order = await Order.create(restaurant_id=restaurant_id, user_id=user_id)
        response.set_cookie('_oi', order.id, httponly=True, secure=True, samesite='none')
    tomorrow = datetime.now(tz=timezone.utc) - timedelta(days=1)
    if order.created_at <= tomorrow:
        order = await Order.create(restaurant_id=restaurant_id, user_id=user_id)
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
        'total_sum': order.sum if not order.total_sum else order.total_sum
    }


async def GetOrderSnapshotInJSON(order, paytype, address, comment):
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
                          'bonuses': item.bonuses,
                          'category': item.menu.category_id
                          })

    promocode_type = 0
    promocode_effect = 0
    promocode_item = {}
    if order.promocode is not None:
        promocode = await PromoCode.get(short_name=order.promocode)
        promocode_type = promocode.type
        promocode_effect = promocode.effect
        if promocode.type == 1:
            promocode_item = await PromocodeProduct.get(id=promocode.effect).values('id', 'title',
                                                                                    'img', 'description', 'price', 'unit', 'size')
    return {
        'user': order.user.id,
        'restaurant': order.restaurant.id,
        'address': address,
        'promocode': {
            'promocode': order.promocode,
            'promocode_applied': order.promocode_applied,
            'promocode_linked': order.promocode_linked,
            'type': promocode_type,
            'effect': promocode_effect,
            'item': promocode_item
        },
        'comment': comment,
        'type': order.type,
        'items': cart_list,
        'bonuses': order.added_bonuses,
        'product_count': order.products_count,
        'sum': order.sum,
        'paytype': paytype.name,
        'total_sum': order.sum if not order.total_sum else order.total_sum
    }


async def validate_menu(order):
    """Функция проверяет что все позиции в меню не
    находятся в стоп листе и отображаются на сайте"""

    items = await CartItem.filter(order_id=order.id).prefetch_related('product', 'menu')
    if not items: raise HTTPException(status_code=200, detail=getResponseBody(
        status=False,
        errorCode=504,
        errorMessage='Невозможно оформить пустой заказ'
    ))
    for item in items:
        if not item.menu.in_stock or not item.menu.visible:
            raise HTTPException(status_code=200, detail=getResponseBody(
                status=False,
                errorCode=402,
                errorMessage=f'К сожалению, {item.product.title} {item.menu.size}{item.menu.unit} сейчас на стопе :('
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
            'type': 0,
            'effect': ''
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
            'type': 0,
            'effect': ''
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
            'type': 0,
            'effect': ''
        }

    '''Проверка на привязку промокода юзеру если он не для всех'''
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
                'type': 0,
                'effect': ''
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
            'type': 0,
            'effect': ''
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
            'type': 0,
            'effect': ''
        }
    if promocode.type == 1:
        item = await PromocodeProduct.get_or_none(id=promocode.effect)
        order.total_sum = order.sum + item.price
        order.promocode_applied = True
        order.promocode_linked = True
        order.promocode = short_promocode
        await order.save()
        return {
            'promocode': short_promocode,
            'applied': True,
            'linked': True,
            'message': 'Промокод применён и продукт добавлен в корзину',
            'type': 1,
            'effect': item
        }

    elif promocode.type == 2:
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
                'type': 2,
                'effect': ''
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
                'message': 'Промокод не может понизить сумму заказа ниже одного рубля',
                'type': 3,
                'effect': ''
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
                'type': 0,
                'effect': ''
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
                'message': 'Промокод не может понизить сумму заказа ниже одного рубля',
                'type': 0,
                'effect': ''
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

