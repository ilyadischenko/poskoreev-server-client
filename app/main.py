from app.database import init_db
from fastapi import FastAPI
from app.users.users_views import user_router
from app.promocodes.promocodes_views import promocodes_router

app = FastAPI()

init_db(app)

app.include_router(user_router)
app.include_router(promocodes_router)