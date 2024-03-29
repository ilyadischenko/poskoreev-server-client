from fastapi import HTTPException, APIRouter, Depends, Request, Response
from app.orders.models import Order, CartItem, OrderLog, OrderPayType
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, AddPromocode, validate_menu, \
    validate_promocode, check_all_cookies, check_order_payment_type
from app.products.models import Menu
from app.restaurants.models import Restaurant, Address, PayType, RestaurantPayType
from app.restaurants.service import time_with_tz, datetime_with_tz
from app.users.models import User
from app.promocodes.models import PromoCode
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta

orders_router = APIRouter(
    prefix="/api/v1/orders"
)

@orders_router.post('/choosePaymentType',tags=['Orders'])
async def choose_payment_type(pay_type: int, request: Request):
    if not '_ri' in request.cookies: raise HTTPException(status_code=400, detail={
        'status': 206,
        'message': "Выберете ресторан"
    })
    if not '_oi' in request.cookies: raise HTTPException(status_code=400, detail={
        'status': 502,
        'message': "Сделайте заказ"
    })
    rpt = await RestaurantPayType.get_or_none(restaurant_id=int(request.cookies['_ri']), pay_type_id=pay_type, available=True).prefetch_related('pay_type')
    if not rpt: raise HTTPException(status_code=404, detail={
        'status': 208,
        'message': "Нет такого способа оплаты"
    })
    opt=await OrderPayType.get_or_none(order_id=int(request.cookies['_oi']))
    if not opt: opt=await OrderPayType.create(order_id=int(request.cookies['_oi']),  restaurant_pay_type_id=rpt.id)
    opt.restaurant_pay_type_id=rpt.id
    await opt.save()
    return {'id': rpt.pay_type.id}

@orders_router.get('/getOrder', tags=['Orders'])
async def get_order(request: Request, responce: Response, user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail={
        'status': 502,
        'message': "Нет заказа"
    })
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order:
        responce.delete_cookie('_oi', httponly=True, secure=True, samesite='none')
        raise HTTPException(status_code=404, detail={
        'status': 502,
        'message': "Нет заказа"
    })

    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }

@orders_router.get('/checkActiveOrders', tags=['Orders'])
async def check_active_orders(user_id: AuthGuard = Depends(auth)):
    active_orders = await Order.filter(user_id=user_id, status__gte=1).prefetch_related('address', 'restaurant')
    response_list = []
    if not active_orders: return {'haveActiveOrders': False, 'orders': response_list}
    for order in active_orders:
        log = await OrderLog.get(order_id=order.id)


        if order.status == 3 and (datetime.now(tz=timezone.utc) - log.success_completion_at).seconds > 3599:
            continue

        if order.status == 4 and (datetime.now(tz=timezone.utc) - log.canceled_at).seconds > 3599:
            continue

        response_list.append({
            'order_id': order.id,
            'status': order.status,
            # 'bonuses': order.added_bonuses,
            'product_count': order.products_count,
            'created_at': str(datetime_with_tz(log.created_at, order.restaurant.timezone_IANA))[:-13],
            'sum': order.sum,
            # 'promocode': order.promocode,
            'total_sum': order.sum if not order.total_sum else order.total_sum,
            # 'payment_type': rpt.pay_type_id,
            'type': order.type,
            'address': {'street_id': order.address.street, 'house': order.house, 'entrance': order.entrance,
                        'floor': order.floor, 'apartment': order.apartment},
            'comment': order.comment
        })
    if len(response_list) == 0:
        return {'haveActiveOrders': False, 'orders': []}
    return {'haveActiveOrders': True, 'orders': response_list}


@orders_router.delete('/cancelOrder', tags=['Orders'])
async def cancel_order(order_id: int, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail={
        'status': 501,
        'message': "Этот заказ уже оформлен"
    })
    if not order.status: return "order isnt finished"
    log = await OrderLog.get(order_id=order_id)
    log.canceled_at = datetime.now(tz=timezone.utc)
    log.status=0
    await log.save()
    user = await User.get(id=user_id)
    user.bonuses -= order.added_bonuses
    await user.save()
    if order.promocode_applied:
        promocode = await PromoCode.get(short_name=order.promocode)
        promocode.count += 1
        await promocode.save()
    # send_to_tg
    await order.delete()


@orders_router.post('/finishOrder', tags=['Orders'])
async def finish_order(comment: str, house: str, entrance: str, appartment: str, floor: str,
                       request: Request,
                       response: Response,
                       user_id: AuthGuard = Depends(auth)):
    await check_all_cookies(request.cookies)
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=400, detail={
        'status': 501,
        'message': "Сначала нужно добавить что-нибудь в корзину"
    })
    await check_order_payment_type(order)
    await validate_menu(order)
    if order.invalid_at <= datetime.now(tz=timezone.utc):
        order.status = -1
        await order.save()
        raise HTTPException(status_code=400, detail={
        'status': 505,
        'message': "Пожалуйста, сделаейте заказ еще раз"
    })
    street_query = await Address.get_or_none(id=int(request.cookies['_si']), available=True,
                                             city_id=int(request.cookies['_ci']),
                                             restaurant_id=int(request.cookies['_ri']))
    if street_query is None: raise HTTPException(status_code=400, detail={
        'status': 207,
        'message': "К сожалению, мы сейчас не доставляем на этот адрес"
    })
    r = await Restaurant.get(id=int(request.cookies['_ri']), city_id=int(request.cookies['_ci']))
    if not r: raise HTTPException(status_code=400, detail={
        'status': 205,
        'message': "Пожалуйста, выберите другой ресторан"
    })
    if r.closed < datetime.now(timezone.utc).timetz(): raise HTTPException(status_code=400, detail={
        'status': 209,
        'message': "К сожалению, этот ресторан уже закрыт"
    })
    if r.open > datetime.now(timezone.utc).timetz(): raise HTTPException(status_code=400, detail={
        'status': 209,
            'message': "К сожалению, этот ресторан еще закрыт"
    })
    if not r.working: raise HTTPException(status_code=400, detail={
        'status': 210,
        'message': "К сожалению, этот ресторан сейчас не работает"
    })
    type = 1
    if not r.delivery: raise HTTPException(status_code=400, detail={
        'status': 211,
        'message': "К сожалению, этот ресторан не работает на доставку сейчас"
    })

    await CalculateOrder(order)

    if r.min_sum > order.sum: raise HTTPException(status_code=400, detail={
        'status': 212,
        'message': f"Минимальная сумма доставки к вам - {r.min_sum}р"
    })
    if order.promocode: await validate_promocode(order, order.promocode, user_id)
    log = await OrderLog.get(order_id=order.id)
    log.items = await GetOrderInJSON(order)
    # log.success_completion_at = datetime.now(tz=timezone.utc)
    order.comment = comment
    order.house = house
    order.entrance = entrance
    order.apartment = appartment
    order.floor = floor
    if order.sum >= r.needs_validation_sum:
        order.status = 1
    if order.sum >= r.max_sum:
        order.status = 1
    else:
        order.status = 2
    await log.save()
    await order.save()
    if order.promocode_applied:
        promocode = await PromoCode.get(short_name=order.promocode)
        promocode.count -= 1
        await promocode.save()
    response.delete_cookie('_oi', secure=True, samesite='none')
    # send_order_to_tg
    return "done"


@orders_router.post('/addToOrder', tags=['Orders'])
async def add_to_order(menu_id: int,
                       request: Request,
                       response: Response,
                       user_id: AuthGuard = Depends(auth)
                       ):
    if '_ri' not in request.cookies: raise HTTPException(status_code=400, detail={
        'status': 206,
        'message': "Пожалуйста, выберите ресторан"
    })
    rid = request.cookies['_ri']
    restaurant = await Restaurant.get(id=int(request.cookies['_ri']), city_id=int(request.cookies['_ci']))
    if not restaurant: raise HTTPException(status_code=400, detail={
        'status': 205,
        'message': "Пожалуйста, выберите другой ресторан"
    })
    menu_item = await Menu.get_or_none(id=menu_id, restaurant_id=int(rid), delivery=True)
    if not menu_item: raise HTTPException(status_code=400, detail={
        'status': 401,
        'message': "Продукт не найден"
    })
    if not menu_item.in_stock: raise HTTPException(status_code=400, detail={
        'status': 402,
        'message': "Продукт закончился"
    })

    order = await OrderCheckOrCreate(request.cookies, user_id, response)
    if order.total_sum + menu_item.price > restaurant.max_sum: raise HTTPException(status_code=400, detail={
        'status': 213,
        'message': f"Достигнут лимит корзины"
    })

    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=order.id)
    if not cart_item:
        item = CartItem(order_id=order.id, product_id=menu_item.product_id, menu_id=menu_item.id, quantity=1,
                        bonuses=menu_item.bonuses, sum=menu_item.price)
        await item.save()
    else:
        cart_item.quantity += 1
        cart_item.sum += menu_item.price
        cart_item.bonuses += menu_item.bonuses
        await cart_item.save()

    await CalculateOrder(order)
    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.delete('/removeFromCart', tags=['Orders'])
async def remove_from_cart(menu_id: int,
                           request: Request,
                           user_id: AuthGuard = Depends(auth)
                           ):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail={
        'status': 502,
        'message': "Заказ не найен"
    })
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove from")
    item = await CartItem.get_or_none(menu_id=menu_id, order_id=request.cookies['_oi'])
    if not item: raise HTTPException(status_code=404, detail="No such product")
    await item.delete()

    await CalculateOrder(order)
    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.put('/decreaseQuantity', tags=['Orders'])
async def decrease_quantity(menu_id: int,
                            request: Request,
                            user_id: AuthGuard = Depends(auth)
                            ):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail={
        'status': 502,
        'message': "Заказ не найден"
    })
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail={
        'status': 501,
        'message': "Не откуда убирать"
    })
    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=request.cookies['_oi'])
    if not cart_item: raise HTTPException(status_code=404, detail={
        'status': 504,
        'message': "Нечего понижать"
    })

    menu_item = await Menu.get_or_none(id=menu_id)
    if not menu_item: raise HTTPException(status_code=404, detail={
        'status': 401,
        'message': "Нет такого продукта"
    })
    if cart_item.quantity == 1:
        await cart_item.delete()
    else:
        cart_item.quantity -= 1
        cart_item.sum -= menu_item.price
        cart_item.bonuses -= menu_item.bonuses
        await cart_item.save()

    await CalculateOrder(order)

    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.post('/addPromocode', tags=['Orders'])
async def add_promocode(promocode_short_name: str,
                              request: Request,
                              response: Response,
                              user_id: AuthGuard = Depends(auth)):
    order = await OrderCheckOrCreate(request.cookies, user_id, response)
    promocode = await AddPromocode(order, promocode_short_name, user_id)
    await CalculateOrder(order)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.post('/removePromocode', tags=['Orders'])
async def remove_promocode(
        request: Request,
        user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail={
        'status': 502,
        'message': "Заказ не найден"
    })
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail={
        'status': 501,
        'message': "Нет заказа"
    })

    order.promocode = None
    await order.save()
    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)

    return {
        'order': order,
        'promocode': promocode
    }
