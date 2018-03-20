from discord.ext import commands
import DatabaseManager


class Threebot(commands.Bot):

    def __init__(self, cogs, db_args, **args):
        super().__init__(**args)
        self.db_manager = DatabaseManager.DatabaseManager(db_args, "_{}")
        self.connected = False
        for cog in cogs:
            self.load_extension(cog)

    # Shortcut for accessing the database connection pool.
    @property
    def pool(self):
        return self.db_manager.pool

    # Shortcut for accessing a guild's table name.
    def get_table_name(self, guild_id):
        return self.db_manager.get_table_name(guild_id)

    # EVENTS #

    # Create necessary tables for the new guild.
    async def on_guild_join(self, guild):
        async with self.pool.acquire() as conn:
            await self.db_manager.add_new_guild_table(guild.id, conn)
            await conn.close()

    # Remove necessary tables for the new guild.
    async def on_guild_remove(self, guild):
        async with self.pool.acquire() as conn:
            await self.db_manager.remove_guild_table(guild.id, conn)
            await conn.close()

    # Loads components on connect, while doing nothing on reconnect.
    async def on_ready(self):

        print("Connecting..")

        # Bot has already connected at least once.
        if self.connected:
            print("Reconnected!")

        else:
            # Connect to database server.
            await self.db_manager.init_db(self.loop)

            # Initialize guild data.
            async with self.pool.acquire() as conn:
                for guild in self.guilds:
                    await self.db_manager.add_new_guild_table(guild.id, conn)
                await conn.close()

            self.connected = True
            print("Connected!")
