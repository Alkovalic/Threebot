import enum
from discord.ext import commands
from . import voice_queue

class Player:

    def __init__(self, bot):
        self._bot = bot
        self._db_manager = bot.db_manager
        self._voice_queues = {}

    # Creates a VoiceQueue for the given guild and discord.Voice object,
    #  and adds it to the dictionary of guilds.
    def __create_queue(self, guild_id, voice):
        self._voice_queues[guild_id] = voice_queue.VoiceQueue(voice)

    def __remove_queue(self, guild_id):
        del self._voice_queues[guild_id]

    # PLAYER's on_message reads every message that starts withh the command prefix.
    # It then attempts to find the entry in the PIN database.
    # If an entry is found, it checks for whether it is a sound command, and plays it.
    async def on_message(self, message):

        if message.content.startswith(self._bot.command_prefix):

            # Remove the command prefix, and get the first word sent.
            cmd = message.content.lstrip(self._bot.command_prefix)

            # Handle empty case.
            if not cmd:
                return
            
            # Ignore all built-in commands.
            for i in self._bot.commands:
                if cmd == i.name:
                    return

            # Check if the command ends with -s.
            # If it does, allow the sound to be silently played later.
            silent = False
            if cmd.endswith(" -s"):
                silent = True
                cmd = cmd.rstrip("- s")
            
            query = await self._db_manager.get_db_entry(self._db_manager.get_table_name(message.guild.id), cmd)

            # If the query returns None, no entry was found, so we ignore the request.
            if not query:
                return
            
            # If the query is of type PIN, ignore it.
            if query.type == "PIN":
                return

            # At this point, the query is of type SOUND, so we attempt to play it.
            # Create a VoiceQueue object for the server if one does not already exist.
            if not message.guild.id in self._voice_queues:
                self.__create_queue(message.guild.id, message.author.voice)
            # Create a voice client for the guild.  If the user is not in a voice channel, do nothing.
            if not await self._voice_queues[message.guild.id].join_channel(message.author.voice):
                return
            # Finally, attempt to play the audio through the voice client.
            await self._voice_queues[message.guild.id].play_audio_file(query.name, query.path)

    @commands.command(help="Play audio from a given URL.\n"
                           "If the player is currently playing something, add the url to the queue.\n"
                           "Does nothing if neither the user nor the bot is in a voice channel.",
                      brief="- Plays audio from a URL.")
    async def play(self, ctx, url=None):
        pass

    @commands.command(help="Vote to skip the currently playing song.\n"
                           "If at least three (or majority, whichever is less) votes are made,"
                           " the current song is skipped."
                           "Immediately skip if the user is the one who added the song to the queue,"
                           " or is an administrator.",
                      brief="- Vote to skip the current song.")
    async def skip(self, ctx):
        pass

    @commands.command(help="Vote to clear the queue.\n"
                            "If at least three (or majority, whichever is less) votes are made,"
                            " the queue is cleared.\n"
                            "Immediately skip if the user is an administrator.",
                      brief="- Vote to clear the queue.")
    async def clear(self, ctx):
        pass

    @commands.command(help="Shows a list of songs in the queue.",
                      brief="- Shows a list of songs.")
    async def queue(self, ctx):
        pass

    @commands.command(help="Shows information about the currently playing song.",
                      brief="- Shows the current song.")
    async def current(self, ctx):
        pass

    @commands.command(help="Stops the audio currently playing, "
                           "if the audio is not part of the queue.",
                      brief="- Stops the player on certain conditions.")
    async def stop(self, ctx):
        
        # Handle case where the guild has no voice client connected.
        if not ctx.guild.id in self._voice_queues:
            return

        self._voice_queues[ctx.guild.id].stop_player()


def setup(bot):
    bot.add_cog(Player(bot))
