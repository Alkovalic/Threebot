from discord.ext import commands
import DatabaseManager


class Threebot(commands.Bot):

    def __init__(self, cogs, db_args, **args):
        super().__init__(**args)
        self.db_manager = DatabaseManager.DatabaseManager(db_args)
        self.connected = False
        for cog in cogs:
            self.load_extension(cog)

    # Shortcut for accessing the database connection pool.
    @property
    def pool(self):
        return self.db_manager.pool

    # EVENTS #

    # Loads components on connect, while doing nothing on reconnect.
    async def on_ready(self):

        print("Connecting..")

        # Bot has already connected at least once.
        if self.connected:
            print("Reconnected!")

        else:
            # Connect to database server.
            await self.db_manager.init_db(self.loop)

            self.connected = True
            print("Connected!")
