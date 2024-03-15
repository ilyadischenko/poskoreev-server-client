from typing import List

import anyio
from starlette.websockets import WebSocketDisconnect
from app.database import init_db
from fastapi import WebSocket, FastAPI
from app.orders.models import Order
from app.orders.services import GetOrderInJSON
app = FastAPI()
init_db(app)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send(self, order_list: list, websocket: WebSocket):
        for order in order_list:
            await websocket.send_json(order)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

@app.get("/orders/{restaurant_id}")
async def get_orders(restaurant_id : int):
    orders = await Order.filter(status=2, restaurant_id=restaurant_id)
    ol=[]
    for order in orders:
        ol.append(await GetOrderInJSON(order))
    return ol
@app.websocket("/ws/{restaurant_id}")
async def websocket_endpoint(restaurant_id : int, websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await manager.send(await get_orders(restaurant_id), websocket)
            await anyio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Restaurant {restaurant_id} disconnected")