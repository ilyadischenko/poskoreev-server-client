import asyncio
from datetime import datetime, timezone, timedelta
import json

from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import StreamingResponse
from tortoise.expressions import Q

from app.app.response import getResponseBody
from app.orders.models import Order, OrderLog
from app.restaurants.models import Restaurant
from app.restaurants.service import datetime_with_tz
from app.users.service import AuthGuard, auth, NewAuthGuard, newAuth

# from app.orders.views import check_active_orders


orders_router = APIRouter(
    prefix="/api/v1/orders"
)


async def get_orders(user_id):
    while True:

        json_data = json.dumps(await get_active_orders(user_id))
        yield f"data:{json_data}\n\n"
        await asyncio.sleep(5)


@orders_router.get("/connecttoorderstream")
async def order_stream(request: Request, user_id: NewAuthGuard = Depends(newAuth)) -> StreamingResponse:
    response = StreamingResponse(get_orders(user_id), media_type="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


async def get_active_orders(user_id):
    today = datetime.now(timezone.utc) - timedelta(days=1)

    active_orders = await OrderLog.filter(
                                          Q(Q(status=0), Q(status=1), Q(status=2), Q(status=3),
                                            # Q(status=4),
                                            Q(status=6),
                                            join_type="OR"),
                                            user_id=user_id,
                                            created_at__gt=today.strftime("%Y-%m-%d")

                                       ).prefetch_related('restaurant')
    response_list = []
    if not active_orders: return {"haveActiveOrders": False, "orders": response_list}

    def get_time_in_tz(time, tz):
        if time != None:
            return str(datetime_with_tz(time, tz).time())[:-10]
        return ''
    for order in active_orders:

        if order.status == 4 and (datetime.now(tz=timezone.utc) - order.success_completion_at).seconds > 1800:
            continue

        response_list.append({
            'order_id': order.id,
            'status': order.status,
            'items': order.items,
            'logs': {
                'created_at': get_time_in_tz(order.created_at, order.restaurant.timezone_IANA),
                'canceled_at': get_time_in_tz(order.canceled_at, order.restaurant.timezone_IANA),
                'start_cooking': get_time_in_tz(order.start_cooking, order.restaurant.timezone_IANA),
                # 'canceled_cooking': get_time_in_tz(log.canceled_cooking, order.restaurant.timezone_IANA),
                'start_delivering': get_time_in_tz(order.start_delivering, order.restaurant.timezone_IANA),
                'success_completion_at': get_time_in_tz(order.success_completion_at, order.restaurant.timezone_IANA),
            },
        })
    if len(response_list) == 0:
        #has*
        return {"haveActiveOrders": False, "orders": []}
    return {"haveActiveOrders": True, "orders": response_list}

