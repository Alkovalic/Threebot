import Command


class TEST(Command.Command):

    async def run(self, client, message):
        with open("home/pi/Threebot/default_misc/important_image.jpg", 'rb') as f:
                return await client.edit_profile(avatar=f.read())
