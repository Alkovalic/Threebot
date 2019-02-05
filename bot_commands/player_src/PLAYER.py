from discord.ext import commands
from discord import ClientException, Embed
from . import voice_queue

import enum
import asyncio

class Player:

    def __init__(self, bot):
        self._bot = bot
        self._pool = None
        self._voice_queues = {}
        self._pin_table = "PIN_{}"
        self._queue_management_task = self._bot.loop.create_task(self.manage_queues())

    # Responsible for clearing inactive voice clients.
    # Every 60 seconds, this task will check every VoiceQueue in the dict of voice queues.
    # - If the queue's state is PLAYING/UNINTERRUPTABLE, do nothing.
    # - If the queue's state is NOT PLAYING, change the state to STALE.
    # - If the queue's state is STALE, disconnect the queue and remove it from the dict of voice queues.
    async def manage_queues(self):
        await self._bot.wait_until_ready()
        print("fda")
        while not self._bot._is_closed():
            print("asdf")
            for guild in list(self._voice_queues.keys()):
                vq = self._voice_queues[guild]
                if vq.state == voice_queue.PlayerState.UNINTERRUPTABLE or vq.state == voice_queue.PlayerState.PLAYING:
                    pass
                elif vq.state == voice_queue.PlayerState.NOT_PLAYING:
                    vq.state = voice_queue.PlayerState.STALE
                else:
                    await vq.exit_channel()
                    del self._voice_queues[guild]
            await asyncio.sleep(60)
        

    # Creates a VoiceQueue for the given guild and discord.Voice object,
    #  and adds it to the dictionary of guilds.
    def _create_queue(self, guild_id, voice):
        self._voice_queues[guild_id] = voice_queue.VoiceQueue(self._bot.loop, self._bot.output_path)

    def _remove_queue(self, guild_id):
        del self._voice_queues[guild_id]

    # Sends a message in response to ctx that will be deleted in the given amount of time in seconds.
    # Usually used for error responses.
    async def send_timed_msg(self, ctx, msg, time=3):
        msg = await ctx.send(msg)
        await asyncio.sleep(time, loop=self._bot.loop)
        await msg.delete()

    # Get the database pool once the database has been fully loaded.
    async def on_ready(self):

        # Do nothing if the pool already exists.
        if not self._pool is None:
            return

        while not self._bot.pool:
            await asyncio.sleep(delay=1, loop=self._bot.loop)

        self._pool = self._bot.pool

    async def on_voice_state_update(self, member, before, after):
        try:
            if member.guild.id in self._voice_queues:
                await self._voice_queues[member.guild.id].generate_voting_dictionaries()
        except AttributeError: # Occurs when the bot first joins a channel.
            pass

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
            
            # Get the entry from the PIN database by name.
            pin_table = self._pin_table.format(message.guild.id)
            query = None
            async with self._pool.acquire() as conn:
                async with conn.cursor() as c:
                    await c.execute(rf"SELECT * FROM {pin_table} WHERE name=(?)", cmd)
                    query = await c.fetchone()

            # If the query returns None, no entry was found, so we ignore the request.
            if not query:
                return
            
            # If the query is of type PIN, ignore it.
            if query.type == "PIN":
                return

            # At this point, the query is of type SOUND, so we attempt to play it.
            # Create a VoiceQueue object for the server if one does not already exist.
            if not message.guild.id in self._voice_queues:
                self._create_queue(message.guild.id, message.author.voice)
            # Create a voice client for the guild.  If the user is not in a voice channel, do nothing.
            if not await self._voice_queues[message.guild.id].join_channel(message.author.voice):
                return
            # Finally, attempt to play the audio through the voice client.
            await self._voice_queues[message.guild.id].play_audio_file(query.name, query.path, message.author.id)

    @commands.command(help="Play audio from a given URL.\n"
                           "If the player is currently playing something, add the url to the queue.\n"
                           "Does nothing if neither the user nor the bot is in a voice channel.",
                      brief="- Plays audio from a URL.")
    async def play(self, ctx, url=None):
        
        # Create a queue if one does not exist.
        if not ctx.guild.id in self._voice_queues:
            self._create_queue(ctx.guild.id, ctx.author.voice)
        # Create a voice client for the guild if one does not exist,
        #  or move the existing voice client to the channel the user is in.
        # If the user isn't in a channel, and a voice client doesn't exist, do nothing.
        if not await self._voice_queues[ctx.guild.id].join_channel(ctx.author.voice):
            return
        # Play the provided url through the voice client.
        if url:
            if not await self._voice_queues[ctx.guild.id].play_audio_url(url, ctx.author.id):
                return await self.send_timed_msg(ctx, "Added to queue.")

    @commands.command(help="Vote to skip the currently playing song.\n"
                           "If at least three (or majority, whichever is less) votes are made,"
                           " the current song is skipped."
                           "Immediately skip if the user is the one who added the song to the queue,"
                           " or is an administrator.",
                      brief="- Vote to skip the current song.")
    async def skip(self, ctx):

        # If there is no voice client connected to this guild, do nothing.
        if not ctx.guild.id in self._voice_queues:
            return

        # If the current audio that is playing isn't part of a queue, skip it like the stop command would.
        if self._voice_queues[ctx.guild.id].state != voice_queue.PlayerState.UNINTERRUPTABLE:
            return self._voice_queues[ctx.guild.id].skip_current_audio()

        # Attempt to cast a vote for the author.
        try:
            result = await self._voice_queues[ctx.guild.id].vote_to_skip(ctx.author.id, ctx.author.permissions_in(ctx.channel).administrator)
        except (ClientException):
            return await self.send_timed_msg(ctx, "You are not currently in the same channel as Threebot.")
        
        # If the vote caused a majority/3 to pass, briefly notify the voters.
        if result:
            return await self.send_timed_msg(ctx, "The current song has been skipped!")
        else:
            return await self.send_timed_msg(ctx, f"{ctx.author.name} has voted to skip the current song!")
        

    @commands.command(help="Vote to clear the queue.\n"
                            "If at least three (or majority, whichever is less) votes are made,"
                            " the queue is cleared.\n"
                            "Immediately skip if the user is an administrator.",
                      brief="- Vote to clear the queue.")
    async def clear(self, ctx):
    
        # If there is no voice client connected to this guild, do nothing.
        if not ctx.guild.id in self._voice_queues:
            return

        # If the current audio that is playing isn't part of a queue, skip it like the stop command would.
        if self._voice_queues[ctx.guild.id].state != voice_queue.PlayerState.UNINTERRUPTABLE:
            return self._voice_queues[ctx.guild.id].skip_current_audio()

        # Attempt to cast a vote for the author.
        try:
            result = await self._voice_queues[ctx.guild.id].vote_to_clear(ctx.author.id, ctx.author.permissions_in(ctx.channel).administrator)
        except (ClientException):
            return await self.send_timed_msg(ctx, "You are not currently in the same channel as Threebot.")
        
        # If the vote caused a majority/3 to pass, briefly notify the voters.
        if result:
            return await self.send_timed_msg(ctx, "The queue has been cleared!")
        else:
            return await self.send_timed_msg(ctx, f"{ctx.author.name} has voted to clear the queue!")

    @commands.command(help="Shows a list of songs in the queue.",
                      brief="- Shows a list of songs.")
    async def queue(self, ctx):
        
        # If there is no voice client connected to this guild, do nothing.
        if not ctx.guild.id in self._voice_queues:
            return
        
        # Get the list of items in the queue.
        q = self._voice_queues[ctx.guild.id].queue_summary

        if not q:
            return

        # If there is anything in the queue, return a formatted list of them, including the currently playing item.
        ret = f"```\nQueue:\n\n   {self._voice_queues[ctx.guild.id].currently_playing.name} (NOW PLAYING)\n"
        ptr = 0
        for item in q:
            ret += f"   {item}\n"
            if ptr > 5:
                ret += f"(And {len(q) - ptr} more.."
                break
            else:
                ptr += 1

        ret += "```"

        return await ctx.send(ret)

    @commands.command(help="Shows information about the currently playing song.",
                      brief="- Shows the current song.")
    async def current(self, ctx):

        # If there is no voice client connected to this guild, do nothing.
        if not ctx.guild.id in self._voice_queues or not self._voice_queues[ctx.guild.id].currently_playing:
            return

        item = self._voice_queues[ctx.guild.id].currently_playing
        name = item.name
        url = item.url
        author_text = f"Requested by {ctx.guild.get_member(item.author_id).display_name}."

        # name, url, authorid

        embed=Embed(title=name, url=url, color=0xfffc00)
        embed.set_author(name="Now playing:")
        embed.set_footer(text=author_text)
        return await ctx.send(embed=embed)

    @commands.command(help="Stops the audio currently playing, "
                           "if the audio is not part of the queue.",
                      brief="- Stops the player on certain conditions.")
    async def stop(self, ctx):
        
        # Handle case where the guild has no voice client connected.
        if not ctx.guild.id in self._voice_queues:
            return

        if self._voice_queues[ctx.guild.id].state != voice_queue.PlayerState.UNINTERRUPTABLE:
            self._voice_queues[ctx.guild.id].skip_current_audio()


def setup(bot):
    bot.add_cog(Player(bot))
