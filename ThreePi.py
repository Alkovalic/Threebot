import os
import discord
import Threebot
import time
import ThreeParser
import pickle

class ThreePi(Threebot.Threebot):

    def __init__(self, args, command_dict):
        super().__init__(args["config"], command_dict)
        self.__misc_dir = args["default_misc"]
        self.__sound_dir = args["default_sounds"]
        self.__server_data_dir = args["server_data"]
        self.__server_dict = {}
        self.__creation_time = time.time()

        # TODO:  make the PM commands similar to the regular commands to avoid clutter.

        self.__pm_help = """
```
Available server management commands: \n\n
To enable/disable the whitelist in a given server for all commands:
enableWL <serverID>\n
To add a user to a server's whitelist:
addWL <serverID> <userID>\n
To remove a user from a server's whitelist:
rmWL <serverID> <userID>\n
To show all whitelisted users in a server:
showWL <serverID>\n
To show all users in a server:
showUsers <serverID>\n
To show all servers available for you to manage:
showServers\n
To decide whether users with administrative rights can manage Threebot:
allowAdmin <serverID>\n
To set permissions for specific commands available in a server:
state <serverID> <cmdName> <enabled/disabled/whitelisted>\n
To show all sound files in a server's local sound folder:
showSound <serverID>\n
To get a sound file from a server's local sound folder:
getSound <serverID> <soundName> (Note:  file extension necessary)\n
To remove a sound file from a server's local sound folder:
rmSound <serverID> <soundName> (Note:  file extension necessary)\n
To show all mern files in a server's local mern folder:
showMern <serverID>\n
To get a mern file from a server's local mern folder:
getMern <serverID> <mernName> (Note:  file extension necessary)\n
To remove a mern file from a server's local mern folder:
rmMern <serverID> <imageName> (Note:  file extension necessary)
```
"""
        self.__pm_dict = {
            "enableWL": self.pm_enable_whitelist,
            "addWL": self.pm_add_whitelist,
            "rmWL": self.pm_rm_whitelist,
            "showWL": self.pm_show_whitelist,
            "showUsers": self.pm_show_users,
            "showServers": self.pm_show_servers,
            "allowAdmin": self.pm_allow_admin,
            "state": self.pm_set_state,
            "showSound": self.pm_show_sounds,
            "getSound":  self.pm_get_sound,
            "rmSound": self.pm_rm_sound,
            "showMern": self.pm_show_mern,
            "getMern":  self.pm_get_mern,
            "rmMern": self.pm_rm_mern
        }

    def __load_server_data(self, server, files):

        if server.id not in files:
            os.makedirs(self.__server_data_dir + server.id)
            os.makedirs(self.__server_data_dir + server.id + "/sounds")
            os.makedirs(self.__server_data_dir + server.id + "/mern")
            os.makedirs(self.__server_data_dir + server.id + "/misc")

            with open(self.__server_data_dir + server.id + "/whitelist.pickle", "wb") as f:
                cmd_wl = {}
                for i in self._cmd_dict:
                    cmd_wl[i] = "enabled"
                pickle.dump({
                    "whitelist": {server.owner.id: server.owner.name},
                    "is_enabled": False,
                    "cmd_whitelist": cmd_wl,
                    "admin_access": False,
                }, f)
                f.close()

        if server.id not in self.__server_dict:
            self.__server_dict[server.id] = ServerData(server, self.__server_data_dir + server.id)
            self.__server_dict[server.id].init_whitelist()

    def init_data(self, new_server=None):

        if new_server is None:
            if len(self.__server_dict) != 0:  # This is a small optimization that keeps init_data from reiterating everything.
                return

            files = os.listdir(self.__server_data_dir)

            for i in self.servers:
                self.__load_server_data(i, files)

            print("Data initialized!")

        else:
            self.__load_server_data(new_server, os.listdir(self.__server_data_dir))
            print("New server data initialized!  Server name:  " + new_server.name)

    def get_uptime(self):
        return time.time() - self.__creation_time

    def get_server_data(self, message=None):
        if message is None:
            return self.__server_dict
        return self.__server_dict[message.server.id]

    def get_default_sounds(self):
        return self.__sound_dir

    def get_default_misc(self):
        return self.__misc_dir

    def check_wl(self, message):
        current_server = self.__server_dict[message.server.id]

        if not current_server.is_whitelist_enabled():
            return current_server.check_command(self, message)

        return message.author.id in current_server.get_whitelist() or message.author.id in self._whitelist

    async def init_voice_client(self, message, move=True):

        if message.author.voice.voice_channel is None:
            return False

        if not self.is_voice_connected(message.server):
            current_client = await self.join_voice_channel(message.author.voice.voice_channel)
            self.__server_dict[message.server.id].set_voice_client(current_client)
            return True
        if move:
            await self.__server_dict[message.server.id].get_voice_client().move_to(message.author.voice.voice_channel)

        return True

    async def do_default(self, command, message):

        cool_dir = None
        server_sounds = self.__server_dict[message.server.id].get_server_dir() + "/sounds/"

        for file in os.listdir(server_sounds):
            if file.split(".")[0] == command:
                cool_dir = server_sounds + file
                break

        if cool_dir is None:
            for file in os.listdir(self.__sound_dir):
                if file.split(".")[0] == command:
                    cool_dir = self.__sound_dir + file
                    break

        if cool_dir is None:
            return

        flag = await self.init_voice_client(message)
        if not flag:
            return

        server = self.__server_dict[message.server.id]
        current_player = server.get_player()

        if not server.is_interruptable():
            return

        if current_player is not None:
            if current_player.is_playing():
                current_player.stop()

        server.set_player(server.get_voice_client().create_ffmpeg_player(cool_dir, use_avconv=True))
        server.get_player().start()

    async def do_pm_command(self, message):

        if message.content.lstrip(self._cmdSym) == "im gay":
            return await self.send_file(message.author, os.path.dirname(__file__) + "default_misc/important_image.jpg")

        can_input_commands = False
        available_servers = {}  # Available servers mapped as <server id> => <ServerData>

        if message.author.id in self._whitelist:
            can_input_commands = True
            available_servers = self.get_server_data()

        if not can_input_commands:

            for server in self.servers:
                data = self.get_server_data()[server.id]

                if server.owner.id == message.author.id:
                    available_servers[data.__str__()] = data
                    can_input_commands = True
                    continue

                if data.get_admin_access() and message.author in server.members:
                    person = None
                    for user in server.members:
                        if user.id == message.author.id:
                            person = user
                            break
                    if person.server_permissions.administrator:
                        available_servers[data.__str__()] = data
                        can_input_commands = True

        if not can_input_commands:
            return

        else:
            return await self.parse_pm_command(message, available_servers)

    async def parse_pm_command(self, message, servers):
        cmd = message.content.lstrip(self._cmdSym)
        if cmd == "help":
            return await self.send_message(message.author, self.__pm_help)
        try:
            return await self.__pm_dict[cmd.split(" ")[0]](message, servers)
        except KeyError:
            return

    # Begin PM Commands #

    async def pm_enable_whitelist(self, message, servers):
        server = None  # Unnecessary?

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument!")

        setting = not server.is_whitelist_enabled()
        server.set_whitelist_enabled(setting)

        self.save_data(server)

        if setting:
            return await self.send_message(message.author, "Whitelist enabled.")
        return await self.send_message(message.author, "Whitelist disabled.")

    async def pm_add_whitelist(self, message, servers):
        server = None
        user_id = None
        username = None
        try:
            server = servers[message.content.split(" ")[1]]
            user_id = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument(s)!")

        is_in_server = False

        if server.get_server().owner.id != user_id:
            for user in server.get_server().members:
                if user.id == user_id:
                    is_in_server = True
                    username = user.name
                    break

        if is_in_server:
            server.get_whitelist()[user_id] = username
            self.save_data(server)
            return await self.send_message(message.author, username + " has been added to the specified server's whitelist!")
        return await self.send_message(message.author, "Failed to add ID to the server's whitelist.")

    async def pm_rm_whitelist(self, message, servers):
        server = None
        user_id = None

        try:
            server = servers[message.content.split(" ")[1]]
            user_id = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument(s)!")

        try:
            if server.get_server().owner.id == user_id:
                return await self.send_message(message.author, "Cannot remove owner from whitelist.")
            del server.get_whitelist()[user_id]
            self.save_data(server)
            return await self.send_message(message.author, "Removal success!")
        except KeyError:
            return await self.send_message(message.author, "Failed to remove user from whitelist.")

    async def pm_show_whitelist(self, message, servers):
        server = None

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument!")

        to_string = "```Whitelist for " + server.get_server().name + ":  \n\n"

        for key in server.get_whitelist():
            to_string += server.get_whitelist()[key] + ": " + key + "\n"

        return await self.send_message(message.author, to_string + "```")

    async def pm_show_users(self, message, servers):
        server = None

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument!")

        to_string = "```Members in " + server.get_server().name + ":  \n\n"

        for member in server.get_server().members:
            to_string += member.name + ": " + member.id + "\n"

        return await self.send_message(message.author, to_string + "```")

    async def pm_show_servers(self, message, servers):
        to_string = "```Available, manageable servers:  \n\n"

        for key in servers:
            to_string += servers[key].get_server().name + ": " + key + "\n"

        return await self.send_message(message.author, to_string + "```")

    async def pm_allow_admin(self, message, servers):

        # TODO:  Check if this shit works.

        server = None

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid argument!")

        state = not server.get_admin_access()

        server.set_admin_access(state)
        self.save_data(server)
        return await self.send_message(message.author, "Admin access:  " + str(state))

    async def pm_set_state(self, message, servers):

        server = None
        command = None
        state = None

        try:
            args = message.content.split(" ")
            server = servers[args[1]]
            command = args[2]
            state = args[3]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        if command not in server.get_command_whitelist():
            return await self.send_message(message.author, "Invalid command passed!")

        if state not in ["enabled", "disabled", "whitelisted"]:
            return await self.send_message(message.author, "Invalid state passed!")

        server.get_command_whitelist()[command] = state
        self.save_data(server)

        return await self.send_message(message.author, command + " has been set to " + str(state))

    async def pm_show_sounds(self, message, servers):

        server = None

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/sounds/'

        to_string = "```List of sounds available in " + server.get_server().name + ":\n\n"

        for i in os.listdir(dir):
            to_string += i + "\n"

        return await self.send_message(message.author, to_string + "```")

    async def pm_get_sound(self, message, servers):

        server = None
        file = None

        try:
            server = servers[message.content.split(" ")[1]]
            file = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        if "/" in file or "\\" in file:
            return await self.send_message(message.author, "Invalid argument!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/sounds/'

        if file in os.listdir(dir):
            return await self.send_file(message.author, dir + file)
        else:
            return await self.send_message(message.author, "File not found.")

    async def pm_rm_sound(self, message, servers):

        server = None
        file = None

        try:
            server = servers[message.content.split(" ")[1]]
            file = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        if "/" in file or "\\" in file:
            return await self.send_message(message.author, "Invalid argument!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/sounds/'

        if file in os.listdir(dir):
            await self.send_file(message.author, dir + file)
            os.remove(dir + file)
            return await self.send_message(message.author, file + " removed!")
        else:
            return await self.send_message(message.author, "File not found.")

    async def pm_show_mern(self, message, servers):

        server = None

        try:
            server = servers[message.content.split(" ")[1]]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/mern/'

        to_string = "```List of mern images available in " + server.get_server().name + ":\n\n"

        for i in os.listdir(dir):
            to_string += i + "\n"

        return await self.send_message(message.author, to_string + "```")

    async def pm_get_mern(self, message, servers):

        server = None
        file = None

        try:
            server = servers[message.content.split(" ")[1]]
            file = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        if "/" in file or "\\" in file:
            return await self.send_message(message.author, "Invalid argument!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/mern/'

        if file in os.listdir(dir):
            return await self.send_file(message.author, dir + file)
        else:
            return await self.send_message(message.author, "File not found.")

    async def pm_rm_mern(self, message, servers):

        server = None
        file = None

        try:
            server = servers[message.content.split(" ")[1]]
            file = message.content.split(" ")[2]
        except (KeyError, IndexError):
            return await self.send_message(message.author, "Invalid arguments!")

        if "/" in file or "\\" in file:
            return await self.send_message(message.author, "Invalid argument!")

        dir = os.path.dirname(__file__) + '/ServerData/' + server.__str__() + '/mern/'

        if file in os.listdir(dir):
            await self.send_file(message.author, dir + file)
            os.remove(dir + file)
            return await self.send_message(message.author, file + " removed!")
        else:
            return await self.send_message(message.author, "File not found.")

    # End PM Commands

    def save_data(self, server=None):
        if server is None:
            for i in self.__server_dict:
                self.__server_dict[i].save_whitelist_info()
        else:
            server.save_whitelist_info()

    async def on_message(self, message):

        if isinstance(message.channel, discord.PrivateChannel):

            if message.author == self.user:
                return

            if message.content.startswith(self._cmdSym):

                print("[PM] " + message.author.name + ": " + message.content)

                return await self.do_pm_command(message)

        return await self.do_message_command(message)

    async def on_ready(self):
        self.init_data()

    async def on_server_join(self, server):
        self.init_data(new_server=server)


class ServerData():

    def __init__(self, server, server_data_dir):

        self.__server = server
        self.__id = server.id
        self.__server_data = server_data_dir
        self.__voice_client = None
        self.__player = None
        self.__player_interruptable = True
        self.__whitelist = None
        self.__whitelist_enabled = False
        self.__allow_admin = False
        self.__command_whitelist = None

    # Accessors and Mutators

    def __str__(self):
        return self.__id

    def get_server(self):
        return self.__server

    def get_server_dir(self):
        return self.__server_data

    def get_voice_client(self):
        return self.__voice_client

    def set_voice_client(self, vclient):
        if not isinstance(vclient, discord.VoiceClient):
            raise AttributeError("Object passed is not a VoiceClient!")
        self.__voice_client = vclient

    def get_player(self):
        return self.__player

    def set_player(self, player):
        self.__player = player

    def is_whitelist_enabled(self):
        return self.__whitelist_enabled

    def set_whitelist_enabled(self, boolean):
        if not isinstance(boolean, bool):
            raise AttributeError("Item passed is not a boolean!")
        self.__whitelist_enabled = boolean

    def get_whitelist(self):
        return self.__whitelist

    def get_command_whitelist(self):
        return self.__command_whitelist

    def check_command(self, client, message):
        if message.author.id in client._whitelist:
            return True

        try:
            state = self.__command_whitelist[message.content.lstrip(client._cmdSym).split(" ")[0]]
            if state == "whitelisted":
                return message.author.id in self.__whitelist
            if state == "disabled":
                return False
            return True

        except KeyError:
            if self.is_whitelist_enabled():
                if message.author in self.__whitelist:
                    return True
                return False
            return True

    def is_interruptable(self):
        return self.__player_interruptable

    def set_interruptable(self, boolean):
        if not isinstance(boolean, bool):
            raise AttributeError("Item passed is not a boolean!")
        self.__player_interruptable = boolean

    def get_admin_access(self):
        return self.__allow_admin

    def set_admin_access(self, boolean):
        if not isinstance(boolean, bool):
            raise AttributeError("Item passed is not a boolean!")
        self.__allow_admin = boolean

    # Everything else

    def init_whitelist(self):
        with open(self.__server_data + "/whitelist.pickle", "rb") as f:
            data = pickle.load(f)
            self.__whitelist = data["whitelist"]
            self.__whitelist_enabled = data["is_enabled"]
            self.__command_whitelist = data["cmd_whitelist"]
            self.__allow_admin = data["admin_access"]

    def save_whitelist_info(self):

        current_name = self.__server_data + "/whitelist.pickle"
        backup_name = self.__server_data + "/whitelist.pickle.old"

        if os.path.isfile(backup_name):
            os.remove(backup_name)

        os.rename(current_name, backup_name)

        with open(current_name, "wb") as f:
            pickle.dump({"whitelist": self.__whitelist,
                         "is_enabled": self.__whitelist_enabled,
                         "cmd_whitelist": self.__command_whitelist,
                         "admin_access": self.__allow_admin,
                         }, f)
            f.close()

    async def reset_voice_client(self, client, after=None):

        if self.__voice_client is None:
            return

        channel = self.__voice_client.channel

        if self.__player and self.__player.is_playing():
            self.__player.pause()

        await self.__voice_client.disconnect()
        self.__voice_client = await client.join_voice_channel(channel)
        if self.__player:
            self.__player.resume()
        if after is not None:
            await after()

