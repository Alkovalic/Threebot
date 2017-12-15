from discord.ext import commands

import discord
import random
import os


class Dice:  # Helper class

    def __init__(self, amount, faces):
        self._amount = amount
        self._faces = faces

    def __repr__(self):
        return f"{self._amount}d{self._faces}"

    def __roll(self, amount=None, faces=None):
        results = []

        if amount is None or faces is None:
            amount = self._amount
            faces = self._faces

        for i in range(amount):
            results.append(random.randint(1,faces))

        return results

    def roll_self(self):
        return self.__roll()

    @classmethod
    def roll_args(cls, amount, faces):
        return cls.__roll(cls, amount, faces)  # This gives a warning, but it works.  Not sure what the issue is.


class RNG:  # Cog

    def __init__(self, bot, guilds):
        self._bot = bot
        self._guilds = guilds
        boo_dir = os.getcwd() + "\\boo"

        if os.path.isdir(boo_dir):
            self._boo_dir = boo_dir
            self._boo_dict = {
                "boo": 49,
                "kingboo": 15,
                "magicboo": 25,
                "pinkgayboo": 10,
                "rainbowboo": 1
            }
            self._boo_table = list()
            for key in self._boo_dict:
                self._boo_table += [key] * (self._boo_dict[key])
        else:
            print("boo directory not found!")
            self._boo_dir = None
            self._boo_dict = None

    @commands.group(help="RNG command with various methods.\nFlips a coin if no arguments are passed.",
                    brief="- Collection of RNG related commands.")
    async def rng(self, ctx):

        if ctx.invoked_subcommand is None:
            result = random.randint(1,100)
            response = f"{ctx.author.display_name}'s coin landed {'Heads' if result%2==True else 'Tails'} ({result})!"
            await ctx.send(response)

    @rng.command(name='roll',
                 help="Rolls a dice in ndn format.\nRolls the default setting if no arguments are passed.\n"
                      "Usage:\n"
                      "  default <n>d<n> -> Sets the default roll.\n"
                      "  <n>d<n> -> Rolls a dice in <dice>d<faces> format",
                 brief="- Dice roller.")
    async def roll(self, ctx, arg=None, arg2=None):

        current_guild = self._guilds[ctx.guild.id]

        if arg is None:  # No arguments passed
            res = current_guild._default_roll.roll_self()

        elif arg == "default":  # At least one argument passed
            if arg2 is None:
                return await ctx.send(f"Current default roll:  {current_guild._default_roll}")  # One argument passed

            # Second argument must be what user wants default to be
            arg2 = arg2.lower()
            try:
                amount, faces = arg2.split("d")
            except ValueError:
                return await ctx.send("Roll must be in ndn format!")
            current_guild._default_roll = Dice(int(amount), int(faces))
            response = f"{ctx.author.display_name} has changed the default roll to {current_guild._default_roll}!"

            return await ctx.send(response)

        else: # One argument passed
            arg = arg.lower()
            try:
                amount, faces = arg.split("d")
            except ValueError:
                return await ctx.send("Roll must be in ndn format!")
            res = Dice.roll_args(int(amount), int(faces))

        await ctx.send(f"{ctx.author.display_name} rolled {res}! (Sum:  {sum(res)})")

    @rng.command(name='choose',
                 help="Chooses one item out of a list of arguments.\n"
                      "Arguments can be combined by wrapping them in quotes.",
                 brief="- Choice selection.")
    async def choose(self, ctx, *args):
        await ctx.send(random.choice(args))

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
        if self._boo_dir is not None:

            boo = random.choice(self._boo_table)

            for i in os.listdir(self._boo_dir):
                if i.startswith(boo):
                    with open(f"{self._boo_dir}\\{i}", "rb") as image:
                        return await ctx.send(file=discord.File(image))

            # From this point on, the file was not found, and we can't return our boo.
            return await ctx.send(f"Sadly, our boos aren't properly configured.  "
                                  "You WOULD have gotten {boo}")
        else:
            return await ctx.send("Sadly, our boos aren't properly configured.")


def setup(bot):
    bot.add_cog(RNG(bot, bot._guild_data))
