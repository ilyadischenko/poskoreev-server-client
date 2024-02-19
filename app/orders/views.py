from fastapi import HTTPException, APIRouter, Depends, Request, Response
from app.orders.models import Order, CartItem, OrderLog
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, check_promocode, AddPromocode, validate_order
from app.products.models import Menu
from app.restaurants.models import Restaurant, Address
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta

orders_router = APIRouter(
    prefix="/api/v1/orders"
)

@orders_router.post('/pickRestaurant', tags=['Orders'])
async def pick_restaurant(restaurant_id: int, response: Response):
    restaurant = await Restaurant.get_or_none(id=restaurant_id)
    if not restaurant: raise HTTPException(status_code=404, detail="Restaurant not found")
    response.set_cookie('_ri',value=restaurant.pk, httponly=True, samesite='none', secure=True)
    return
@orders_router.post('/pickAdress', tags=['Orders'])
async def pick_address(street : str,response: Response, request: Request):
    rid = request.cookies['_ri']
    if not rid: raise HTTPException(status_code=400, detail="PLEASE pick restaurant")
    address = await Address.get_or_none(street=street, restaurant_id=int(rid))
    if not address: raise HTTPException(status_code=400, detail="doesnt exist or unreachable by this restaurant")
    if not address.available: raise HTTPException(status_code=400, detail="temporally(hopefully) unavailable")
    response.set_cookie('_ai', value=address.pk, httponly=True, samesite='none', secure=True)
    return
@orders_router.get('/getOrder', tags=['Orders'])
async def get_order(request: Request, response: Response, user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order:
        # надо бы удалять куки, но я пока не пойму как
        # response.delete_cookie('_oi')
        raise HTTPException(status_code=404, detail="Order not found")

    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)
    return {
        'order': order,
        'promocode': promocode
    }


@orders_router.post('/addToOrder', tags=['Orders'])
async def add_to_order(menu_id: int,
                     request: Request,
                     response: Response,
                     user_id: AuthGuard = Depends(auth)
                     ):
    rid = request.cookies['_ri']
    if not rid: raise HTTPException(status_code=400, detail="PLEASE pick restaurant")
    order = await OrderCheckOrCreate(request.cookies, user_id, response)
    menu_item = await Menu.get_or_none(id=menu_id, restaurant_id=int(rid))
    if not menu_item: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
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
    await validate_order(request.cookies, order)
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
    await validate_order(request.cookies, order)
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


# @orders_router.delete('/removeOrder', tags=['Orders dev'])
# async def removeOrder(request: Request, user_id: AuthGuard = Depends(auth)):
#     #order = await Order.get_or_none(order_id=request.cookies['_oi'], user_id=user_id)
#     order = await Order.get_or_none(user_id=user_id)
#     if not order: raise HTTPException(status_code=404, detail="Nothing to remove")
#     log = await OrderLog.get(order_id=order.pk)
#     log.canceled_at = datetime.now()
#     await log.save()
#     return await order.delete()


# @orders_router.post('/finishOrder', tags=['Orders dev'])
# async def finishOrder(user_id: AuthGuard = Depends(auth)):
#     order = await Order.get_or_none(user_id=user_id)
#     if not order: raise HTTPException(status_code=404, detail="No order")
#     await check_promocode(order)
#     order.status = 1
#     await order.save()
#     log = await OrderLog.get(order_id=order.pk)
#     log.status = 1
#     log.paid_at = datetime.now()
#     await log.save()
#     promocode = await PromoCode.get_or_none(short_name=order.promocode)
#     if promocode:
#         promocode.count-=1
#         await promocode.save()
#     return await order.delete()

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
    await validate_order(request.cookies, order)
    if not order: raise HTTPException(status_code=404, detail="No order")

    order.promocode = None
    await order.save()
    promocode = await AddPromocode(order, order.promocode, user_id)
    order = await GetOrderInJSON(order)

    return {
        'order': order,
        'promocode': promocode
    }
