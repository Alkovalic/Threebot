import Command
import discord
import aiohttp


class TEST(Command.Command):

    async def run(self, client, message):

        client.loop.stop()
        client.loop.close()
