import ThreePi
import Command
import ThreebotCommands
import sys
import os

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

# MY MAIN MAN #

def main():

    bot.CANNON_ENGAGED()

main()
