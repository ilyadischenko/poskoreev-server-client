
from fastapi import HTTPException, APIRouter, Depends, Request, Response
from fastapi.responses import PlainTextResponse
from app.orders.models import Order, CartItem, OrderLog
from app.orders.services import OrderCheckOrCreate, CalculateOrder, GetOrderInJSON, check_promocode
from app.products.models import Menu
from app.users.models import User
from app.promocodes.models import PromoCode
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta

orders_router = APIRouter(
    prefix="/api/v1/orders"
)


@orders_router.get('/getOrder', tags=['Orders'])
async def getOrder(request: Request, response: Response, user_id: AuthGuard = Depends(auth)):
    if '_oi' not in request.cookies: raise HTTPException(status_code=404, detail="Order not found")
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order:
        # надо бы удалять куки, но я пока не пойму как
        # response.delete_cookie('_oi')
        raise HTTPException(status_code=404, detail="Order not found")
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
    await check_promocode(order)
    return await GetOrderInJSON(order)


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
    await check_promocode(order)
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
    await check_promocode(order)
    return await GetOrderInJSON(order)

@orders_router.delete('/removeOrder', tags=['Orders dev'])
async def removeOrder(request: Request, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove")
    log = await OrderLog.get(order_id=order.pk)
    log.canceled_at = datetime.now()
    await log.save()
    return await order.delete()


@orders_router.post('/finishOrder', tags=['Orders dev'])
async def finishOrder(request: Request, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")
    await check_promocode(order)
    order.status = 1
    await order.save()
    log = await OrderLog.get(order_id=order.pk)
    log.status = 1
    log.paid_at = datetime.now()
    await log.save()
    promocode = await PromoCode.get_or_none(short_name=order.promocode)
    if promocode:
        promocode.count-=1
        await promocode.save()
    return await order.delete()

@orders_router.post('/addPromocode', tags=['Orders'])
async def addPromocode(request: Request, promocode : str, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=request.cookies['_oi'], user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")
    if order.promocode: await removePromocode(request, user_id)
    user = await User.get(id=user_id)
    # user_promocode = await user.get_promocode(promocode)
    # if not user_promocode: raise HTTPException(status_code=404, detail="No promocode???")
    user_promocodes = await user.get_all_promocodes_dev()
    for i in user_promocodes:
        if promocode == i["promocode"]:
            if i["minimal_sum"] <= order.sum:
                if i["type"]==2:
                    order.total_sum=round(order.sum*(1-i["effect"]*0.01), 2)
                elif i["type"]==3:
                    order.total_sum = order.sum - i["effect"]
                if order.total_sum <= 0 : raise HTTPException(status_code=405, detail="what")
                order.promocode = promocode
                order.promocode_valid = True
                await order.save()
                promocode = await PromoCode.get(id=i["id"])
                return {"valid": order.promocode_valid,
                        "min sum": promocode.min_sum,
                        "effect": promocode.effect,
                        "message": "idk"
                        }
            else: return "sum too small for code to work"
    return "u dont have that or it doesnt exist or it expired or u just unlucky"

@orders_router.post('/removePromocode', tags=['Orders'])
async def removePromocode(request: Request, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(id=request.cookies['_oi'],user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")
    order.promocode=None
    order.total_sum = order.sum
    order.promocode_valid = False
    await order.save()
    return order