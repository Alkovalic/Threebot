import enum
import discord
import youtube_dl
import asyncio

class PlayerState(enum.Enum):
    PLAYING = 0
    NOT_PLAYING = 1
    UNINTERRUPTABLE = 2
    STALE = 3

class AudioData():

    # Try adding a "Time played/time left" member
    def __init__(self, name, source, url, playlist, author_id):
        self.name = name
        self.source = source
        self.url = url
        self.playlist = playlist
        self.author_id = author_id
        #self.time_left

class VoiceQueue():

    def __init__(self, loop, output_path):
        self._loop = loop
        self._state = PlayerState.NOT_PLAYING
        self._queue = list()
        self._skip_votes = dict()
        self._clear_votes = dict()
        self._currently_playing = None
        self._voice_client = None
        self._video_path = f"{output_path}/videos/"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value : PlayerState):
        self._state = value

    @property
    def currently_playing(self):
        return self._currently_playing

    # Returns the list of items in the queue.
    @property
    def queue_summary(self):
        return [x.name for x in self._queue]

    # Updates the voice state depending on what the voice client is doing.
    # This method will never be responsible for setting the state to "STALE"
    def _update_state(self, uninterruptable=False):
        if uninterruptable:
            self._state = PlayerState.UNINTERRUPTABLE
        elif self._voice_client.is_playing():
            self._state = PlayerState.PLAYING
        else:
            self._state = PlayerState.NOT_PLAYING
        
    # Creates an AudioData given at least a name and a path, and returns it.
    # url is optional, usually representing the online source of the file.
    # playlist should be True if the AudioData is meant to be added to the queue.
    def _create_audio_data(self, name, path, author_id=None, url=None, playlist=False):
        src = discord.FFmpegPCMAudio(path)
        return AudioData(name, src, url, playlist, author_id)

    # Conditionally plays an audio source.
    # If no audio is currently playing, play the source normally.
    # If audio is playing, play the audio passed instead.
    # If audio is playing, but the audio is uninterruptable, ignore the audio source.
    #   However, if playlist is true, add the source to the queue.
    # Returns true if the audio plays, and false if is either added to the queue, or not added at all.
    async def _play_audio_data(self, data):

        # Return flag for the function.
        ret = False

        # Handle the case where the source is part of a playlist.
        if data and data.playlist:
            if self._voice_client.is_playing() and self._state == PlayerState.UNINTERRUPTABLE:
                self._queue.append(data)
            else:
                self._currently_playing = data

                # Taken from discord.py documentation FAQ.
                def next_song(error):
                    if error:
                        print(error)

                    coro = self._play_audio_data(None if len(self._queue)==0 else self._queue.pop(0))
                    fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
                    try:
                        fut.result()
                    except Exception as e:
                        print(e)
                if self._state == PlayerState.PLAYING:
                    self._voice_client.stop()
                self._voice_client.play(data.source, after=next_song)
                ret = True

        # Handle the case where the source is not part of a playlist.
        elif data and self._state != PlayerState.UNINTERRUPTABLE:
            self._currently_playing = data
            self._voice_client.stop()
            self._voice_client.play(data.source)
            ret = True

        # Handle the case where data is passed, but the queue is uninterruptable.
        elif data:
            pass

        # Handle the case where no data is passed, which means the queue has been depleted.
        else:
            self._currently_playing = None

        # Update the state of the queue.
        self._update_state(data and (data.playlist or self._state == PlayerState.UNINTERRUPTABLE))

        # Clear all votes for skipping and clearing.
        await self.generate_voting_dictionaries(clear=True)

        return ret

    # Skips the current audio source.
    # Returns True on success, False if nothing is playing.
    # Also sets the player state accordingly.
    def skip_current_audio(self):
        if self._voice_client.is_playing():
            self._voice_client.stop()
            self._update_state()
            return True 
        return False

    # Joins a voice channel using the given discord.Voice object.
    #  voice is usually obtained from the author of a message.
    # If the voice client isn't connected already, initialize a voice client for that channel.
    # Otherwise, move the voice client into the author's channel.
    # If the author isn't in a channel, return False, otherwise, return True.
    async def join_channel(self, voice):

        # Check if the author is in a voice channel.
        if voice is None:
            return False

        # Create the voice client if it doesn't already exist.
        if self._voice_client is None:
            self._voice_client = await voice.channel.connect()
            await self.generate_voting_dictionaries()
            return True

        # Move the voice client to the author's channel.
        await self._voice_client.move_to(voice.channel)
        await self.generate_voting_dictionaries()
        return True

    # Disconnect from the voice channel the voice client is currently in.
    async def exit_channel(self):
        return await self._voice_client.disconnect()

    # Play audio from the local filesystem given a path.
    async def play_audio_file(self, name, path, author_id):
        
        # If no path is passed, do nothing.
        if not path:
            return
        
        # Create an audio source based off of the path, and attempt to play it.
        data = self._create_audio_data(name, path, author_id=author_id)
        await self._play_audio_data(data)

    # Play audio from the internet given a URL.
    # Code based off of examples provided in the discord.py repo.
    # Returns True if the audio is played immediately, and False if it is queued or failed.
    async def play_audio_url(self, url, author_id):
        loop = self._loop or asyncio.get_event_loop()
        extract_opt = {
            'format': '43/best',
            'outtmpl': f'{self._video_path}/%(title)s_%(id)s.%(ext)s',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }
        with youtube_dl.YoutubeDL(extract_opt) as extr:
            video_data = await loop.run_in_executor(None, lambda: extr.extract_info(url, download=False))

            # If the video is live, just put the url in as the filename.
            filename = video_data['url']

            opt = {
                'format': '43/best',
                'outtmpl': f'{self._video_path}/%(title)s_%(id)s.%(ext)s',
                'noplaylist': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'download_archive': f'{self._video_path}/video_list.txt',
            }

            # If the video is NOT live, download the file, and replace the filename accordingly.
            if not video_data['is_live']:
                with youtube_dl.YoutubeDL(opt) as yt:
                    yt.download([url])
                filename = extr.prepare_filename(video_data)

            print(filename)

            data = self._create_audio_data(name=video_data.get('title', 'untitled'), path=filename, author_id=author_id, url=url, playlist=True)
            return await self._play_audio_data(data)

    # Appropriately set a vote to skip from the given author id.
    # Return True if the audio is skipped, and False if it is not.
    # If, after adding the vote, the number of votes reaches the amount needed to skip, skip the current song.
    # Also skips the song if the author_id matches the id of the author who played the song, 
    #  or if the admin flag is set to True.
    async def vote_to_skip(self, author_id, admin=False):
        
        # Set vote accordingly.
        if not author_id in self._skip_votes.keys():
            raise discord.ClientException("Author not in channel.")
        self._skip_votes[author_id] = True
        
        # Check if the overall vote has passed.
        total_votes = 0
        for value in self._skip_votes.values():
            total_votes = (total_votes + 1) if value else total_votes
        
        # If there is a majority vote, or >=3 votes, or a special condition passes,
        #  skip the current song.
        if (total_votes >= 3 or total_votes / len(self._skip_votes.values()) > .5 or
            self._currently_playing.author_id == author_id or admin):
            self.skip_current_audio()
            await self.generate_voting_dictionaries(clear=True)
            return True
        return False

    # Appropriately set a vote to clear from the given author id.
    # If the author isn't currently in the dictionary of possible voters, return False.
    # Otherwise, return True.
    async def vote_to_clear(self, author_id, admin=False):

        # Set vote accordingly.
        if not author_id in self._clear_votes.keys():
            raise discord.ClientException("Author not in channel.")
        self._clear_votes[author_id] = True
        
        # Check if the overall vote has passed.
        total_votes = 0
        for value in self._clear_votes.values():
            total_votes = (total_votes + 1) if value else total_votes
        
        # If there is a majority vote, or >=3 votes, skip the current song.
        if (total_votes >= 3 or total_votes / len(self._skip_votes.values()) > .5 or
            self._currently_playing.author_id == author_id or admin):
            self._queue = list()
            self.skip_current_audio()
            await self.generate_voting_dictionaries(clear=True)
            return True
        return False

    # (Re)generate the skip/clear voting dictionaries.
    # If clear is enabled, clears all votes.
    async def generate_voting_dictionaries(self, clear=False):

        # Create new dictionaries to replace the old ones.
        new_clear_votes = dict()
        new_skip_votes = dict()

        # Iterate through all current members in the voice client's channel,
        #  and use them to populate the new dictionaries.
        # Doing this removes any existing votes from members that are no longer in the channel.
        for member in self._voice_client.channel.members:

            # Add onto the new_skip_votes dictionary.
            if member not in self._skip_votes.keys() or clear:
                new_skip_votes[member.id] = False
            else:
                new_skip_votes[member.id] = self._skip_votes[member.id]

            # Add onto the new_clear_votes dictionary.
            if member not in self._skip_votes.keys() or clear:
                new_clear_votes[member.id] = False
            else:
                new_clear_votes[member.id] = self._clear_votes[member.id]

        # Finally, assign the new dictionaries to the appropriate member variable.
        self._clear_votes = new_clear_votes
        self._skip_votes = new_skip_votes

