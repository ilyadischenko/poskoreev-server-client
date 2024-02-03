from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "restaurants" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "open" TIMETZ NOT NULL,
    "close" TIMETZ NOT NULL,
    "delivery" BOOL NOT NULL  DEFAULT True,
    "pickup" BOOL NOT NULL  DEFAULT False,
    "inside" BOOL NOT NULL  DEFAULT False,
    "is_work" BOOL NOT NULL  DEFAULT True,
    "city" VARCHAR(255)   DEFAULT 'Орёл',
    "timezone" VARCHAR(255) NOT NULL,
    "min_sum" INT NOT NULL  DEFAULT 0,
    "addres_id" INT REFERENCES "address" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "restaurants";"""
