# Threebot.py

import discord
import logging
import ThreeParser


from discord import opus

# opus.load_opus('libopus-0.x64.dll')

logging.basicConfig(level=logging.INFO)


class Threebot(discord.Client):

    def __init__(self, three_config_dir, command_dict):

        super().__init__()

        prse = ThreeParser.ThreeParser(three_config_dir + "Options.txt", three_config_dir + "Whitelist.txt")
        options, whitelist = prse.getAll()
        self._cmdSym = options['cmdSym']
        self.__cToken = options['cToken']
        self._cmd_dict = command_dict
        self._whitelist = whitelist
        self._whitelistEnabled = options['enWL']

    def __cmd_parse(self, cmd):
        user_command = cmd.content.lstrip(self._cmdSym).split(' ', 1)[0]

        return user_command, cmd

    async def do_message_command(self, message):

        if message.author == self.user:
            return

        if message.content.startswith(self._cmdSym):

            print("[" + message.server.name + "] " + message.author.name + ": " + message.content)

            user_cmd, msg = self.__cmd_parse(message)

            await self.delete_message(message)

            if not self.check_wl(msg):
                return

            return await self.execute(user_cmd, msg)

    def check_wl(self, message):

        if not self._whitelistEnabled:
            return True
        else:
            return message.author.id in self._whitelist

    def get_cmd_dict(self):
        return self._cmd_dict

    async def do_default(self, command, message):
        return

    async def execute(self, command, message):

        try:
            await self._cmd_dict[command].run(self, message)
        except KeyError:
            await self.do_default(command, message)

    #async def on_error(self, event_method, *args, **kwargs):
        #print("Super gay stuff:")
        #print(event_method)
        #print(*args)
        #print(**kwargs)

    # THE MAIN DEAL #

    async def on_message(self, message):

        return await self.do_message_command(message)

    # THIS IS WHAT THE FUTURE LOOKS LIKE #

    def CANNON_ENGAGED(self):  # FEEL THE THUNDER

        # EYES ON THE HORIZON #

        if self.__cToken is "":
            raise TypeError("No bot token found!")
        if self._cmdSym is "":
            raise TypeError("No cmd symbol found!")

        # NEVER GIVE UP #

        self.run(self.__cToken)
