import Command
import asyncio

class PLAY(Command.Command):

    def __init__(self):
        self.__player_object = None

    def set_player_obj(self, obj):
        self.__player_object = obj

    def info(self):
        return "player"

    async def play_next(self, server_data, client_loop):

        voice_client = server_data.get_voice_client()

        if voice_client is None:
            return

        video_data = self.__player_object.dequeue_song(server_data)

        if video_data is None:
            server_data.set_interruptable(True)
            return

        if server_data.is_interruptable():
            server_data.set_interruptable(False)

        path = video_data.get_path()

        def after_song(cmd, data, loop):
            coro = cmd.play_next(data, loop)
            fut = asyncio.run_coroutine_threadsafe(coro, loop)
            fut.result()

        if path is None:
            plr = await voice_client.create_ytdl_player(video_data.get_url(), use_avconv=True, after=lambda:  after_song(self, server_data, client_loop))
        else:
            plr = voice_client.create_ffmpeg_player(path, use_avconv=True, after=lambda:  after_song(self, server_data, client_loop))
        server_data.set_player(plr)
        server_data.get_player().start()

    async def run(self, client, message):

        server = client.get_server_data(message)

        url = None
        try:
            url = message.content.split(" ")[1]
        except IndexError:
            return

        if "&t=" in url:
            return await client.send_message(message.channel, "No timestamps allowed!")
        if "&list=" in url:
            return await client.send_message(message.channel, "No playlists allowed!")

        self.__player_object.enqueue_song(server, url)

        if not await client.init_voice_client(message):
            if server.get_voice_client() is None:
                return

        if server.get_player() is not None:
            if server.get_player().is_playing() and server.is_interruptable():
                server.get_player().stop()
            elif server.get_player().is_playing():
                return await client.send_message(message.channel, "Added to queue")

        return await self.play_next(server, client.loop)






