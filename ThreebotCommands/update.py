import Command
import git
import os
import subprocess


class UPDATE(Command.Command):

    async def run(self, client, message):

        if not message.author.id == "158738845758652416":
            return

        await client.send_message(message.channel, "Updating Threebot..")

        g = git.cmd.Git(os.path.dirname(os.path.dirname(__file__)))
        g.pull()

        command = "/usr/bin/sudo /sbin/shutdown -r now"
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
        output = process.communicate()[0]
        print(output)