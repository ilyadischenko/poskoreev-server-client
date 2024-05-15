import asyncio
from datetime import datetime, timezone, timedelta
import json

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse

from app.orders.models import Order, OrderLog
from app.restaurants.models import Restaurant
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
    today = datetime.now(timezone.utc) - timedelta(days=2)
    active_orders = await Order.filter(user_id=user_id, status__gte=1, status__lt=4, invalid_at__gte=today.strftime("%Y-%m-%d"),).prefetch_related('restaurant')
    response_list = []
    if not active_orders: return {"haveActiveOrders": False, "orders": response_list}

    def get_time_in_tz(time, tz):
        if time != None:
            return str(datetime_with_tz(time, tz).time())[:-10]
        return ''
    for order in active_orders:
        log = await OrderLog.get(order_id=order.id)


        if log.status == 4 and (datetime.now(tz=timezone.utc) - log.success_completion_at).seconds > 1800:
            continue

        response_list.append({
            'order_id': order.id,
            'mainStatus': order.status,
            'logStatus': log.status,
            'items': log.items,
            'logs': {
                'created_at': get_time_in_tz(log.created_at, order.restaurant.timezone_IANA),
                'canceled_at': get_time_in_tz(log.canceled_at, order.restaurant.timezone_IANA),
                'start_cooking': get_time_in_tz(log.start_cooking, order.restaurant.timezone_IANA),
                # 'canceled_cooking': get_time_in_tz(log.canceled_cooking, order.restaurant.timezone_IANA),
                'start_delivering': get_time_in_tz(log.start_delivering, order.restaurant.timezone_IANA),
                'success_completion_at': get_time_in_tz(log.success_completion_at, order.restaurant.timezone_IANA),
            },
            # 'bonuses': order.added_bonuses,
            'product_count': order.products_count,
            'created_at': str(datetime_with_tz(log.created_at, order.restaurant.timezone_IANA))[:-13],
            'sum': order.sum,
            'total_sum': order.sum if not order.total_sum else order.total_sum,
            # 'payment_type': rpt.pay_type_id,
            'type': order.type,
            'address': {'address': order.address, 'entrance': order.entrance,
                        'floor': order.floor, 'apartment': order.apartment},
            'comment': order.comment
        })
    if len(response_list) == 0:
        #has*
        return {"haveActiveOrders": False, "orders": []}
    return {"haveActiveOrders": True, "orders": response_list}

