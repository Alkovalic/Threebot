from discord.ext import commands
from bot_commands.rng_src import dice
from bot_commands.rng_src import random_boo_generator

import discord
import random
import asyncio


class RNG(commands.Cog):  # Cog

    """ Cog responsible for handling commands related to random number generation.
    """

    def __init__(self, bot):
        self._bot = bot
        self._pool = None  # Database pool from the bot.
        self._boo_generator = random_boo_generator.RandomBooGenerator()
        self._dice = dice.Dice(
            "```\n"
            "{author} rolled {input}!\n\n"
            "Result:  {result}\n\n"
            "Sum:  {sum}\n"
            "```"
        )
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
    @commands.Cog.listener()
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
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await self._add_guild_entry(guild.id)

    # Remove the entry for the removed guild.
    @commands.Cog.listener()
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

    # Default roll subcommand for RNG
    # Responsible for changing the default roll of the server it is invoked in.
    @commands.command(name='default_roll',
                 help="Sets the server's default dice roll.\n"
                      "Format must be in mdn or k format, and supports addition or subtraction.\n"
                      "Examples:\n"
                      "  default_roll 3d6 -> Sets the default roll to 3 six sided dice."
                      "  default_roll 1d20+3 -> Sets the default roll to 1 twenty sided dice plus 3.",
                 brief="- Server default dice.")
    async def default_roll(self, ctx, *, arg=None):

        # No arguments passed.
        if arg is None:
            return await ctx.send(f"Current default roll:  {self._defaults[ctx.guild.id]}")

        # Second argument must be what user wants the server default to become.
        # Second argument should be in format <n>d<f>
        if self._dice.max_length(arg) > 2000:
            return await ctx.send(f"Argument invalid! " 
                                   "Format must be in mdn format, and result cannot potentially exceed 2000 characters.")
        
        # Modify default roll table, and update database.
        self._defaults[ctx.guild.id] = arg.replace(" ", "")

        # Updating guild default in the database.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                await c.execute(f"UPDATE {self._table} SET dice=(?) WHERE guild=(?)", arg.replace(" ",""), ctx.guild.id)
                await c.commit()
        
        return await ctx.send(f"Default roll has been set to {arg}!")

    # Roll command for RNG.
    # Responsible for rolling whatever the author gives, or the default roll of the guild if no arg is passed.
    @commands.command(name='roll',
                help="Rolls a given dice roll.\n"
                     "Format must be in mdn or k format, and supports addition or subtraction.\n"
                     "If no argument is provided, rolls the default roll of the guild.\n"
                     "Examples:\n"
                     "  roll 3d6 -> Rolls 3 six sided dice."
                     "  roll 1d20 + 3 -> Rolls 1 twenty sided dice, and adds three to it."
                     "  roll -> Rolls whatever the default dice is set as in the current guild.",
                brief="- Dice roller.") 
    async def roll(self, ctx, *, arg=None):

        # No arguments passed.
        if arg is None:
            return await ctx.send(self._dice.roll_dice(self._defaults[ctx.guild.id], ctx.author.display_name))

        # Check if the argument is formatted properly.
        if self._dice.max_length(arg) > 2000:
            return await ctx.send("Argument invalid! "
                                  "Format must be in mdn format, and result cannot potentially exceed 2000 characters.")

        # At this point, the format is correct, and is ready to be rolled.
        return await ctx.send(self._dice.roll_dice(arg, ctx.author.display_name))    

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
