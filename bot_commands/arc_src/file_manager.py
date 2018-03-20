import discord
import os


class FileManager:

    """ Helper class for Threebot and its cogs that manages files. """

    # Takes a path to where files are stored.
    def __init__(self, path):
        self._path = path

    # PRIMARY METHODS #

    # Adds a file to a guild's directory.
    # Takes a discord.Attachment object as it's argument.
    # Creates a new directory if the guild has no entries.
    # Returns a file path on success, or None if the adding failed.
    async def add_file(self, attachment, guild_id):

        # Get the attachments found in the ctx.

        # If there are no attachments, return None.
        if not attachment:
            return None

        # If the guild directory does not exist, create it!
        path = self.__create_guild_dir(guild_id)
        if path is None:  # Guild probably already exists.
            path = f"{self._path}\\{guild_id}"

        # Create the path for the file.
        filename = f"{path}\\{attachment.filename}"

        # Check if the file exists.
        if os.path.isfile(filename):
            return None

        # At this point, we are ready to save the file.
        await attachment.save(filename)
        return filename

    # Removes a file from a guild's directory.
    # Note:  if all files are removed from a directory,
    #        the directory does not get removed.
    # Returns a discord.File object on success, or None on failure.
    def remove_file(self, path):

        # Get the file, and handle the case where it doesn't exist.
        result = self.get_file(path)
        if result is not None:
            os.remove(path)

        return result

    # Retrieves a file from a guild's directory.
    # Returns a discord.File object on success, or None on failure.
    def get_file(self, path):

        # Check if the file exists.
        if not os.path.isfile(path):
            return None

        with open(path, 'rb') as file:
            result = discord.File(file)

        return result

    # Creates a directory for a guild, if none exists.
    # Returns the path to the new directory on success, or None on failure.
    def __create_guild_dir(self, guild_id):

        new_directory = f"{self._path}\\{guild_id}"

        try:
            os.mkdir(new_directory)
            return new_directory
        except OSError:  # Directory already exists, or something stupid happened.
            return None
