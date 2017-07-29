# Ping.py

import Command
import time


class PING(Command.Command):

    def info(self):
        name = "ping"
        desc = ("Returns pong.\n"
                "Format:  ping\n")
        return name, desc

    async def run(self, client, message):
        if time.localtime()[4] == 33:
            return await client.send_file(message.channel, "default_misc/mmm.jpg")
        return await client.send_message(message.channel, "Pong")
