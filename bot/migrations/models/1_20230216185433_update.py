from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_quake3serve_discord_34d90e";
        CREATE TABLE IF NOT EXISTS "commandexecution" (
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(32) NOT NULL,
    "discord_channel_id" BIGINT NOT NULL,
    "discord_guild_id" BIGINT NOT NULL REFERENCES "discordguild" ("id") ON DELETE CASCADE,
    "discord_user_id" BIGINT NOT NULL REFERENCES "discorduser" ("id") ON DELETE CASCADE
);;
        CREATE  INDEX "idx_quake3serve_address_898bca" ON "quake3server" ("address", "discord_guild_id");;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_quake3serve_address_898bca";
        DROP TABLE IF EXISTS "commandexecution";
        CREATE  INDEX "idx_quake3serve_discord_34d90e" ON "quake3server" ("discord_guild_id", "address");;"""
