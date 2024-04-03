from fastapi import FastAPI

from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

model_paths = ["app.users.models", "app.promocodes.models", "app.products.models", "app.restaurants.models",
               "app.orders.models",
               "aerich.models"
               ]

admin_model_paths = ["app.restaurants.admin"]

TORTOISE_ORM = {

    "connections": {
        # "default": "postgres://gzabjmhg:jm4CMJAWNG8itVAWRpGKUdSGcFt6rql7@cornelius.db.elephantsql.com/gzabjmhg",
        "default": "postgres://user:1234@localhost:5432/pizza",
        # "adminDB": "postgres://ilya:1234@localhost:55001",
    },
    "apps": {
        "models": {
            "models": ["app.users.models", "app.promocodes.models", "app.products.models", "app.restaurants.models",
                       "app.orders.models",
                       "aerich.models"
                       ],
            "default_connection": "default",
        },
        # "admin": {'models': ['app.restaurants.admin'], 'default_connection': "adminDB"},
    },
    "use_tz": False,
}


def init_db(app: FastAPI) -> None:
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        modules={"models": model_paths,
                 # "adminDB": admin_model_paths
                 },
        generate_schemas=True,
        add_exception_handlers=True,
    )

# Tortoise.init_models(admin_model_paths, "admin")
Tortoise.init_models(model_paths, "models")
