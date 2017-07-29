import Command


class SKIP(Command.Command):

    def __init__(self):
        self.__player_object = None

    def set_player_obj(self, obj):
        self.__player_object = obj

    def info(self):
        return "player"

    async def run(self, client, message):
        server = client.get_server_data(message)

        if server.get_player() is None or not server.get_player().is_playing():
            return

        return self.__player_object.skip_song(server)