import random
import Command


class BOO(Command.Command):
    # The format of this command is ~BOO

    def __init__(self):

        self._normalBoo = booLocation("boo.png", 101)
        self._wizardBoo = booLocation("magicboo.jpg", 50)
        self._kingBoo = booLocation("kingboo.png", 25)
        self._pinkGayBoo = booLocation("pinkgayboo.png", 10)
        self._rainBoo = booLocation("rainboo.gif", 1)
        self._boo_list = [self._rainBoo, self._pinkGayBoo, self._kingBoo, self._wizardBoo, self._normalBoo]

        self._boo_list.sort()

    def info(self):

        command = "BOO"
        description = ("Returns a random Boo.  \n\nCurrent chance table:  \n"
                       "Normal Boo:  50%\n"
                       "Wizard Boo:  25%\n"
                       "King Boo:  15%\n"
                       "Pink Gay Boo:  10%\n"
                       "RainBoo:  gay%\n"
                       "Format:  BOO\n"
                       )

        return command, description

    async def run(self, client, message):

        ptr = 0
        roll = random.randint(0, 100)

        while ptr < len(self._boo_list):
            if roll < self._boo_list[ptr].getChance():
                short_string = self._boo_list[ptr].getDirectory()
                return await client.send_file(message.channel, client.get_default_misc() + "BOO/" + short_string)
            ptr += 1


class booLocation():  # Under no normal circumstance should this be initialized in openthegame.py

    def __init__(self, location, chance):
        self.__boo_directory = location
        self.__chance = chance

    def getChance(self):
        return self.__chance

    def getDirectory(self):
        return self.__boo_directory

    def __gt__(self, other):
        return self.__chance > other.__chance

    def __repr__(self):
        return self.__boo_directory
