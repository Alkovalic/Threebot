import Command
import youtube_dl
import pickle
import re
import os


class PLAYER(Command.Command):

    def __init__(self):
        self.__queues = {}
        self.__currents = {}
        self.__dl_dir = None
        self.__directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + "video_data.pickle"
        # data = open("/home/pi/Threebot/video_data.pickle", "rb")
        data = open(self.__directory, "rb")
        self.__video_data_dict = pickle.load(data)

    """
    enqueue_song creates VideoData that will be placed in video_data_dict to be pickled later,
    IF the VideoData doesn't exist.  Either way, it will then add the VideoData to the queue of
    the specific server.
    """

    def get_queue(self, server_data):
        return self.__queues[server_data]

    def pickle_video_data(self):

        backup_name = self.__directory + ".old"

        if os.path.isfile(backup_name):
            os.remove(backup_name)

        os.rename(self.__directory, backup_name)

        with open(self.__directory, "wb") as file:
            pickle.dump(self.__video_data_dict, file)
            file.close()

    def enqueue_song(self, server_data, url):

        if url not in self.__video_data_dict:

            with youtube_dl.YoutubeDL({'quiet': True}) as ydl:  # Getting data on the video.
                info = ydl.extract_info(url, download=False)

                data_args = {
                    'name': info['title'],
                    'url': url,
                    'path': None
                }
                if not info['is_live'] and int(info['duration']) < 1860:  # If it's not a stream and it's not too long.

                    path = self.__dl_dir + re.sub("[^\\w]", "", info['id'])

                    info_opts = {
                        'quiet': True,
                        'format': '43/best',
                        'outtmpl': path + '.%(ext)s'
                    }

                    data_args['path'] = path + ".webm"  # This is problematic:  hard-coding a file extension

                    with youtube_dl.YoutubeDL(info_opts) as new_ydl:
                        new_ydl.download([url])

                self.__video_data_dict[url] = VideoData(data_args)

            self.pickle_video_data()

    # At this point in the program, we have VideoData of whatever is being added.
    # Now we have to add the song to the queue of the provided server ID.

        if server_data not in self.__queues:
            self.__queues[server_data] = []

        self.__queues[server_data].append(self.__video_data_dict[url])

    """
    dequeue_song removes the first song from the specified queue, and returns it.
    server_data should be a ServerData object.
    """

    def dequeue_song(self, server_data):
        queue = self.__queues[server_data]
        if len(queue) == 0:
            self.nullify_current_song(server_data)
            return None
        dequeued = queue[0]
        self.__currents[server_data] = dequeued  # Current song stuff.
        del queue[0]
        return dequeued

    def clear_queue(self, server_data):

        self.__queues[server_data] = []
        self.__currents[server_data] = None

    """
    get_current_song returns None if no song is playing.
    """

    def skip_song(self, server_data):
        server_data.get_player().stop()

    def get_current_song(self, server_data):
        try:
            return self.__currents[server_data]
        except KeyError:
            return None

    def nullify_current_song(self, server_data):
        self.__currents[server_data] = None

    """
    initialize adds player to the provided commands in cmd_dict.
    """

    def initialize(self, cmd_dict, dl_dir):
        self.__dl_dir = dl_dir

        for name in ["play", "current", "clear", "queue", "skip"]:
            cmd_dict[name].set_player_obj(self)

    def info(self):

        name = "player"
        desc = ("Plays a provided link, typically from Youtube.\n\n"
                "Formats:  \n"
                "  play <url> - Adds the content to the queue.\n"
                "  clear      - Clears the current queue.\n"
                "  skip       - Skips the song currently playing.\n"
                "  current    - Displays the current song playing.\n"
                "  queue      - Displays up to the first 10 songs in queue.\n\n"
                "Notes:  \n"
                "  Playlists and timestamped videos will not be played.\n"
                "  Streams can be choppy and crazy, so play them at your own risk.\n")

        return name, desc

    async def run(self, client, message):
        pass


class VideoData():

    def __init__(self, args):
        self.__video_name = args["name"]
        self.__video_url = args["url"]
        self.__video_path = args["path"]

    def get_name(self):
        return self.__video_name

    def get_url(self):
        return self.__video_url

    def get_path(self):
        return self.__video_path
