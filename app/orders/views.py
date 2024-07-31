import time
from datetime import datetime, timezone

from fastapi import HTTPException, APIRouter, Depends, Request, Response

from app.app.jwtService import decodeJWT
from app.app.response import getResponseBody
# from app.auth.jwt_handler import decodeJWT
from app.orders.eventSourcing import get_active_orders
from app.orders.models import Order, CartItem, OrderLog, OrderPayType
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, AddPromocode, validate_menu, \
    validate_promocode, check_order_payment_type, CookieCheckerOrder, CCO, GetOrderSnapshotInJSON
from app.products.models import Menu
from app.restaurants.models import Restaurant, RestaurantPayType, DeliveryZones
from app.telegram.main import send_order_to_tg
from app.users.models import User
from app.promocodes.models import PromoCode
from app.users.service import AuthGuard, auth, GetDecodedUserIdOrNone, getUserId, newAuth, NewAuthGuard
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

    order = await Order.get(id=order_id)
    order.paytype = rpt
    await order.save()

    return getResponseBody(data={'id': rpt.pay_type.id})


@orders_router.get('/getOrder', tags=['Orders'])
async def get_order(response: Response,
                    user_id: GetDecodedUserIdOrNone = Depends(getUserId),
                    order_id: CookieCheckerOrder = Depends(CCO),
                    restaurant_id: CookieCheckerRestaurant = Depends(CCR)
                    ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order:
        response.delete_cookie('_oi', httponly=True, secure=True, samesite='none')
        return getResponseBody(status=False, errorCode=501, errorMessage='Такого заказа нет')

    promocode = await AddPromocode(order=order, input_promocode=order.promocode, user_id=user_id,
                                   restaurant_id=restaurant_id)
    order = await GetOrderInJSON(order)
    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })


@orders_router.get('/checkActiveOrders', tags=['Orders'])
async def check_active_orders(user_id: NewAuthGuard = Depends(newAuth)):
    return getResponseBody(data=await get_active_orders(user_id))


@orders_router.post('/finishOrder', tags=['Orders'])
async def finish_order(comment: str, entrance: str, appartment: str, floor: str,
                       response: Response,
                       user_id: NewAuthGuard = Depends(newAuth),
                       order_id: CookieCheckerOrder = Depends(CCO),
                       address: CookieCheckerAddress = Depends(CCA),
                       city_id: CookieCheckerCity = Depends(CCC),
                       restaurant_id: CookieCheckerRestaurant = Depends(CCR)):
    order = await Order.get_or_none(id=order_id, user_id=user_id).prefetch_related('restaurant', 'user')
    if not order: return getResponseBody(
        status=False,
        errorCode=501,
        errorMessage='Сначала нужно добавить что-нибудь в корзину'
    )

    paytype = await check_order_payment_type(order)
    await validate_menu(order)
    # if order.invalid_at <= datetime.now(tz=timezone.utc):
    #     order.status = -1
    #     await order.save()
    #     raise HTTPException(status_code=400, detail={
    #         'status': 505,
    #         'message': "Пожалуйста, сделаейте заказ еще раз"
    #     })

    zone = await DeliveryZones.get_or_none(id=address['zone_id'], is_active=True)
    if zone is None: return getResponseBody(
        status=False,
        errorCode=207,
        errorMessage='К сожалению, мы временно не доставляем к вам :('
    )

    r = await Restaurant.get(id=restaurant_id, city_id=city_id)
    if not r: return getResponseBody(
        status=False,
        errorCode=205,
        errorMessage='Пожалуйста, выберите другой ресторан'
    )

    if r.closed < datetime.now(timezone.utc).timetz(): return getResponseBody(
        status=False,
        errorCode=209,
        errorMessage='К сожалению, этот ресторан уже закрыт'
    )

    if r.open > datetime.now(timezone.utc).timetz(): return getResponseBody(
        status=False,
        errorCode=209,
        errorMessage='К сожалению, этот ресторан еще закрыт'
    )

    if not r.working: return getResponseBody(
        status=False,
        errorCode=210,
        errorMessage='К сожалению, этот ресторан сейчас не работает'
    )

    if not r.delivery: return getResponseBody(
        status=False,
        errorCode=211,
        errorMessage='К сожалению, этот ресторан не работает на доставку сейчас'
    )

    await CalculateOrder(order)

    if r.min_sum > order.total_sum: return getResponseBody(
        status=False,
        errorCode=212,
        errorMessage=f'Минимальная сумма доставки к вам - {r.min_sum}р'
    )


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
    saved_order = await OrderLog.create(
        created_at=datetime.now(timezone.utc),
        items=await GetOrderSnapshotInJSON(order, paytype),
        status=logstatus,
        user_id=order.user_id,
        restaurant_id=order.restaurant_id
    )

    try:
        await send_order_to_tg(saved_order, user_number)
    except:
        pass

    await order.delete()
    await CartItem.filter(order_id=order_id).delete()

    response.delete_cookie('_oi', secure=True, samesite='none')
    return getResponseBody()


@orders_router.post('/addToOrder', tags=['Orders'])
async def add_to_order(menu_id: int,
                       request: Request,
                       response: Response,
                       user_id: GetDecodedUserIdOrNone = Depends(getUserId),
                       restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                       address: CookieCheckerAddress = Depends(CCA),
                       city_id: CookieCheckerCity = Depends(CCC)):
    restaurant = await Restaurant.get_or_none(id=restaurant_id, city_id=city_id)
    if not restaurant: return getResponseBody(status=False, errorCode=205,
                                              errorMessage='Пожалуйста, выберите другой ресторан')

    menu_item = await Menu.get_or_none(id=menu_id, restaurant_id=restaurant_id, delivery=True,
                                       visible=True).prefetch_related('product')
    if not menu_item: return getResponseBody(status=False, errorCode=401,
                                             errorMessage='Продукт не найден или недоступен сейчас')
    if not menu_item.in_stock: return getResponseBody(status=False, errorCode=402, errorMessage='Продукт закончился')

    order = await OrderCheckOrCreate(cookies=request.cookies, response=response,
                                     restaurant_id=restaurant_id, address=address['address'], user_id=user_id)

    if order.total_sum + menu_item.price > restaurant.max_sum: return getResponseBody(status=False, errorCode=213,
                                                                                      errorMessage='Достигнут лимит корзины')

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

    promocode = await AddPromocode(order, order.promocode, restaurant_id, user_id)
    order = await GetOrderInJSON(order)
    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })


@orders_router.delete('/removeFromCart', tags=['Orders'])
async def remove_from_cart(menu_id: int,
                           user_id: GetDecodedUserIdOrNone = Depends(getUserId),
                           order_id: CookieCheckerOrder = Depends(CCO),
                           restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                           ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: return getResponseBody(
        status=False,
        errorCode=501,
        errorMessage='Сначала добавьте что-нибудь в корзину'
    )

    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=order_id)
    if not cart_item: return getResponseBody(
        status=False,
        errorCode=504,
        errorMessage='Сначала добавьте что-нибудь в корзину'
    )
    await cart_item.delete()

    await CalculateOrder(order)
    promocode = await AddPromocode(order, order.promocode, user_id, restaurant_id)
    order = await GetOrderInJSON(order)
    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })


@orders_router.put('/decreaseQuantity', tags=['Orders'])
async def decrease_quantity(menu_id: int,
                            user_id: GetDecodedUserIdOrNone = Depends(getUserId),
                            order_id: CookieCheckerOrder = Depends(CCO),
                            restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                            ):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: return getResponseBody(
        status=False,
        errorCode=501,
        errorMessage='Сначала добавьте что-нибудь в корзину'
    )

    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=order_id)
    if not cart_item: return getResponseBody(
        status=False,
        errorCode=504,
        errorMessage='Сначала добавьте что-нибудь в корзину'
    )

    menu_item = await Menu.get_or_none(id=menu_id)
    if not menu_item: return getResponseBody(
        status=False,
        errorCode=401,
        errorMessage='Такого продукта нет или он временно отключен'
    )

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
    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })


@orders_router.post('/addPromocode', tags=['Orders'])
async def add_promocode(promocode_short_name: str,
                        request: Request,
                        response: Response,
                        user_id: GetDecodedUserIdOrNone = Depends(getUserId),
                        restaurant_id: CookieCheckerRestaurant = Depends(CCR),
                        address: CookieCheckerAddress = Depends(CCA)):
    order = await OrderCheckOrCreate(request.cookies, user_id, response, restaurant_id, address['address'])
    promocode = await AddPromocode(order, promocode_short_name, restaurant_id,  user_id )
    await CalculateOrder(order)
    order = await GetOrderInJSON(order)
    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })


@orders_router.post('/removePromocode', tags=['Orders'])
async def remove_promocode(
        user_id: GetDecodedUserIdOrNone = Depends(getUserId),
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
    promocode = await AddPromocode(order, order.promocode, restaurant_id, user_id)
    order = await GetOrderInJSON(order)

    return getResponseBody(data={
        'order': order,
        'promocode': promocode
    })
