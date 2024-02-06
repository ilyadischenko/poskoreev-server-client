from fastapi import HTTPException, APIRouter, Depends
from app.orders.models import Order, CartItem
from app.products.models import Menu
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
    for item in await order.items.all():
        cart_list.append({'product_id': item.product_id,
                          'quantity': item.quantity,
                          'sum': item.sum})
        count+=item.quantity
        sum+=item.sum
        order.products_count=count
        order.sum=sum
        await order.save()
    return {"user":order.pk, "items":cart_list, "sum": sum}
@orders_router.post('/addToOrder', tags=['Orders'])
async def addToOrder(menu_id: int, quantity: int, user_id: AuthGuard = Depends(auth)):
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    item = await CartItem.get_or_none(product_id=menu_id, user_id=user_id)
    if not item:
        item=CartItem(user_id=user_id, product_id=menu_id, quantity=quantity, sum=quantity*product.price)
        await item.save()
    else:
        item.quantity = quantity
        item.sum = product.price*quantity
        await item.save()
    order = await Order.get_or_none(user_id=user_id)
    if not order:
        order = await Order.create(user_id=user_id, invalid_at=datetime.now()+timedelta(days=1))
    await order.items.add(item)
    return await getOrder(user_id)

@orders_router.delete('/removeFromCart', tags=['Orders'])
async def removeFromCart(menu_id: int, user_id: AuthGuard = Depends(auth)):
    order = await Order.get_or_none(user_id=user_id)
    if not order: return None
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    item = await CartItem.get_or_none(product_id=menu_id, user_id=user_id)
    if not item: raise HTTPException(status_code=404, detail="No such product")
    await order.items.remove(item)
    await item.delete()
    return await getOrder(user_id)