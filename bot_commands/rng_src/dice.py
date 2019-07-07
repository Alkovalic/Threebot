import random
import re

# r"^([+-]?[0-9]+(d[0-9]+)?)+$"

class Dice:

    def __init__(self, output_format):
        self.output_format = output_format
        self.msg_length_limit = 2000
        self.author_len_limit = 32

    # Returns the "largest" possible output for a given input and author.
    # Used for checking the maximum length of the output string, given a dice roll, an author, and roll reason.
    # Returns None if the argument is formatted incorrectly, ignoring whitespace.
    def max_length(self, arg):

        # Check argument format.
        if not re.search(r"^([+-]?[0-9]+(d[0-9]+)?)+$", arg.replace(" ","")):
            return self.msg_length_limit + 1

        # Clean up the given roll, and split up the roll based on +- operators.
        roll = arg.replace(" ", "")
        split_args = re.split(r"[+-]", roll)

        # Calculate the length of the string that the input could potentionally generate.
        format_len = len(self.output_format.format(author='', input='', result='', sum=''))
        roll_len = len(roll)
        result_len = 0
        sum_len = 0
        for r in split_args:
            if r == '':
                continue
            if 'd' in r:
                vals = r.split('d')
                sum_len += (int(vals[0]) * int(vals[1])) # number of dice * number of faces
                # (length of max result * number of results) + (number of results - beginning operand + parens + starting operand
                result_len += (len(vals[1]) * int(vals[0])) + int(vals[0]) + 2
            else:
                sum_len += int(r)
                result_len += len(r)
            if result_len > self.msg_length_limit:
                return self.msg_length_limit + 1

        return format_len + self.author_len_limit + roll_len + result_len + len(str(sum_len))

    def roll_dice(self, arg, author):

        # Check argument format.
        if not re.search(r"^([+-]?[0-9]+(d[0-9]+)?)+$", arg.replace(" ","")):
            return "Message is improperly formatted!"

        # Clean up the given roll, and split up the roll based on the +- operators.

        roll = arg.replace(" ", "")
        split_args = re.split(r"([+-])", roll)

        # Roll the dice.
        # This loop builds both the result string and the sum at the same time.

        sum = 0
        next_op = "+" # Previous operator found, set every time an operator is encountered.
        result = ""

        for r in split_args:
            
            if r in "-+": # Case where r is an operator.
                next_op = r
            
            elif 'd' in r: # Case where r is a dice roll.
                
                # Roll the dice and get the final total.
                vals = r.split('d')
                res = 0
                res_string = ""
                for _ in range(int(vals[0])):
                    res_roll = random.randint(1, int(vals[1]))
                    res += res_roll
                    res_string += f"+{res_roll}"

                result += next_op + ("(0)" if res_string == "" else f"({res_string.lstrip('+')})")
                sum += res * (-1 if (next_op == '-') else 1)

            else: # Case where r is a constant value.
                
                result += next_op + r
                sum += int(r) * (-1 if (next_op == '-') else 1)

        return self.output_format.format(author=author, input=arg.replace(" ",""), result=result.lstrip("+"), sum=sum)