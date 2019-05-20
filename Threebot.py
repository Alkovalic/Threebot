from discord.ext import commands

import asyncio
import DatabaseManager


class Threebot(commands.Bot):

    def __init__(self, cogs, output_path, db_args, **args):
        super().__init__(**args)
        self.db_manager = DatabaseManager.DatabaseManager(db_args, output_path)
        self.connected = False
        self.output_path = output_path
        for cog in cogs:
            self.load_extension(cog)

    # Shortcut for accessing the database connection pool.
    @property
    def pool(self):
        return self.db_manager.pool

    # Method for sending a message that deletes itself after t seconds.
    async def send_timed_msg(self, ctx, msg, time=3):
        msg = await ctx.send(msg)
        await asyncio.sleep(time, loop=self.loop)
        await msg.delete()

    # EVENTS #

    async def on_message(self, message):
        if message.content.startswith("~") and not message.content.startswith("~~"):
            print(f"{message.author}:{message.content}")
            await message.delete()
            await self.process_commands(message)

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
