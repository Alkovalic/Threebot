import asyncio
import discord
import math

from time import strftime
from discord.ext import commands
from . import pin_manager


# Cog
class PIN(commands.Cog):

    def __init__(self, bot):
        self._bot = bot
        self._pin_manager = None
        self._pool = None
        self._image_extensions = [".gif", ".jpg", ".jpeg", ".png"]

    # Checks if a file ends with an image extension.
    def is_image(self, filename):
        if filename is None:
            return False
        for ext in self._image_extensions:
            if (filename.lower()).endswith(ext):
                return True
        return False

    # EVENTS #

    # PIN's on_ready waits for the bot's connection pool to initialize before initializing the PinManager.
    @commands.Cog.listener()
    async def on_ready(self):

        if self._pin_manager is None:

            while not self._bot.pool:
                await asyncio.sleep(delay=1, loop=self._bot.loop)

            self._pool = self._bot.pool
            self._pin_manager = pin_manager.PinManager(self._pool, self._bot.output_path)

            # Create tables for any existing guilds if needed.
            for guild in self._bot.guilds:
                await self._pin_manager.add_new_guild_table(guild.id)

    # Create necessary tables for the new guild.
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self._pin_manager.add_new_guild_table(guild.id)

    # Remove necessary tables for the new guild.
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await self._pin_manager.remove_guild_table(guild.id)

    # PIN's on_message reads every command sent to the bot,
    #  and checks if the command is found in the list of pins.
    # If it is found, return the value or path associated with it,
    #  unless it is a sound file. (Filename ends with certain extensions.)
    # Ignores calls to actual commands.
    @commands.Cog.listener()
    async def on_message(self, message):

        if message.content.startswith(self._bot.command_prefix):

            # Remove the command prefix, and get the first word sent.
            cmd = message.content.lstrip(self._bot.command_prefix)

            file_flag = False
            if cmd.endswith("-f"):
                file_flag = True
                cmd = cmd.rstrip("-f").rstrip()

            # Handle empty case.
            if not cmd:
                return
            
            # Ignore all built-in commands.
            for i in self._bot.commands:
                if cmd == i.name:
                    return
            
            # Look up the name in the list of pins.
            result = await self._pin_manager.get_entry(cmd, message.guild.id)

            # If result is None, no entry was found, so we ignore the request.
            if not result:
                return

            # If result is a discord.File object, check if it is an audio file, 
            #  and ignore it if it is.
            if isinstance(result, discord.File):
                for ext in self._pin_manager._sound_extensions:
                    if (result.filename.endswith(ext) and message.author.voice and not file_flag):
                        return
                return await message.channel.send(file=result)

            # At this point, the pin was associated with a string, so return the string.
            # Do nothing if the pin is being played by sound.
            # TODO fix this after updating how the database calls work.
            is_yt = "youtu.be" in result.lower() or "youtube.com" in result.lower() and len(result.split()) == 1
            if is_yt and message.author.voice and not file_flag:
                return
            return await message.channel.send(result)


    @commands.command(name="pin",
                 help="Adds a <name>:<data> association to the list of pins.\n"
                      "If no <data> is passed, the user has 20 seconds to upload a file to associate with the name.\n"
                      "  Notes:  If the file is larger than 8 MB, it will not be added to the list of pins.\n"
                      "          If the file already exists, the <name> for the existing file will be returned, "
                      "and the association will not be made.\n"
                      "          Adding a sound file to the list of pins will add it to the soundboard.",
                 brief="- Pins a message or file.")
    async def pin(self, ctx, name, *, data=None):\

        if not name:
            return await self._bot.send_timed_msg(ctx, "No name provided!")

        for cmd in self._bot.commands:
            if name == cmd.name:
                return await self._bot.send_timed_msg(ctx, "Name provided is a built-in command!")

        if len(name) > 25:
            return self._bot.send_timed_msg(ctx, "Length of pin name must be 25 characters or less!")
        
        value = data
        
        # Handle case where no data entry was passed.
        if not data:

            # Begin seeking for a file.
            req_msg = await ctx.send(f"Please upload a file, {ctx.author.name}.")

            # A lot of this is straight from the discord.py documentation.
            
            # check returns whether a message has attachments, and the attachment is less than 8mb.
            def check(m):
                return bool(m.attachments) and (m.attachments[0].size < 8000000)
            msg = None
            try:  # Wait for a message with an attachment.
                msg = await self._bot.wait_for('message', check=check, timeout=20.0)
            except asyncio.TimeoutError:  # 20 seconds has passed without a valid file sent.
                await req_msg.delete()
                return await self._bot.send_timed_msg(ctx, "File not found, or file was too big!")
            # A valid file has been sent at this point.
            value = msg.attachments[0]
            await req_msg.delete()
        
        try:
            await self._pin_manager.add_entry(name, ctx.author.id, ctx.guild.id, value)
            await self._bot.send_timed_msg(ctx, f'Entry "{name}" added!')
        except ValueError as v:  # Entry failed due to an invalid value being passed.
            await self._bot.send_timed_msg(ctx, v.args[0])
        except FileExistsError as f:  # Entry failed due to an association or file already existing.
            await self._bot.send_timed_msg(ctx, f'Entry "{f.args[0]}" already exists!')
            

    @commands.command(name="unpin",
                 help="Removes a <name>:<data> association from the list of pins.\n"
                      "The author must either be the creator of the association, "
                      "or must have an administrative role.\n"
                      "Returns the data after removing the association.",
                 brief="- Removes a pin.")
    async def unpin(self, ctx, *, name=None):

        if not name:
            return await self._bot.send_timed_msg(ctx, "No name provided!")

        # Check if the author is allowed to remove the entry.
        override = False
        if ctx.author.guild_permissions.administrator or ctx.author == ctx.guild.owner:

            override = True
        
        # Get the entry before removing it.
        # If the entry is None, no such entry exists, so error out the request.
        try:
            entry = await self._pin_manager.get_entry(name, ctx.guild.id)
            if entry is None:
                return await self._bot.send_timed_msg(ctx, f"Entry {name} does not exist!")
            if isinstance(entry, discord.File):
                await ctx.send(file=entry)
                entry.fp.close()
            else:
                await ctx.send(entry)
        except ValueError as v:
            return await self._bot.send_timed_msg(ctx, v.args[0])

        # Attempt to remove the entry.
        try:
            removal = await self._pin_manager.remove_entry(name, ctx.author.id, ctx.guild.id, override=override)
        except PermissionError as e:  # User not allowed to remove the entry.
            owner = ctx.guild.get_member(e.args[0])
            return await self._bot.send_timed_msg(ctx, f"You are unauthorized to remove entry created by {owner}!")
        except ValueError as v:  # Redundancy, should not be reached under normal circumstances.
            return await self._bot.send_timed_msg(ctx, v.args[0])

        # Should not happen, but here just in case.
        if not removal:
            entry.close()
            return await self._bot.send_timed_msg(ctx, f"Unable to remove entry {name}!")

        # Removal successful.
        await self._bot.send_timed_msg(ctx, f"Entry {name} removed successfully.")

    @commands.command(name="list",
                help="Finds pins similar to a given search term."
                     "If the term is a single letter, returns all pins that start with that letter.",
                brief="- Searches pins.")
    async def pins(self, ctx, page=1, name=None):

        # Get a list of similar entries from the database.
        results = await self._pin_manager.search_entries(name, ctx.guild.id)

        # No results found.
        if not results:  # Quality wording.
            if name is None:
                return await self._bot.send_timed_msg(ctx, f"No entries found.")
            elif len(name) == 1:
                return await self._bot.send_timed_msg(ctx, f"No entries starting with {name} found.")
            return await self._bot.send_timed_msg(ctx, f"No entries similar to {name} found.")

        # Create a formatted list of results, cutting off the list if more than list_length results are found.

        list_length = 20
        max_pages = math.ceil(len(results) / list_length)
        if page > max_pages:
            page = max_pages

        if name is None:
            msg = f'Results for all pinned entries (Page {page}/{max_pages}):\n\n'
        else:
            msg = f'Results for search term "{name}" (Page {page}/{max_pages}):\n\n'

        # Calculating the indices of the first and last entry to display.
        start = list_length * (page - 1)
        end = (list_length * page) - 1

        # Populate the list with entries based off of the start and end indices.
        while start <= end and start < len(results):
            msg += f"\t{results[start]}\n"
            start += 1

        return await ctx.send(f"```\n{msg}```")


    @commands.command(name="info",
                help="Gets information about a given pin.\n"
                     "Return the file associated with it, no matter what type.",
                brief="- Pin details.")
    async def info(self, ctx, *, name=None):

        if name is None:
            return await self._bot.send_timed_msg(ctx, "No entry provided!")

        result = await self._pin_manager.get_entry_details(name, ctx.guild.id)

        if result is None:
            return await self._bot.send_timed_msg(ctx, "Entry not found!")

        # Get the author's discord.Member representation, and gather info from it.
        # Also prepare the info from result for the embed.
        author = ctx.guild.get_member(int(result[0].authorid))
        author_name = author.display_name
        author_avatar = author.avatar_url

        date = strftime("%B %d, %Y")
        pin_name = result[0].name
        pin_value = result[0].value
        if pin_value is None and not self.is_image(result[1].filename):
            pin_value = "User upload."
        
        embed=discord.Embed(title=pin_name, description=pin_value, color=0xfffc00)
        embed.set_author(name=author_name,icon_url=author_avatar)
        embed.set_footer(text=date)
        if pin_value is None and self.is_image(result[1].filename):
            embed.set_image(url=f'attachment://{result[1].filename}')
        await ctx.send(embed=embed)
        if (result[1]):
            return await ctx.send(file=result[1])

def setup(bot):
    bot.add_cog(PIN(bot))
