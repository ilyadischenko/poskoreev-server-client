from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255),
    "birthday" DATE,
    "email" VARCHAR(255)  UNIQUE,
    "number" VARCHAR(255) NOT NULL UNIQUE,
    "code" VARCHAR(255) NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "telegram" VARCHAR(255)  UNIQUE,
    "bonuses" INT NOT NULL  DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "userblacklist" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "user_id" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "userjwt" (
    "refresh_code" VARCHAR(255) NOT NULL,
    "is_active" BOOL NOT NULL,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_userjwt_user_id_af14a7" ON "userjwt" ("user_id");
CREATE TABLE IF NOT EXISTS "promocodepercent" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "short_name" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255),
    "count" INT,
    "for_all" BOOL NOT NULL  DEFAULT False,
    "discount" DECIMAL(4,2) NOT NULL  DEFAULT 0,
    "start_day" TIMESTAMPTZ NOT NULL,
    "end_day" DATE NOT NULL,
    "min_sum" INT,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE TABLE IF NOT EXISTS "products" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "description" VARCHAR(255),
    "img" VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS "productscategories" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(255) NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "menu" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "price" INT NOT NULL,
    "quantity" INT NOT NULL,
    "size" INT NOT NULL  DEFAULT 0,
    "bonuses" INT NOT NULL  DEFAULT 0,
    "is_view" BOOL NOT NULL  DEFAULT True,
    "is_have" BOOL NOT NULL  DEFAULT True,
    "categories_id" INT NOT NULL REFERENCES "productscategories" ("id") ON DELETE CASCADE,
    "product_id" INT NOT NULL REFERENCES "products" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "user_promocodepercent" (
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE,
    "promocodepercent_id" INT NOT NULL REFERENCES "promocodepercent" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
