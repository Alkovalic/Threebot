import asyncio

from discord.ext import commands
from . import archive


# Cog
class Archive:

    def __init__(self, bot):
        self._bot = bot
        self._arc_manager = None

    async def on_ready(self):

        while not self._bot.pool:
            await asyncio.sleep(delay=1, loop=self._bot.loop)

        self._arc_manager = archive.Archive(self._bot.pool)

    @commands.group(help="Archive system that uses a key -> value layout to access saved items.\n"
                         "Use arc <key> to access a value.",
                    brief="- Archive system.")
    async def arc(self, ctx, name=None):
        if ctx.invoked_subcommand is None:

            # If an argument is passed, get the value associated with the argument
            if name is not None:
                print(f"getting {name}")
                return

            # Otherwise, return usage information.
            return await ctx.send(f"Type {self._bot.command_prefix}help arc for usage.")

    @arc.command(name="add",
                 help="Adds a <name>:<data> association to the archive.\n"
                      "If a message ID is passed as <data>, "
                      "Threebot will attempt to find the message and add it as the content instead.\n"
                      "If no <data> is passed, the user has 20 seconds to upload a file to associate with the name.\n"
                      "  Notes:  If the file is larger than 8 MB, it will not be added to the archive.\n"
                      "          If the file is a text document with 2000 characters or less, "
                      "the text will be saved directly.\n"
                      "          If the file already exists, the <name> will be returned, "
                      "and the association will not be made.\n"
                      "          Adding a sound file to the archive will add it to the soundboard.",
                 brief="- Creating name associations.")
    async def add(self, ctx, name, data=None):
        print(f"adding {name} with data {data}")

    @arc.command(name="rm",
                 help="Removes a <name>:<data> association from the archive.\n"
                      "The author must either be the creator of the association, "
                      "or must have an administrative role.\n"
                      "Returns the data after removing the association.",
                 brief="- Removing name associations.")
    async def rm(self, ctx, name):
        print(f"removing {name}")


def setup(bot):
    bot.add_cog(Archive(bot))
