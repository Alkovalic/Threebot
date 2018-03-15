from Threebot import Threebot

init_cog = ["bot_commands.ping", "bot_commands.rng_src.rng", "bot_commands.arc_src.arc"]

db_args = {"DRIVER": "SQLite3 ODBC Driver",
           "DATABASE": "threebot.db"}

bot = Threebot(cogs=init_cog,
               db_args=db_args,
               command_prefix="::",
               description="A bot with various utilities.",
               pm_help=True,
               help_attrs={"hidden": True,
                           "help": "https://suicidepreventionlifeline.org/"})

with open("token.txt", 'r') as get_token:
    token = get_token.read()

bot.run(token)
