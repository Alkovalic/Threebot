import asyncio
import discord

from discord.ext import commands
from . import pin_manager


# Cog
class PIN:

    def __init__(self, bot):
        self._bot = bot
        self._pin_manager = None

    async def on_ready(self):

        while not self._bot.pool:
            await asyncio.sleep(delay=1, loop=self._bot.loop)

        self._pin_manager = pin_manager.PinManager(self._bot)
    

    @commands.command(name="pin",
                 help="Adds a <name>:<data> association to the list of pins.\n"
                      "If no <data> is passed, the user has 20 seconds to upload a file to associate with the name.\n"
                      "  Notes:  If the file is larger than 8 MB, it will not be added to the list of pins.\n"
                      "          If the file already exists, the <name> for the existing file will be returned, "
                      "and the association will not be made.\n"
                      "          Adding a sound file to the list of pins will add it to the soundboard.",
                 brief="- Pins a message or file.")
    async def pin(self, ctx, name, data=None):\

        if not name:

            return await ctx.send("No name provided!")

        value = data
        
        # Handle case where no data entry was passed.
        if not data:

            # Begin seeking for a file.
            await ctx.send(f"Please upload a file, {ctx.author.name}.")

            # A lot of this is straight from the documentation, so thanks, Danny.
            
            # check returns whether a message has attachments, and the attachment is less than 8mb.
            def check(m):
                return bool(m.attachments) and (m.attachments[0].size < 8000000)

            msg = None
            try:  # Wait for a message with an attachment.
                msg = await self._bot.wait_for('message', check=check, timeout=20.0)
            except asyncio.TimeoutError:  # 20 seconds has passed without a valid file sent.
                return await ctx.send("File not found, or file was too big!")
            # A valid file has been sent at this point.
            value = msg.attachments[0]
        
        try:
            await self._pin_manager.add_entry(name, ctx.author.id, ctx.guild.id, value)
            return await ctx.send(f'Entry "{name}" added!')
        except ValueError as v:  # Entry failed due to an invalid value being passed.
            return await ctx.send(v.args[0])
        except FileExistsError as f:  # Entry failed due to an association or file already existing.
            return await ctx.send(f'Entry "{f.args[0]}" already exists!')


    @commands.command(name="unpin",
                 help="Removes a <name>:<data> association from the list of pins.\n"
                      "The author must either be the creator of the association, "
                      "or must have an administrative role.\n"
                      "Returns the data after removing the association.",
                 brief="- Removes a pin.")
    async def unpin(self, ctx, name=None):

        if not name:
            return await ctx.send("No name provided!")

        # Check if the author is allowed to remove the entry.
        override = False
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner:

            override = True
        
        # Attempt to remove the entry.
        try:
            res = await self._pin_manager.remove_entry(name, ctx.author.id, ctx.guild.id, override=override)
        except PermissionError as e:  # User not allowed to remove the entry.
            owner = ctx.guild.get_member(e.args[0])
            return await ctx.send(f"You are unauthorized to remove entry created by {owner}!")
        except ValueError as v:  # User attempted to remove a blank entry.
            return await ctx.send(v.args[0])

        # Check if removal is successful, and return the removed item if this is the case.
        if res is None:
            return await ctx.send(f"Entry '{name}' does not exist!")

        # Removal successful.
        await ctx.send(f"Entry {name} removed successfully:")
        if isinstance(res, discord.File):
            await ctx.send(file=res)
            res.close()
        else:
            await ctx.send(res)


    @commands.command(name="search",
                help="Finds pins similar to a given search term."
                     "If the term is a single letter, returns all pins that start with that letter.",
                     brief="- Searches pins.")
    async def search(self, ctx, name=None):
        
        if not name:
            return await ctx.send("No search term provided!")

        # Get a list of similar entries from the database.
        results = await self._pin_manager.search_entries(name, ctx.guild.id)

        # No results found.
        if not results:  # Quality wording.
            if len(name) == 1:
                return await ctx.send(f"No entries starting with {name} found.")
            return await ctx.send(f"No entries similar to {name} found.")

        # Create a formatted list of results, cutting off the list if more than 20 results are found.

        msg = f'Results for search term "{name}":\n'
        ptr = 0
        for i in results:
            if ptr > 20:
                msg += f"... ({len(results)-ptr} more)\n"
                break
            else:
                msg += f"{i}\n"
                ptr += 1

        return await ctx.send(f"```\n{msg}```")


def setup(bot):
    bot.add_cog(PIN(bot))
