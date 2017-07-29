import random
import Command


class HELP(Command.Command):

    def __init__(self):
        self.__cmd_dict = None

    def set_cmd_dict(self, cmd_list):
        self.__cmd_dict = cmd_list

    def fail_message(self, command):
        return "No such command:  " + command

    def parse_info(self, info_tuple):

        if info_tuple is None:
            to_string = ("```You have been reported to the FBI for the attempted use of " + "[REDACTED]" + "!\n"
                         "Please stay where you are.  [REPORT FILE:  T" + str(random.randint(1, 500)) + " " +
                         str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) + str(random.randint(0, 9)) + "]```")
            return to_string

        elif type(info_tuple) is tuple:
            to_string = "```" + info_tuple[0] + ":\n\n"
            to_string += info_tuple[1] + "```"
            return to_string

        else:
            return None

    def get_all_commands(self):

        command_list = []
        to_string = "```List of commands in Threebot:  \n\n"

        for i, j in self.__cmd_dict.items():
            a = j.info()
            if a is not None and len(a) == 2:
                command_list.append(j)

        for i in command_list:
            to_string += i.info()[0] + "\n"

        return to_string + "```"

    def info(self):

        command = "help"
        description = "https://suicidepreventionlifeline.org/"

        return command, description

    async def run(self, client, message):

        command_content = None
        try:
            command_content = message.content.lstrip(client._cmdSym).split(" ")[1]
        except IndexError:
            return await client.send_message(message.channel, self.get_all_commands())

        help_obj = None

        try:
            help_obj = self.__cmd_dict[command_content]
        except KeyError:
            return await client.send_message(message.channel, self.fail_message(command_content))

        to_string = self.parse_info(help_obj.info())


        while to_string is None:
            try:
                help_obj = self.__cmd_dict[help_obj.info()]
            except KeyError:
                raise KeyError("Invalid return value passed by info!")

            to_string = self.parse_info(help_obj.info())

        return await client.send_message(message.channel, to_string)



