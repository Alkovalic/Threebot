from discord.ext import commands

import random


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

    @commands.group()
    async def rng(self, ctx):

        if ctx.invoked_subcommand is None:
            result = random.randint(1,100)
            response = f"{ctx.author.display_name}'s coin landed {'Heads' if result%2==True else 'Tails'} ({result})!"
            await ctx.send(response)

    @rng.command(name='roll')
    async def default_roll(self, ctx, arg=None, arg2=None):

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


def setup(bot):
    bot.add_cog(RNG(bot, bot._guild_data))
