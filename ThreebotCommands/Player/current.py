import Command


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
            return await client.send_message(message.channel, "Current song:  None")
        return await client.send_message(message.channel, "Current song:  " + video_data.get_url())
