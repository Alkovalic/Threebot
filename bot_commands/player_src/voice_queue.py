import enum
import discord

class PlayerState(enum.Enum):
    PLAYING = 0
    NOT_PLAYING = 1
    UNINTERRUPTABLE = 2
    STALE = 3

class AudioData():

    # Try adding a "Time played/time left" member
    def __init__(self, name, source, url, playlist):
        self.name = name
        self.source = source
        self.url = url
        self.playlist = playlist
        #self.time_left

class VoiceQueue():

    def __init__(self, voice):
        self._state = PlayerState.NOT_PLAYING
        self._queue = []
        self._currently_playing = None
        self._voice_client = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value : PlayerState):
        self._state = value

    @property
    def curently_playing(self):
        return self._currently_playing

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
    def _create_audio_data(self, name, path, url=None, playlist=False):
        src = discord.FFmpegPCMAudio(path)
        return AudioData(name, src, url, playlist)

    # Conditionally plays an audio source.
    # If no audio is currently playing, play the source normally.
    # If audio is playing, play the audio passed instead.
    # If audio is playing, but the audio is uninterruptable, ignore the audio source.
    #   However, if playlist is true, add the source to the queue.
    async def _play_audio_data(self, data, playlist=False):

        # Handle the case where the source is part of a playlist.
        if data and data.playlist:
            if self._voice_client.is_playing() and self._state == PlayerState.UNINTERRUPTABLE:
                self._queue.append(data)
            else:
                self._currently_playing = data
                self._voice_client.play(data.source)

        # Handle the case where the source is not part of a playlist.
        elif data and self._state != PlayerState.UNINTERRUPTABLE:
            self._currently_playing = data
            self._voice_client.stop()
            self._voice_client.play(data.source)

        # Update the state of the queue.
        self._update_state(data and playlist)

    # Conditionally stops the current audio source from playing.
    # Will not work if the player is uninterruptable.
    # Returns True on success, False on failure.
    #  Failure entails the player being uninterruptable, or if nothing is playing.
    # Also sets the player state accordingly.
    def stop_player(self):
        if self._state != PlayerState.UNINTERRUPTABLE and self._voice_client.is_playing():
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
            return True

        # Move the voice client to the author's channel.
        await self._voice_client.move_to(voice.channel)
        return True

    # Disconnect from the voice channel the voice client is currently in.
    async def exit_channel(self):
        return await self._voice_client.disconnect()

    async def play_audio_file(self, name, path):
        
        # If no path is passed, do nothing.
        if not path:
            return
        
        # Create an audio source based off of the path, and attempt to play it.
        data = self._create_audio_data(name, path)
        await self._play_audio_data(data)


    