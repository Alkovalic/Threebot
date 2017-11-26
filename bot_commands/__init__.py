'''
Dynamically adds all .py files to threebot_commands
Credit to Lennart Regebro for the help.
https://stackoverflow.com/questions/1057431/loading-all-modules-in-a-folder-in-python
'''

import os


__all__ = []

for file in os.listdir(os.path.dirname(__file__)):
    if file == '__init__.py' or not file.endswith(".py"):
        continue
    __all__.append(file[:-3])

from . import *