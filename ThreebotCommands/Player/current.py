import Command
import youtube_dl
import discord


class CURRENT(Command.Command):

    def __init__(self):
        self.__player_object = None

    def set_player_obj(self, obj):
        self.__player_object = obj

    def info(self):
        return "player"

    async def run(self, client, message):

        server = client.get_server_data(message)
        video_data = self.__player_object.get_current_song(server)

        if video_data is None:
            return await client.send_message(message.channel, "No song currently playing.")

        # return await client.send_message(message.channel, "Current song:  " + video_data.get_url())

        with youtube_dl.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(video_data.get_url(), download=False)

            embed = discord.Embed(title=info["title"], url=info['webpage_url'], description=info["duration"])
            embed.set_author(name="Currently playing:")
            embed.set_thumbnail(url=info["thumbnail"])

            return await client.send_message(message.channel, embed=embed)

