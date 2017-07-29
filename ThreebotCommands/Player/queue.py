import Command


class QUEUE(Command.Command):

    def __init__(self):
        self.__player_object = None

    def set_player_obj(self, obj):
        self.__player_object = obj

    def info(self):
        return "player"

    async def run(self, client, message):

        server = client.get_server_data(message)
        songs = self.__player_object.get_queue(server)

        inc = 0

        to_string = "```Currently queued:\n\n"

        for song in songs:
            if inc == 10:
                to_string += "...\n"
                break
            to_string += song.get_name() + "\n"
            inc += 1

        to_string += "```"

        return await client.send_message(message.channel, to_string)