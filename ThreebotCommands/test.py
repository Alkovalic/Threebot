import Command
import discord


class TEST(Command.Command):

    async def run(self, client, message):

        embed = discord.Embed(title='<video id="sampleMovie" src="HTML5Sample.mov"></video>')

        return await client.send_message(message.channel, embed=embed)