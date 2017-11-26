import discord
from bot_commands import *
from Threebot import Threebot

init_cog = ["ping", "rng"]

bot = Threebot(cogs=init_cog, command_prefix="::", description="Threebot rewrite.", pm_help=True,)

with open("token.txt", 'r') as get_token:
    token = get_token.read()

bot.run(token)