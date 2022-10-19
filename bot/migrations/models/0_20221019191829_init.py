from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "discordguild" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGINT NOT NULL  PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "discorduser" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGINT NOT NULL  PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "quake3server" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "address" VARCHAR(128) NOT NULL,
    "discord_guild_id" BIGINT NOT NULL REFERENCES "discordguild" ("id") ON DELETE CASCADE
);
CREATE  INDEX IF NOT EXISTS "idx_quake3serve_discord_34d90e" ON "quake3server" ("discord_guild_id", "address");
CREATE TABLE IF NOT EXISTS "userquake3serverconfiguration" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "encrypted_password" VARCHAR(128) NOT NULL,
    "discord_user_id" BIGINT NOT NULL REFERENCES "discorduser" ("id") ON DELETE CASCADE,
    "server_id" INT NOT NULL REFERENCES "quake3server" ("id") ON DELETE CASCADE
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
