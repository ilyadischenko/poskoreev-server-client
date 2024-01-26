from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db

from app.users.users_views import user_router
from app.promocodes.promocodes_views import promocodes_router

import socket
socket.getaddrinfo(socket.gethostname(), None)

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