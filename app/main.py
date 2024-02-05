
from app.database import init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware



from app.users.views import user_router
from app.promocodes.views import promocodes_router
from app.products.views import products_router
from app.orders.views import orders_router

app = FastAPI()

init_db(app)

origins = ["http://localhost:3000", "http://localhost:80"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(promocodes_router)
app.include_router(products_router)
app.include_router(orders_router)