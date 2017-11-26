from discord.ext import commands
from bot_commands.rng import Dice

import os
import pickle


class Threebot(commands.Bot):

    def __init__(self, cogs, **args):
        super().__init__(**args)
        self._cogs = cogs
        self._guild_data = None
        self._has_loaded = False

    def __create_guild_data(self):

        res = self.__load_guild_pickle()
        for guild in self.guilds:
            if guild not in res:
                res[guild.id] = GuildData(guild.id)
        return res

    def __load_guild_pickle(self):

        if "guilds.pickle" in os.listdir(os.getcwd()):
            with open(os.getcwd() + "\guilds.pickle", "rb") as file:
                return pickle.load(file)
        else:
            return {}

    def save_guild_pickle(self):

        if "guilds.pickle" in os.listdir(os.getcwd()):
            os.rename(os.getcwd() + "\guilds.pickle", os.getcwd() + "\guilds.pickle.old")

        with open(os.getcwd() + "\guilds.pickle", "wb") as file:
            pickle.dump(self._guild_data, file)

    async def on_guild_join(self, guild):
        self._guild_data[guild.id] = GuildData(guild.id)

    async def on_guild_remove(self, guild):
        del self._guild_data[guild.id]

    async def on_ready(self):

        if not self._has_loaded:

            self._guild_data = self.__create_guild_data()

            for cog in self._cogs:
                self.load_extension(cog)
            self._has_loaded = True

            print("Connected!")
        else:
            print("Reconnected!")



class GuildData:

    """ GuildData stores various info about servers Threebot is in."""

    def __init__(self, id):

        self._id = id

        # RNG
        self._default_roll = Dice(3,6)  # Default roll for a specific server.
        # Soundboard - probably make a folder
        # Archive - db connection
        # Reminder? - probably empty _ or none to start
