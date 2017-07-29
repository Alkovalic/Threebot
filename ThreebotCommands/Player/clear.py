import Command


class CLEAR(Command.Command):

    def __init__(self):
        self.__player_object = None

    def set_player_obj(self, obj):
        self.__player_object = obj

    def info(self):
        return "player"

    async def run(self, client, message):

        server = client.get_server_data(message)

        self.__player_object.clear_queue(server)
        self.__player_object.skip_song(server)

        return await client.send_message(message.channel, "Queue cleared!")
