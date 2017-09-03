import random
import Command
import discord


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
            """
            to_string = "```" + info_tuple[0] + ":\n\n"
            to_string += info_tuple[1] + "```"
            return to_string
            """

            embed = discord.Embed(title=info_tuple()[0], description=info_tuple()[1], color=discord.Color.gold())
            embed.set_author(name="Threebot Command")

        else:
            return None

    def get_all_commands(self, server_data):

        cmds = server_data.get_command_whitelist()

        embed = discord.Embed(title=" ", color=discord.Color.gold())
        embed.set_author(name="List of Threebot commands:")

        for item in cmds:
            embed.add_field(name=item, value=cmds[item], inline=True)

        return embed

    def info(self):

        command = "help"
        description = "https://suicidepreventionlifeline.org/"

        return command, description

    async def run(self, client, message):

        command_content = None
        try:
            command_content = message.content.lstrip(client._cmdSym).split(" ")[1]
        except IndexError:
            return await client.send_message(message.channel, embed=self.get_all_commands(client.get_server_data(message=message)))

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

        if type(to_string) is str:
            return await client.send_message(message.channel, to_string)

        return await client.send_message(message.channel, embed=to_string)


