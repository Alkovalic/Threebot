import os
import random


class RandomBooGenerator:

    """ Very important BOO generator do not steal """

    def __init__(self):
        self._images = self.__init_dir()
        self._table = self.__init_table(self.__get_table_info())

    # Initializes the directory the Boo images are found.
    def __init_dir(self):
        boo_dir = os.path.dirname(os.path.realpath(__file__)) + "\\boo"

        # If the directory exists, set up the table.
        # If the directory exists, but a certain Boo image is NOT found, the entry will not exist,
        #  which may cause errors later.  Handled in get_random_boo.
        if os.path.isdir(boo_dir):
            boo_dict = self.__get_table_info()
            image_list = os.listdir(boo_dir)
            return_dict = {}

            for entry in boo_dict:
                for img in image_list:
                    if img.startswith(entry):
                        return_dict[entry] = f"{boo_dir}\\{img}"
                        break
            return return_dict

        else:
            print("Boo directory not found!")
            return None

    # Initializes the dictionary holding information about Boo drop tables.
    def __get_table_info(self):
        boo_dict = {
            "boo": 49,
            "kingboo": 15,
            "magicboo": 25,
            "pinkgayboo": 10,
            "rainbowboo": 1
        }
        return boo_dict

    # Returns the table holding the actual Boo drop table, given a drop table dictionary.
    def __init_table(self, dict):
        boo_table = list()
        for key in dict:
            boo_table += [key] * (dict[key])
        return boo_table

    # Returns the path of the image of the Boo that was randomly selected.
    def get_random_boo(self):

        # Return None if the directory didn't load correctly.
        if self._images is None:
            return None

        # Select a Boo, and return it's path.
        boo = random.choice(self._table)
        try:
            return self._images[boo]
        except KeyError:
            print(f"Image for {boo} not found!")
            return None
