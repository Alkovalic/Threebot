import Command
import requests
import os
import shutil


class SOUNDS(Command.Command):

    def info(self):
        name = "sounds"
        desc = ("Returns the list of sounds available to the server.\n"
                "Can also be used to save a new sound file that can only be "
                "accessed by the server it was saved in.\n"
                "If an argument is given otherwise, it will search sounds for "
                "any sounds that start with the argument.\n\n"
                "Formats:\nsounds <search>\nsounds save")

        return name, desc

    def save_file(self, url, filename, path):

        explore = {'User-agent': 'Mozilla/5.0'}

        if self.exists(filename, "/home/pi/Threebot/default_sounds/"):
            return False

        if self.exists(filename, path):
            return False

        file_url = requests.get(url, stream=True, headers=explore)
        if file_url.status_code == 200:
            with open(path + filename, 'wb') as f:
                file_url.raw.decode_content = True
                shutil.copyfileobj(file_url.raw, f)
        else:
            return False
        return True

    def exists(self, filename, path):
        return filename in os.listdir(path)

    def get_sounds_dir(self, id):
        return "/home/pi/Threebot/ServerData/" + id + "/sounds/"

    async def run(self, client, message):

        default_dir = client.get_default_sounds()
        server_dir = client.get_server_data(message).get_server_dir() + "/sounds/"
        songlist = os.listdir(default_dir) + os.listdir(server_dir)
        songlist.sort()

        cmd = message.content.lstrip(client._cmdSym)

        to_string = "```"

        if cmd == "sounds save":

            path = self.get_sounds_dir(message.server.id)

            await client.send_message(message.channel, "Please upload your file.")
            file_message = await client.wait_for_message(timeout=15, author=message.author)

            if file_message is None:
                print("fail")
                return

            if len(file_message.attachments) == 0:
                return await client.send_message(message.channel, "File not found.")

            file = file_message.attachments[0]

            is_invalid = True

            for i in (".mp3", ".wav", ".webm"):
                if file["filename"].endswith(i):
                    is_invalid = False
                    break

            if is_invalid:
                return await client.send_message(message.channel, "Invalid format:  only .webm, .mp3, .wav supported.")

            if self.save_file(file["url"], file["filename"], path):
                return await client.send_message(message.channel, "Save success!")
            return await client.send_message(message.channel, "Filename in use. / Invalid status code.")

        if cmd == "sounds":

            to_string += "List of sounds available in " + message.server.name + ":\n\n  "

            for song in songlist:
                flag = True
                for i in "зхцвбнмасдфгчйкльжэъщюпоиуытрешяё":
                    if song.startswith(i):
                        flag = False

                if flag:
                    to_string += song.split(".")[0]
                    to_string += ", "
            to_string = to_string[:-2] + "```"
            return await client.send_message(message.channel, to_string)

        else:

            search_term = cmd.split(" ")[1]

            to_string += "List of sounds available in " + message.server.name + " beginning with " + search_term + ":\n\n  "

            for song in songlist:
                flag = True
                for i in "зхцвбнмасдфгчйкльжэъщюпоиуытрешяё":
                    if song.startswith(i):
                        flag = False

                if flag:
                    if song.startswith(search_term):
                        to_string += song.split(".")[0]
                        to_string += ", "
            to_string = to_string[:-2] + "```"
            return await client.send_message(message.channel, to_string)
