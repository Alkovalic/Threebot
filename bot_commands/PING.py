from discord.ext import commands


class Ping(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Returns pong.",
                      brief="- Returns pong.")
    async def ping(self, ctx):
        return await ctx.send("pong")


def setup(bot):
    bot.add_cog(Ping(bot))
    