from urllib import request

from fastapi import HTTPException, APIRouter, Depends, Request, Response
from app.orders.models import Order, CartItem, OrderLog
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON
from app.products.models import Menu
# from app.users.models import User
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta

orders_router = APIRouter(
    prefix="/api/v1/orders"
)


@orders_router.get('/getOrder', tags=['Orders'])
async def getOrder(request: Request, user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: return None

    # log = await OrderLog.get(order_id=order.pk)
    # log.items = cart_list
    # await log.save()
    return await GetOrderInJSON(order)



@orders_router.post('/addToOrder', tags=['Orders'])
async def addToOrder(menu_id: int,
                     request: Request,
                     response: Response,
                     user_id: AuthGuard = Depends(auth)
                     ):
    order = await OrderCheckOrCreate(request.cookies, user_id, response)
    menu_item = await Menu.get_or_none(id=menu_id)
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
    return await GetOrderInJSON(order)
    # return await getOrder(user_id)


@orders_router.delete('/removeFromCart', tags=['Orders'])
async def removeFromCart(menu_id: int,
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
    return await GetOrderInJSON(order)


@orders_router.put('/decreaseQuantity', tags=['Orders'])
async def decreaseQuantity(menu_id: int,
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
    return await GetOrderInJSON(order)

@orders_router.delete('/removeOrder', tags=['Orders'])
async def removeOrder(user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove")
    log = await OrderLog.get(order_id=order.pk)
    log.canceled_at = datetime.now()
    await log.save()
    return await order.delete()


@orders_router.post('/finishOrder', tags=['Orders'])
async def finishOrder(user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")
    order.status = 1
    await order.save()
    log = await OrderLog.get(order_id=order.pk)
    log.status = 1
    log.paid_at = datetime.now()
    await log.save()
    return await order.delete()
