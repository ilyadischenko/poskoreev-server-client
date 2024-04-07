import asyncio
from datetime import datetime, timezone
import json

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse

from app.orders.models import Order, OrderLog
from app.restaurants.service import datetime_with_tz
from app.users.service import AuthGuard, auth

# from app.orders.views import check_active_orders


orders_router = APIRouter(
    prefix="/api/v1/orders"
)


async def get_orders(user_id):
    # print(request.cookies)
    """
    Generates random value between 0 and 100

    :return: String containing current timestamp (YYYY-mm-dd HH:MM:SS) and randomly generated data.
    """
    # client_ip = request.client.host

    while True:

        json_data = json.dumps(await get_active_orders(user_id))
        yield f"data:{json_data}\n\n"
        await asyncio.sleep(5)


@orders_router.get("/connecttoorderstream")
async def order_stream(request: Request, user_id: AuthGuard = Depends(auth)) -> StreamingResponse:
    response = StreamingResponse(get_orders(user_id), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


async def get_active_orders(user_id):
    active_orders = await Order.filter(user_id=user_id, status__gte=1, status__lt=4).prefetch_related('address', 'restaurant')
    response_list = []
    if not active_orders: return {"haveActiveOrders": False, "orders": response_list}
    for order in active_orders:
        log = await OrderLog.get(order_id=order.id)


        if order.status == 3 and (datetime.now(tz=timezone.utc) - log.success_completion_at).seconds > 1800:
            continue


        print("Отправил заказ")
        response_list.append({
            'order_id': order.id,
            'mainStatus': order.status,
            'logStatus': log.status,
            # 'bonuses': order.added_bonuses,
            'product_count': order.products_count,
            'created_at': str(datetime_with_tz(log.created_at, order.restaurant.timezone_IANA))[:-13],
            'sum': order.sum,
            'total_sum': order.sum if not order.total_sum else order.total_sum,
            # 'payment_type': rpt.pay_type_id,
            'type': order.type,
            'address': {'street_id': order.address.street, 'house': order.house, 'entrance': order.entrance,
                        'floor': order.floor, 'apartment': order.apartment},
            'comment': order.comment
        })
    if len(response_list) == 0:
        return {"haveActiveOrders": False, "orders": []}
    return {"haveActiveOrders": True, "orders": response_list}

