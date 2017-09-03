import Command


class UPTIME(Command.Command):

    def info(self):
        name = "uptime"
        description = ("Returns the time since Threebot's last reboot.\n\n"
                       "Format:  uptime")

        return name, description

    async def run(self, client, message):
        etime = int(client.get_uptime())

        days = etime // 86400
        hours = etime % 86400 // 3600
        minutes = etime % 86400 % 3600 // 60
        seconds = etime % 86400 % 3600 % 60

        text = "Current uptime:  " + str(days) + " days, " + str(hours) + " hours, " + str(
            minutes) + " minutes, " + str(seconds) + " seconds."

        return await client.send_message(message.channel, text)


