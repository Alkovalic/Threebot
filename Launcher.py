from Threebot import Threebot

init_cog = ["bot_commands.Ping", "bot_commands.rng.Rng", "bot_commands.pin.Pin", "bot_commands.player.Player"]

db_args = {"DRIVER": "SQLite3 ODBC Driver",
           "DATABASE": "threebot.db"}

output_path = "saved"

bot = Threebot(cogs=init_cog,
               output_path=output_path,
               db_args=db_args,
               command_prefix="~",
               description="A bot with various utilities.",
               pm_help=False,
               help_attrs={"hidden": True,
                           "help": "https://suicidepreventionlifeline.org/"})
try:
    with open("token.txt", 'r') as get_token:
        token = get_token.read()
        print("Running the bot..")

        bot.run(token)

except FileNotFoundError:
    print("Token text file not found!")
