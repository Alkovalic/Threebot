import Command


class REBOOT(Command.Command):

    def info(self):

        name = "reboot"
        description = ("Reboots the voice client in the current channel.\n"
                       "Format:  reboot\n"
                       "Note:  Clears current queue if one exists.\n")
        return name, description

    async def run(self, client, message):

        await client.send_message(message.channel, "Resetting voice client..")
        return await client.get_server_data(message).reset_voice_client(client)
        # return await client.get_cmd_dict()["clear"].run(client, message)
