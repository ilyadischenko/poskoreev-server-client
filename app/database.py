from fastapi import FastAPI

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

model_paths = ["app.users.users_models", "app.promocodes.promocodes_models"]

TORTOISE_ORM = {
    "connections": {
        # i change postgres to localhost, because local i cant connect to db
        "default": "postgres://user:1234@localhost:5432/pizza",
    },
    "apps": {
        "models": {
            "models": ["app.users.users_models", "app.promocodes.promocodes_models", "app.products.products_models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
}
def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        modules={"models": model_paths},
        generate_schemas=True,
        add_exception_handlers=True,
    )


Tortoise.init_models(model_paths, "models")
