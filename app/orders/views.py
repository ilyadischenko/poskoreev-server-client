from fastapi import HTTPException, APIRouter, Depends, Request, Response
from app.orders.models import Order, CartItem, OrderLog
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, AddPromocode, validate_menu, \
    validate_promocode
from app.products.models import Menu
from app.restaurants.models import Restaurant, Address
from app.users.models import User
from app.promocodes.models import PromoCode
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta

orders_router = APIRouter(
    prefix="/api/v1/orders"
)


@orders_router.get('/getOrder', tags=['Orders'])
async def get_order(request: Request, responce: Response, user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order:
        # чтобы удалить куки нужен пост мб но я пока не понял зачем их удалять
        raise HTTPException(status_code=404, detail="Order not found")

    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }

@orders_router.get('/checkActiveOrders', tags=['Orders'])
async def check_active_orders(user_id: AuthGuard = Depends(auth)):
    active_orders = await Order.filter(user_id=user_id, status__gte=1)
    responce_list = []
    if not active_orders: return responce_list
    for order in active_orders:
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
        responce_list.append({
            'order id': order.id,
            'status': order.status,
            'items': cart_list,
            'bonuses': order.added_bonuses,
            'product_count': order.products_count,
            'sum': order.sum,
            'promocode': order.promocode,
            'total sum': order.sum if not order.total_sum else order.total_sum,
            'payment type': order.pay_type,
            'type': order.type,
            'address': {'street id': order.address_id, 'house': order.house, 'entrance': order.entrance,
                        'floor': order.floor, 'apartment': order.apartment},
            'restaurant id': order.restaurant_id,
            'comment': order.comment
        })
    return responce_list


@orders_router.delete('/cancelOrder', tags=['Orders'])
async def cancel_order(order_id: int, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=order_id, user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Order finished")
    if not order.status: return "order isnt finished"
    log = await OrderLog.get(order_id=order_id)
    log.canceled_at = datetime.now()
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
async def finish_order( pay_type: int, comment: str, house: str, entrance: str, appartment: str, floor: str,
                       request: Request,
                       response: Response,
                       user_id: AuthGuard = Depends(auth)):
    if '_at' not in request.cookies: raise HTTPException(status_code=401, detail="unauthorized")
    if '_oi' not in request.cookies: raise HTTPException(status_code=400, detail="make order first")
    if '_ci' not in request.cookies: raise HTTPException(status_code=400, detail="pick city")
    if '_ri' not in request.cookies: raise HTTPException(status_code=400, detail="pick restaurant")
    if '_si' not in request.cookies: raise HTTPException(status_code=400, detail="pick street")
    if pay_type < 0 or pay_type > 1: raise HTTPException(status_code=400, detail="please pick correct payment variant (0 - cash, 1 - card)")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=400, detail="make an order first")
    await validate_menu(order)
    if order.invalid_at <= datetime.now(tz=timezone.utc):
        log = await OrderLog.get(order_id=order.id)
        log.status = 2
        await log.save()
        raise HTTPException(status_code=400, detail="order expired")
    street_query = await Address.get_or_none(id=int(request.cookies['_si']), available=True,
                                             city_id=int(request.cookies['_ci']),
                                             restaurant_id=int(request.cookies['_ri']))
    if street_query is None: raise HTTPException(status_code=400, detail="address isnt viable anymore")
    r = await Restaurant.get(id=int(request.cookies['_ri']), city_id=int(request.cookies['_ci']))
    if r.closed < datetime.now(timezone.utc).timetz(): raise HTTPException(status_code=400, detail=f"this restaurant was closed at {r.closed}")
    if r.open > datetime.now(timezone.utc).timetz(): raise HTTPException(status_code=400, detail=f"this restaurant will be opened at {r.open}")
    if not r.working: raise HTTPException(status_code=400, detail="this restaurant isnt working")
    type = 1
    if not r.delivery: raise HTTPException(status_code=400, detail="this restaurant doesnt support this type")

    await CalculateOrder(order)

    if r.min_sum > order.sum: raise HTTPException(status_code=400, detail=f"too cheap min sum {r.min_sum} while yours {order.sum}")
    if order.promocode: await validate_promocode(order, order.promocode, user_id)
    log = await OrderLog.get(order_id=order.id)
    log.items = await GetOrderInJSON(order)
    log.type = type
    log.success_completion_at = datetime.now()
    await log.save()
    order.comment = comment
    order.house = house
    order.entrance = entrance
    order.apartment = appartment
    order.floor = floor
    if order.sum >= 3000: order.status = 1
    else: order.status = 2
    await order.save()
    if order.promocode_applied:
        promocode = await PromoCode.get(short_name=order.promocode)
        promocode.count -= 1
        await promocode.save()
    response.delete_cookie('_oi')
    # send_order_to_tg
    return "done"


@orders_router.post('/addToOrder', tags=['Orders'])
async def add_to_order(menu_id: int,
                       request: Request,
                       response: Response,
                       user_id: AuthGuard = Depends(auth)
                       ):
    if '_ri' not in request.cookies: raise HTTPException(status_code=400, detail="PLEASE pick restaurant")
    rid = request.cookies['_ri']
    menu_item = await Menu.get_or_none(id=menu_id, restaurant_id=int(rid))
    if not menu_item: raise HTTPException(status_code=404, detail=f"Продукт {menu_id} не найден")
    if not menu_item.in_stock: raise HTTPException(status_code=400, detail="Продукт закончился")

    order = await OrderCheckOrCreate(request.cookies, user_id, response)
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
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
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
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove from")
    cart_item = await CartItem.get_or_none(menu_id=menu_id, order_id=request.cookies['_oi'])
    if not cart_item: raise HTTPException(status_code=404, detail="Nothing to decrease from")

    menu_item = await Menu.get_or_none(id=menu_id)
    if not menu_item: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
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
async def add_promocode_route(promocode_short_name: str,
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
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")

    order.promocode = None
    await order.save()
    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)

    return {
        'order': order,
        'promocode': promocode
    }
