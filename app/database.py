from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

# List of model paths
model_paths = ["users.users_models", "promocodes.promocodes_models"]

# Initialize Tortoise and provide the list of model paths
Tortoise.init_models(model_paths, "models")

# Database configuration
TORTOISE_ORM = {
    "connections": {
        "default": "postgres://postgres:1234@localhost:5432/test",
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
    # Register Tortoise with FastAPI
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        modules={"models": model_paths},
        generate_schemas=True,
        add_exception_handlers=True,
    )
