from discord.ext import commands


class Ping:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        return await ctx.send("pong")


def setup(bot):
    bot.add_cog(Ping(bot))
