from fastapi import FastAPI

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.config import DB_USER, DB_HOST, DB_PASS, DB_PORT, DB_NAME, isUseProdDB

model_paths = ["app.users.models", "app.promocodes.models", "app.products.models", "app.restaurants.models",
               "app.orders.models",
               "aerich.models"
               ]

TORTOISE_ORM = {
    "connections": {
        "default": f"postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    },
    "apps": {
        "models": {
            "models": model_paths,
            "default_connection": "default",
        },
    },
    "use_tz": False,
}

DEV_TORTOISE_ORM = {
    "connections": {
        "default": "postgres://gen_user:12345678a@82.97.255.65:5432/pizza",
    },
    "apps": {
        "models": {
            "models": model_paths,
            "default_connection": "default",
        },
    },
    "use_tz": False,
}


def init_db(app: FastAPI) -> None:
    if isUseProdDB:
        register_tortoise(
            app,
            config=TORTOISE_ORM,
            modules={"models": model_paths},
            generate_schemas=True,
            add_exception_handlers=True,
        )
    else:
        register_tortoise(
            app,
            config=DEV_TORTOISE_ORM,
            modules={"models": model_paths},
            generate_schemas=True,
            add_exception_handlers=True,
        )


Tortoise.init_models(model_paths, "models")
