import Command
import requests
import os
import random
import shutil


class MERN(Command.Command):

    def __init__(self):
        self.__default = os.listdir("/home/pi/Threebot/default_misc/mern/")
        for i in range(len(self.__default)):
            self.__default[i] = "/home/pi/Threebot/default_misc/mern/" + self.__default[i]

    def info(self):
        name = "mern"
        desc = ("Returns the user's feelings at the time the command was issued.\n\n"
                "Formats: \n"
                "mern - Returns aforementioned information.\n"
                "mern save - Saves an image provided by the user for use by mern.\n"
                "Note:  mern will not overwrite existing files.")

        return name, desc

    def get_mern_dir(self, id):
        return os.path.dirname(os.path.dirname(__file__)) + "ServerData/" + str(id) + "/mern/"

    def get_random_image(self, path):
        image_list = os.listdir(path) + self.__default
        ptr = random.randint(0, len(image_list) - 1)

        random_image = image_list[ptr]

        if "default_misc/mern/" not in random_image:
            random_image = path + random_image

        return random_image

    def exists(self, filename, path):
        return filename in os.listdir(path)

    def save_image(self, url, filename, path):

        explore = { 'User-agent': 'Mozilla/5.0' }

        if self.exists(filename, path):
            return False

        image_url = requests.get(url, stream=True, headers=explore)
        if image_url.status_code == 200:
            with open(path + filename, 'wb') as f:
                image_url.raw.decode_content = True
                shutil.copyfileobj(image_url.raw, f)
        else:
            return False
        return True


    async def run(self, client, message):

        cmd = message.content.lstrip(client._cmdSym)

        if cmd == "mern save":

            path = self.get_mern_dir(message.server.id)

            await client.send_message(message.channel, "Please upload your file.")
            file_message = await client.wait_for_message(timeout=10, author=message.author)

            if file_message is None:
                return

            if len(file_message.attachments) == 0:
                return await client.send_message(message.channel, "File not found.")

            image = file_message.attachments[0]

            if not image["filename"].endswith(".gif"):
                return await client.send_message(message.channel, "Feelings can only be described with .gifs")

            if image["size"] > 9437184:
                return await client.send_message(message.channel, "File too big! (turbo nerd..)")

            if self.save_image(image["url"], image["filename"], path):
                return await client.send_message(message.channel, "Save success!")
            return await client.send_message(message.channel, "Filename in use. / Invalid status code.")

        else:

            return await client.send_file(message.channel, self.get_random_image(self.get_mern_dir(message.server.id)))
