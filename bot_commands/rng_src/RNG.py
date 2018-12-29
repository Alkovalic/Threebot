from discord.ext import commands
from bot_commands.rng_src import dice
from bot_commands.rng_src import random_boo_generator

import discord
import random
import asyncio


class RNG:  # Cog

    """ Cog responsible for handling commands related to random number generation.
    """

    def __init__(self, bot):
        self._bot = bot
        self._pool = None  # Database pool from the bot.
        self._boo_generator = random_boo_generator.RandomBooGenerator()
        self._defaults = None
        self._table = "default_dice"
        self._initial_dice = "3d6"  # Default rolls for a newly added entry for a guild.

    # Creates a dictionary of default rolls for each server.
    # Using this to save database queries when getting a default roll.
    async def _init_defaults(self):

        result = {}

        # For each guild the bot is part of, check their database table for an RNG entry.
        async with self._pool.acquire() as conn:
            cur = await conn.cursor()
            for guild in self._bot.guilds:
                await cur.execute(f"SELECT dice FROM {self._table} WHERE guild=(?)", guild.id)
                result[guild.id] = (await cur.fetchone())[0]
            await cur.close()
            await conn.close()

        self._defaults = result

    # Adds a default roll entry to the RNG table for the given guild.
    # Returns True if the entry is successfully added, and False if the entry already exists.
    async def _add_guild_entry(self, guild_id):

        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                
                # First, check if the guild is already in the database.
                await c.execute(rf"SELECT * FROM {self._table} WHERE guild=(?)", guild_id)
                if await c.fetchone():
                    return False
        
                # If it isn't, create a new entry for the guild.
                values = (guild_id, self._initial_dice)
                await c.execute(rf"INSERT INTO {self._table} (guild, dice) VALUES (?, ?)", values)
                await c.commit()
                return True

    # Removes the entry for the given guild from the RNG table.
    async def _remove_guild_entry(self, guild_id):
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                await c.execute(rf"DELETE FROM {self._table} WHERE guild=(?)", guild_id)

    # Initialize defaults when the bot is ready.
    async def on_ready(self):

        if not self._pool is None:
            return

        # Wait for the pool to be ready.
        while not self._bot.pool:
            await asyncio.sleep(delay=1, loop=self._bot.loop)

        # Assign pool, create table if necessary, pull default rolls from the database.
        self._pool = self._bot.pool

        # Checking if the table exists, and make one if it doesn't.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                check = await c.tables(table=self._table, tableType='TABLE')
                if not check.fetchone():
                    execute_input = rf"CREATE TABLE {self._table} (guild TEXT, dice TEXT)"
                    await c.execute(execute_input)
                    await c.commit()

        # Add entries for every guild the bot is part of, if one doesn't already exist.
        for guild in self._bot.guilds:
            await self._add_guild_entry(guild.id)

        await self._init_defaults()

    # Create a new entry for the newly joined guild.
    async def on_guild_join(self, guild):
        await self._add_guild_entry(guild.id)

    # Remove the entry for the removed guild.
    async def on_guild_remove(self, guild):
        await self._remove_guild_entry(guild.id)

    # The main group for RNG commands.
    # Calling this command without an argument flips a coin,
    #  otherwise, it will execute a subcommand, if one exists.
    @commands.command(name = 'flip',
                help="Flips a coin, returning heads/tails and a number between 1-100.",
                brief=" - Coin flip.")
    async def flip(self, ctx):

        if ctx.invoked_subcommand is None:
            result = random.randint(1, 100)
            response = f"{ctx.author.display_name}'s coin landed {'Heads' if result%2==True else 'Tails'} ({result})!"
            await ctx.send(response)

    # Roll subcommand from RNG.
    # Responsible for handling dice rolls,
    #  as well as managing a default roll for easy use.
    @commands.command(name='roll',
                 help="Rolls a dice in ndn format.\n"
                      "Rolls the default setting if no arguments are passed.\n"
                      "Usage:\n"
                      "  default <n>d<n> -> Sets the default roll.\n"
                      "  <n>d<n> -> Rolls a dice in <dice>d<faces> format",
                 brief="- Dice roller.")
    async def roll(self, ctx, arg=None, arg2=None):

        # No arguments passed.
        if arg is None:
            return await ctx.send(dice.roll_string(ctx.author.name, self._defaults[ctx.guild.id]))

        # First argument is "default"
        elif arg == "default":  # At least one argument passed.

            # Only argument "default" is passed.
            if arg2 is None:
                return await ctx.send(f"Current default roll:  {self._defaults[ctx.guild.id]}")

            # Second argument must be what user wants the server default to become.
            # Second argument should be in format <n>d<f>
            if not dice.is_valid_roll(arg2):
                return await ctx.send(f"Argument {arg2} invalid! "
                                      "Format must be ndn, and result cannot potentially exceed 2000 characters.")

            # Modify default roll table, and update database.
            self._defaults[ctx.guild.id] = arg2

            # Could potentially make a function in DatabaseManager to handle value updating,
            #  but worried that it could lead to certain values being updated when they shouldn't be.
            async with self._pool.acquire() as conn:
                async with conn.cursor() as c:
                    await c.execute(f"UPDATE {self._table} SET dice=(?) WHERE guild=(?)", arg2, ctx.guild.id)
                    await c.commit()

            return await ctx.send(f"Default roll has been set to {arg2}!")
        # One argument passed.
        else:
            if not dice.is_valid_roll(arg):
                return await ctx.send(f"Argument {arg} invalid! Format must be ndn, *n* must be non-zero, "
                                      "and result cannot potentially exceed 2000 characters.")
            return await ctx.send(dice.roll_string(ctx.author.name, arg))

    # Choose subcommand from RNG.
    # Responsible for choosing a random element from a list of arguments.
    @commands.command(name='choose',
                 help="Chooses one item out of a list of arguments.\n"
                      "Arguments can be combined by wrapping them in quotes.",
                 brief="- Choice selection.")
    async def choose(self, ctx, *args):

        # Check for empty and pure whitespace strings.
        result = random.choice(args)
        if result.isspace() or not result:
            return await ctx.send("(None)")
        
        await ctx.send(result)

    # Reorder command from RNG.
    # Responsible for reordering a list of arguments in random order.
    @commands.command(name='reorder',
                 help="Takes a list of arguments, and returns a permutation of it.\n"
                      "Arguments can be combined by wrapping them in quotes.",
                 brief="- List reordering.")
    async def reorder(self, ctx, *args):
        stuff = list(args)
        random.shuffle(stuff)
        result = "```"

        for i in range(len(stuff)):
            result += str(i+1) + ".  " + stuff[i] + "\n"

        await ctx.send(result+" ```")

    # Boo command from RNG.
    # Responsible for returning a random Boo.
    @commands.command(name='boo',
                 help="Returns a random boo.\n"
                      "Current boo table:\n"
                      "  Regular boo: 49%\n"
                      "  Magic boo: 25%\n"
                      "  King boo: 15%\n"
                      "  Pink Gay Boo: 10%\n"
                      "  Rainbow Boo: 1%\n",
                 brief="- Boo retrieval.")
    async def random_boo(self, ctx):

        # Select a random Boo.
        selected_boo = self._boo_generator.get_random_boo()

        # If None is returned, something went wrong, so log it to the console, and send a default message to the user.
        if selected_boo is None:
            print("RNG Boo generator returned None:  maybe an image hasn't been hooked up in the Boo generator?")
            return await ctx.send("Luigi, what the hell?  You told me there were GHOSTS in here!")

        # At this point, a path has been returned, and we're ready to deliver the Boo.
        with open(selected_boo, "rb") as image:
            return await ctx.send(file=discord.File(image))


def setup(bot):
    bot.add_cog(RNG(bot))
