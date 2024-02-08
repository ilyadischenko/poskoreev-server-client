from fastapi import HTTPException, APIRouter, Depends
from app.orders.models import Order, CartItem, OrderLog
from app.products.models import Menu
#from app.users.models import User
from app.users.service import AuthGuard, auth
from datetime import datetime, timezone, timedelta
orders_router = APIRouter(
    prefix="/api/v1/orders"
)

@orders_router.get('/getOrder', tags=['Orders'])
async def getOrder(user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: return None
    cart_list=[]
    sum=0
    count=0
    bonuses=0
    for item in await order.items.all():
        cart_list.append({'product_id': item.product_id,
                          'quantity': item.quantity,
                          'sum': item.sum,
                          'bonuses': item.bonuses})
        count+=item.quantity
        sum+=item.sum
        bonuses+=item.bonuses
        order.products_count=count
        order.added_bonuses=bonuses
        order.sum=sum
        order.total_sum=sum
        await order.save()
    log = await OrderLog.get(order_id=order.pk)
    log.items=cart_list
    await log.save()
    return {"user":user_id, "items":cart_list, "bonuses": order.added_bonuses, "products count": order.products_count, "sum": sum}
@orders_router.post('/addToOrder', tags=['Orders'])
async def addToOrder(menu_id: int, user_id: AuthGuard = Depends(auth)):
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    item = await CartItem.get_or_none(product_id=menu_id, user_id=user_id)
    if not item:
        item=CartItem(user_id=user_id, product_id=menu_id, quantity=1, sum=product.price)
        await item.save()
    else:
        item.quantity += 1
        item.sum += product.price
        await item.save()
    order = await Order.get_or_none(user_id=user_id)
    if not order:
        order = await Order.create(user_id=user_id, invalid_at=datetime.now()+timedelta(days=1))
        await OrderLog.create(order_id=order.pk, user_id=user_id)
    await order.items.add(item)
    return await getOrder(user_id)

@orders_router.delete('/removeFromCart', tags=['Orders'])
async def removeFromCart(menu_id: int, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove from")
    item = await CartItem.get_or_none(product_id=menu_id, user_id=user_id)
    if not item: raise HTTPException(status_code=404, detail="No such product")
    await order.items.remove(item)
    await item.delete()
    return await getOrder(user_id)

@orders_router.put('/decreaseQuantity', tags=['Orders'])
async def decreaseQuantity(menu_id: int, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove from")
    item = await CartItem.get_or_none(product_id=menu_id, user_id=user_id)
    if not item: raise HTTPException(status_code=404, detail="Nothing to decrease from")
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    if item.quantity==1 : await removeFromCart(menu_id, user_id)
    else:
        item.quantity -= 1
        item.sum -= product.price
        await item.save()
        await order.items.add(item)
    return await getOrder(user_id)

@orders_router.delete('/removeOrder', tags=['Orders'])
async def removeOrder(user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="Nothing to remove")
    log = await OrderLog.get(order_id=order.pk)
    log.canceled_at=datetime.now()
    await log.save()
    return await order.delete()

@orders_router.post('/finishOrder', tags=['Orders'])
async def finishOrder(user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: raise HTTPException(status_code=404, detail="No order")
    order.status=1
    await order.save()
    log = await OrderLog.get(order_id=order.pk)
    log.status=1
    log.paid_at=datetime.now()
    await log.save()
    return await order.delete()