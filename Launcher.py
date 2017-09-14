import ThreePi
import Command
import ThreebotCommands
import sys
import os
import asyncio

import websockets.exceptions

# COMMANDS #

cmd_dict = {}

for cls in Command.Command.__subclasses__():
    cmd = cls()
    cmd_dict[cmd.__module__.split(".")[-1]] = cmd

# SETTINGS #

p = os.path.dirname(__file__)

bot_args = {
            "default_sounds": p + "/default_sounds/",
            "default_misc": p + "/default_misc/",
            "config": p + "/ThreeConfig/",
            "server_data": p + "/ServerData/",
           }

# BOT + COMMAND SETTINGS #

bot = ThreePi.ThreePi(bot_args, cmd_dict)

cmd_dict["help"].set_cmd_dict(cmd_dict)
cmd_dict["player"].initialize(cmd_dict, "/mnt/banana/")

loop = asyncio.get_event_loop()

# MY MAIN MAN #


def main(lp):

    lp.run_until_complete(bot.CANNON_ENGAGED())

a = 0

while 1:

    try:
        main(loop)
    except RuntimeError as e:  # Catches closed event loops ..?
        if a <= 2:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            a += 1
        else:
            raise e

