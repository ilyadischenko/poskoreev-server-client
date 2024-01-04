from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

Tortoise.init_models(["users.users_models"], "models")

TORTOISE_ORM = {
    "connections": {
        "default": "postgres://postgres:1234@localhost:5432/test",
    },
    "apps": {
        "models": {
            "models": ["users.users_models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
}

def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        modules={"models": ["users.users_models"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )