from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "address" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "adress" VARCHAR(255) NOT NULL,
    "is_work" BOOL NOT NULL  DEFAULT False,
    "min_sum" INT NOT NULL  DEFAULT 0
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "address";"""
