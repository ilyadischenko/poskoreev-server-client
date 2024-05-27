import time
from datetime import datetime, timezone

from fastapi import HTTPException, APIRouter, Depends, Request, Response

from app.orders.eventSourcing import get_active_orders
from app.orders.models import Order, CartItem, OrderLog, OrderPayType
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, AddPromocode, validate_menu, \
    validate_promocode, check_order_payment_type, CookieCheckerOrder, CCO, GetOrderSnapshotInJSON
from app.products.models import Menu
from app.restaurants.models import Restaurant, RestaurantPayType
from app.telegram.main import send_order_to_tg
from app.users.models import User
from app.promocodes.models import PromoCode
from app.users.service import AuthGuard, auth
from app.restaurants.service import CookieCheckerRestaurant, CCR, CookieCheckerCity, CCC, \
    CookieCheckerAddress, CCA

orders_router = APIRouter(
    prefix="/api/v1/orders"
)


@orders_router.post('/choosePaymentType', tags=['Orders'])
async def choose_payment_type(pay_type: int,
                              restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                              order_id: CookieCheckerOrder = Depends(CCO)):
    rpt = await RestaurantPayType.get_or_none(restaurant_id=restaurant_id, pay_type_id=pay_type,
                                              available=True).prefetch_related('pay_type')
    if not rpt: raise HTTPException(status_code=404, detail={
        'status': 208,
        'message': "Нет такого способа оплаты"
    })
    opt = await OrderPayType.get_or_none(order_id=order_id)
    if not opt: opt = await OrderPayType.create(order_id=order_id, restaurant_pay_type_id=rpt.id)
    opt.restaurant_pay_type_id = rpt.id
    await opt.save()
    return {'id': rpt.pay_type.id}


@orders_router.get('/getOrder', tags=['Orders'])
async def get_order(response: Response,
                    user_id: AuthGuard = Depends(auth),
                    order_id: CookieCheckerOrder = Depends(CCO),
                    restaurant_id: CookieCheckerRestaurant = Depends(CCR)
                    ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order:
        response.delete_cookie('_oi', httponly=True, secure=True, samesite='none')
        raise HTTPException(status_code=404, detail={
            'status': 501,
            'message': "Нет заказа"
        })

    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.get('/checkActiveOrders', tags=['Orders'])
async def check_active_orders(user_id: AuthGuard = Depends(auth)):
    return await get_active_orders(user_id)


# @orders_router.delete('/cancelOrder', tags=['Orders'])
# async def cancel_order(order_id: int, user_id: AuthGuard = Depends(auth)):
#     order = await Order.get_or_none(id=order_id, user_id=user_id)
#     if not order: raise HTTPException(status_code=404, detail={
#         'status': 501,
#         'message': "Этот заказ уже оформлен"
#     })
#     if not order.status: return "order isnt finished"
#     log = await OrderLog.get(order_id=order_id)
#     log.canceled_at = datetime.now(tz=timezone.utc)
#     log.status = 0
#     await log.save()
#     user = await User.get(id=user_id)
#     user.bonuses -= order.added_bonuses
#     await user.save()
#     if order.promocode_applied:
#         promocode = await PromoCode.get(short_name=order.promocode)
#         promocode.count += 1
#         await promocode.save()
#     # send_to_tg
#     await order.delete()


@orders_router.post('/finishOrder', tags=['Orders'])
async def finish_order(comment: str, entrance: str, appartment: str, floor: str,
                       response: Response,
                       user_id: AuthGuard = Depends(auth),
                       order_id: CookieCheckerOrder = Depends(CCO),
                       address: CookieCheckerAddress = Depends(CCA),
                       city_id: CookieCheckerCity = Depends(CCC),
                       restaurant_id: CookieCheckerRestaurant = Depends(CCR)):
    order = await Order.get_or_none(id=order_id, user_id=user_id).prefetch_related( 'restaurant', 'user')
    if not order: raise HTTPException(status_code=400, detail={
        'status': 501,
        'message': "Сначала нужно добавить что-нибудь в корзину"
    })
    paytype = await check_order_payment_type(order)
    await validate_menu(order)
    # if order.invalid_at <= datetime.now(tz=timezone.utc):
    #     order.status = -1
    #     await order.save()
    #     raise HTTPException(status_code=400, detail={
    #         'status': 505,
    #         'message': "Пожалуйста, сделаейте заказ еще раз"
    #     })

    # street_query = await Address.get_or_none(id=street_id, available=True,
    #                                          city_id=city_id,
    #                                          restaurant_id=restaurant_id)
    # if street_query is None: raise HTTPException(status_code=400, detail={
    #     'status': 207,
    #     'message': "К сожалению, мы сейчас не доставляем на этот адрес"
    # })
    r = await Restaurant.get(id=restaurant_id, city_id=city_id)
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

    order.address = address['address']
    order.comment = comment
    order.entrance = entrance
    order.apartment = appartment
    order.floor = floor

    await order.save()
    if order.total_sum >= r.needs_validation_sum or order.sum >= r.max_sum:
        order.status = 1
        logstatus = 6
    if order.total_sum < r.needs_validation_sum and order.sum < r.max_sum:
        order.status = 2
        logstatus = 0
    if order.promocode_applied:
        promocode = await PromoCode.get(short_name=order.promocode)
        promocode.count -= 1
        await promocode.save()

    user_number = order.user.number
    now = datetime.now(timezone.utc)
    saved_order = await OrderLog.create(
        created_at = now,
        items = await GetOrderSnapshotInJSON(order, paytype),
        status=logstatus,
        user_id=order.user_id,
        restaurant_id=order.restaurant_id
    )
    await send_order_to_tg(saved_order, user_number)

    await order.delete()
    await CartItem.filter(order_id=order_id).delete()

    response.delete_cookie('_oi', secure=True, samesite='none')
    return "done"


@orders_router.post('/addToOrder', tags=['Orders'])
async def add_to_order(menu_id: int,
                       request: Request,
                       response: Response,
                       user_id: AuthGuard = Depends(auth),
                       restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                       address: CookieCheckerAddress = Depends(CCA),
                       city_id: CookieCheckerCity = Depends(CCC)):
    restaurant = await Restaurant.get_or_none(id=restaurant_id, city_id=city_id)
    if not restaurant: raise HTTPException(status_code=400, detail={
        'status': 205,
        'message': "Пожалуйста, выберите другой ресторан"
    })
    menu_item = await Menu.get_or_none(id=menu_id, restaurant_id=restaurant_id, delivery=True).prefetch_related('product')
    if not menu_item: raise HTTPException(status_code=400, detail={
        'status': 401,
        'message': "Продукт не найден"
    })
    if not menu_item.in_stock: raise HTTPException(status_code=400, detail={
        'status': 402,
        'message': "Продукт закончился"
    })

    order = await OrderCheckOrCreate(request.cookies, user_id, response, restaurant_id, address['address'])
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

    start_time = time.time()
    await CalculateOrder(order)
    process_time = time.time() - start_time
    response.headers["X-calculate-order-Time"] = str(process_time)

    start_time = time.time()
    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    process_time = time.time() - start_time
    response.headers["X-add-promocode-Time"] = str(process_time)

    start_time = time.time()
    order = await GetOrderInJSON(order)
    process_time = time.time() - start_time
    response.headers["X-get-order-in-json-Time"] = str(process_time)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.delete('/removeFromCart', tags=['Orders'])
async def remove_from_cart(menu_id: int,
                           user_id: AuthGuard = Depends(auth),
                           order_id: CookieCheckerOrder = Depends(CCO),
                            restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                           ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: raise HTTPException(status_code=400, detail="Nothing to remove from")
    item = await CartItem.get_or_none(menu_id=menu_id, order_id=order_id)
    if not item: raise HTTPException(status_code=400, detail="No such product")
    await item.delete()

    await CalculateOrder(order)
    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.put('/decreaseQuantity', tags=['Orders'])
async def decrease_quantity(menu_id: int,
                            user_id: AuthGuard = Depends(auth),
                            order_id: CookieCheckerOrder = Depends(CCO),
                            restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                            ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail={
        'status': 501,
        'message': "Неоткуда убирать"
    })
    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=order_id)
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

    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.post('/addPromocode', tags=['Orders'])
async def add_promocode(promocode_short_name: str,
                        request: Request,
                        response: Response,
                        user_id: AuthGuard = Depends(auth),
                        restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                        address: CookieCheckerAddress = Depends(CCA)):
    order = await OrderCheckOrCreate(request.cookies, user_id, response, restaurant_id, address['address'])
    promocode = await AddPromocode(order, promocode_short_name, user_id, restaurant_id)
    await CalculateOrder(order)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.post('/removePromocode', tags=['Orders'])
async def remove_promocode(
        user_id: AuthGuard = Depends(auth),
        order_id: CookieCheckerOrder = Depends(CCO),
        restaurant_id: CookieCheckerRestaurant = Depends(CCR),
):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail={
        'status': 501,
        'message': "Нет заказа"
    })

    order.promocode = None
    await order.save()
    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    order = await GetOrderInJSON(order)

    return {
        'order': order,
        'promocode': promocode
    }
