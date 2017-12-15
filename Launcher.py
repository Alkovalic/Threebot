import discord
from bot_commands import *
from Threebot import Threebot

init_cog = ["ping", "rng"]

bot = Threebot(cogs=init_cog,
               command_prefix="::",
               description="A bot with various utilities, not unlike a slightly dull Swiss Army knife.",
               pm_help=True,
               help_attrs={"hidden": True,
                           "help": "https://suicidepreventionlifeline.org/"})

with open("token.txt", 'r') as get_token:
    token = get_token.read()

bot.run(token)