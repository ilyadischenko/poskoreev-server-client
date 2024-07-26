import time


from fastapi import Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import server_number
from app.database import init_db
from app.telegram.main import send_message_to_me

from app.users.views import user_router
from app.products.views import products_router
from app.orders.views import orders_router
from app.orders.eventSourcing import orders_router as orders_event_router
from app.restaurants.views import restaurant_router

app = FastAPI(
    # redoc_url=None,
    # docs_url=None
)

init_db(app)

origins = ["http://localhost:3000", "https://test.poissystem.ru", "https://poskoreev.ru"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(user_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(restaurant_router)
app.include_router(orders_event_router)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["Server-ID"] = str(server_number)
    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(exc.detail, status_code=exc.status_code)

@app.middleware("http")
async def catch_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        try:
            await send_message_to_me(f'500 ошибка\n'
                                     f'Роут: {request.url.path}\n'
                                     f'Ошибка: {e}')
        except:
            pass
        return JSONResponse(status_code=500, content={"message": "Нихуя"})
