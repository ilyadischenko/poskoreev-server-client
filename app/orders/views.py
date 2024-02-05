from fastapi import HTTPException, APIRouter
from app.orders.models import Order, OrderType, OrderStatus, Cart, CartItem
from app.products.models import Menu
orders_router = APIRouter(
    prefix="/api/v1/orders"
)

@orders_router.get('/getCart', tags=['Orders'])
async def getCart(user_id : int):
    cart = await Cart.get_or_none(user_id=user_id)
    if not cart: return None
    cart_list=[]
    for item in await cart.items.all():
        cart_list.append({'product_id': item.product_id,
                          'quantity': item.quantity,
                          'sum': item.sum})
    return cart_list
@orders_router.post('/addToCart', tags=['Orders'])
async def addToCart(menu_id: int, quantity: int, user_id : int):
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    item = await CartItem.get_or_none(product_id=product.id)
    if not item:
        item=CartItem(product_id=product.id, quantity=quantity, sum=quantity*product.price)
        await item.save()
    else:
        item.quantity = quantity
        item.sum = product.price*quantity
        await item.save()
    cart = await Cart.get_or_none(user_id=user_id)
    if not cart:
        cart = await Cart.create(user_id=user_id)
    await cart.items.add(item)
    return await getCart(user_id)

@orders_router.delete('/removeFromCart', tags=['Orders'])
async def removeFromCart(menu_id: int, user_id : int):
    cart = await Cart.get_or_none(user_id=user_id)
    if not cart: return None
    product = await Menu.get_or_none(id=menu_id)
    if not product: raise HTTPException(status_code=404, detail=f"Product {menu_id} not found")
    item = await CartItem.get_or_none(product_id=product.id)
    if not item: raise HTTPException(status_code=404, detail="No such product")
    await cart.items.remove(item)
    await item.delete()
    return await getCart(user_id)