import random


# Checks if a roll is valid.
def is_valid_roll(arg):

    # Setting up check.
    default_check = arg.split("d")
    faces = default_check[0]
    amount = default_check[1]

    # Check if both arguments are numeric.
    if not faces.isnumeric() or not amount.isnumeric():
        return False

    # Check if either argument is zero.
    if not int(faces) or not int(amount):
        return False

    # 5000000 IQ char check, assuming 63 chars are reserved for formatting, out of the 2000 char limit.
    if len(amount) + (int(amount) * len(faces)) + len(faces) + (2 * int(amount)) + 1 > 1937:
        return False

    # At this point, the result is probably valid.
    return True


# Rolls <amount> dice with <faces> faces.
def roll_dice(amount, faces):
    results = []

    for i in range(amount):
        results.append(random.randint(1, faces))

    return results


# Rolls an ndn roll, and returns a string in the following format:
# <author> rolled <result>! (Sum:  <result_sum>, Input:  <amount>d<faces>)
# Returns an error message if ndn is improperly formatted.
def roll_string(author, ndn):
    try:
        amount, faces = ndn.lower().split("d")
        result = roll_dice(int(amount), int(faces))
        return f"{author} rolled {result}! (Sum:  {sum(result)}, Input:  {ndn})"
    except ValueError:
        return "Roll must be in ndn format!"
