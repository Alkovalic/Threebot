import random
import Command


class ROLL(Command.Command):

    def info(self):

        name = "roll"
        description = ("Returns a dice roll and it's sum specified by the user.\n"
                       "Format:  roll <dice>d<faces>\n"
                       "Note:  roll returns 3d6 if no arguments are provided.")

        return name, description

    def roll(self, number, sides):

        rolls = []

        for i in range(number):
            rolls += [random.randint(1, sides)]

        return rolls, sum(rolls)

    async def run(self, client, message):

        final_rolls = None
        final_sum = None

        try:
            stuff = message.content.split(" ")[1]
            cool_stuff = stuff.split("d")

            final_rolls, final_sum = self.roll(int(cool_stuff[0]), int(cool_stuff[1]))

        except (IndexError, ValueError):

            final_rolls, final_sum = self.roll(3, 6)

        to_string = message.author.name + " rolled: "

        for i in final_rolls:
            to_string += str(i) + ", "

        to_string = to_string[:-2] + " (Sum: " + str(final_sum) + ")"

        return await client.send_message(message.channel, to_string)


