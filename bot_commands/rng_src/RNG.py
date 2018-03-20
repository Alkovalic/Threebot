from discord.ext import commands
from . import dice
from . import random_boo_generator

import discord
import random
import asyncio


class RNG:  # Cog

    """ Cog responsible for handling commands related to random number generation.
        WARNING:  If the RNG type is ever used for more than one thing, dice roll
                  defaults must be modified to update select entries.
    """

    def __init__(self, bot):
        self._bot = bot
        self._pool = None  # Database pool from the bot.
        self._boo_generator = random_boo_generator.RandomBooGenerator()
        self._defaults = None

    # Creates a dictionary of default rolls for each server.
    # Using this to save database queries when getting a default roll.
    async def __init_defaults(self):

        result = {}

        # For each guild the bot is part of, check their database table for an RNG entry.
        async with self._pool.acquire() as conn:
            cur = await conn.cursor()
            for guild in self._bot.guilds:
                table = self._bot.get_table_name(guild.id)
                await cur.execute(f"SELECT type, value FROM {table} WHERE type='RNG'")
                result[guild.id] = (await cur.fetchone())[1]
            await cur.close()
            await conn.close()

        self._defaults = result

    # Changes a default value for a server.
    def __change_default(self, server, arg):
        pass

    # Initialize defaults when the bot is ready.
    async def on_ready(self):

        # Wait for the pool to be ready.
        while not self._bot.pool:
            await asyncio.sleep(delay=1, loop=self._bot.loop)

        # Assign pool, initialize default rolls.
        self._pool = self._bot.pool
        await self.__init_defaults()

    # The main group for RNG commands.
    # Calling this command without an argument flips a coin,
    #  otherwise, it will execute a subcommand, if one exists.
    @commands.group(help="RNG command with various methods.\n"
                         "Flips a coin if no arguments are passed.",
                    brief="- Collection of RNG related commands.")
    async def rng(self, ctx):

        if ctx.invoked_subcommand is None:
            result = random.randint(1, 100)
            response = f"{ctx.author.display_name}'s coin landed {'Heads' if result%2==True else 'Tails'} ({result})!"
            await ctx.send(response)

    # Roll subcommand from RNG.
    # Responsible for handling dice rolls,
    #  as well as managing a default roll for easy use.
    @rng.command(name='roll',
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

            async with self._pool.acquire() as conn:
                cur = await conn.cursor()
                table = self._bot.get_table_name(ctx.guild.id)
                await cur.execute(f"UPDATE {table} SET value=(?) WHERE type='RNG'", arg2)
                await cur.commit()
                await cur.close()
                await conn.close()

            return await ctx.send(f"Default roll has been set to {arg2}!")
        # One argument passed.
        else:
            if not dice.is_valid_roll(arg):
                return await ctx.send(f"Argument {arg} invalid! Format must be ndn, *n* must be non-zero, "
                                      "and result cannot potentially exceed 2000 characters.")
            return await ctx.send(dice.roll_string(ctx.author.name, arg))

    # Choose subcommand from RNG.
    # Responsible for choosing a random element from a list of arguments.
    @rng.command(name='choose',
                 help="Chooses one item out of a list of arguments.\n"
                      "Arguments can be combined by wrapping them in quotes.",
                 brief="- Choice selection.")
    async def choose(self, ctx, *args):
        await ctx.send(random.choice(args))

    # Reorder command from RNG.
    # Responsible for reordering a list of arguments in random order.
    @rng.command(name='reorder',
                 help="Takes a list of arguments, and returns a permutation of it.\n"
                      "Arguments can be combined by wrapping them in quotes.",
                 brief="- List reordering.")
    async def reorder(self, ctx, *args):
        stuff = list(args)
        random.shuffle(stuff)
        result = "```"

        for i in range(len(stuff)):
            result += str(i+1) + ".  " + stuff[i] + "\n"

        await ctx.send(result+"```")

    # Boo command from RNG.
    # Responsible for returning a random Boo.
    @rng.command(name='boo',
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

        # If None is returned, something went wrong, so tell the user just that.
        if selected_boo is None:
            return await ctx.send("Luigi, what the hell?  You told me there were GHOSTS in here!")

        # At this point, a path has been returned, and we're ready to deliver the Boo.
        with open(selected_boo, "rb") as image:
            return await ctx.send(file=discord.File(image))


def setup(bot):
    bot.add_cog(RNG(bot))
