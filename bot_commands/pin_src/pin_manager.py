import os
import discord
import youtube_dl

from bot_commands.pin_src import file_manager


class PinManager:

    """ Helper class for pin that handles database transactions and file storage. """

    def __init__(self, bot):
        self._bot = bot
        self._db_manager = bot.db_manager
        self._file_manager = file_manager.FileManager(os.getcwd() + "/guild_file_data")
        self._sound_extensions = [".webm", ".mp3", ".wav"]

    # PRIMARY METHODS #

    # Add an entry, given a name, author, and value.
    # If value is a discord.Attachment, save the file, and add the entry to the database.
    # If value is a string, just add the entry to the database.
    async def add_entry(self, name : str, author : str, guild_id, value):

        # (type, name, author, value, path)
        # name and author are given from arguments
        # value is given if value is a string, and must be saved if it is an attachment.
        # path is the path of the attachment provided, or None if there was no attachment.
        # type is either SOUND or PIN, depending on these conditions:
        # - if value is an attachment of filetypes .mp3, .wav, and .webm,
        #   or if value is a valid Youtube URL, the type will be SOUND.
        # - otherwise, the type will be PIN.

        # Make sure name is not none.
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # First, get the type of entry that has been passed.

        entry_type = "PIN"
        entry_path = None
        entry_value = None

        # Get the associated table with the given guild.
        guild_table = self._db_manager.get_table_name(guild_id)

        # Handle case where value is an attachment, a.k.a an image, file, etc.
        if isinstance(value, discord.Attachment):
            
            # Check for sound related files.
            for e in self._sound_extensions:
                if value.filename.endswith(e):
                    entry_type = "SOUND"
                    break
            
            # From here, the type has been set, and we need to save the file.
            try:
                entry_path = await self._file_manager.add_file(value, guild_id)

            # Handle case where the file already exists.
            # Raise an exception that has the entry name as the argument.
            except FileExistsError as e:
                # Raise an exception, with the found entry as the result.
                # NOTE:  If a file in the database is removed, without removing the
                #        entry in the database, this may cause an error.
                raise FileExistsError((await self._db_manager.filter_db_entries(guild_table, e.args[0], "path"))[0].name)
        
        # Handle special cases when value is a string.
        else:
            
            # If value doesn't exist, raise error.
            if value.isspace() or not value:
                raise ValueError("Value cannot be empty!")

            entry_value = value

            # Handle Youtube URLs.
            if "youtu.be" in value or "watch?v=" in value:
                try:
                    entry_path = await self._file_manager.add_ytlink(value, guild_id)
                except FileExistsError as e:
                    # Same as above:  raise the name of the entry as an exception.
                    raise FileExistsError((await self._db_manager.filter_db_entries(guild_table, e.args[0], "path"))[0].name)

            if entry_path:
                entry_type = 'SOUND'

        # At this point, everything is ready to be added to the database.

        entry_tuple = entry_type, name, author, entry_value, entry_path
        result = await self._db_manager.insert_db_entry(guild_table, (entry_tuple))
        
        # If the insert fails, then the name is already in use, and cannot be reused.
        if not result:
            try:
                await self._file_manager.remove_file(entry_path)
            except TypeError: # Handling case where no file was saved.
                pass
            raise FileExistsError(name)

    # Remove an entry, given a name, author, and guild_id.
    # If the author is not the owner of the entry, raise the error.
    # Else, remove the entry, and return the file as a string or a discord.File object.
    # If override is true, remove the entry regardless of ownership.
    async def remove_entry(self, name : str, author : str, guild_id, override=False):

        # Check if the name isn't blank.
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # Attempt to remove the given entry.
        guild_table = self._db_manager.get_table_name(guild_id)
        result = None
        try:
            result = await self._db_manager.remove_db_entry(guild_table, name, author, override=override)
        except PermissionError as e:  # Here just to show that this error is supposed to happen.
            raise e

        # Handle the case where the entry didn't exist.
        if result is None:
            return None
        
        # From here, something has been removed from the database.
        # Get whatever was removed, remove it from the disk, and send it.
        
        # Handle the case where the entry was a file.
        elif result.path:
            # Getting filesize.
            is_oversized = (os.stat(result.path).st_size > 8000000)
            file = await self._file_manager.remove_file(result.path)
            
            # If the file is too large to upload, just upload the value.
            if is_oversized:
                file.close()
                return result.value
            else:
                return file

        # Handle the case where the entry was a string.
        else:
            return result.value
        

    # Get an entry, given a name and guild_id.
    # Returns either a discord.File object or a string.
    # Returns None when the entry isn't found.
    async def get_entry(self, name : str, guild_id):
        
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # Get the entry associated with the given name.
        guild_table = self._db_manager.get_table_name(guild_id)
        details = await self._db_manager.get_db_entry(guild_table, name)

        # No details found, no entry found.
        if details is None:
            return None

        # If a path exists, open and return it.
        if details.path:
            return await self._file_manager.get_file(details.path)

        # At this point, the only reasonable possibility is the value being a string.
        return details.value

        

    # Returns both detailed information about the entry,
    #  and, if a file is associated with the entry, said file
    #  as a discord.File object.
    # The information is returned as a tuple (<info tuple>, File)
    # Returns None if the entry is not found.
    async def get_entry_details(self, name : str, guild_id):
        
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # Get the entry associated with the given name.
        guild_table = self._db_manager.get_table_name(guild_id)
        details = await self._db_manager.get_db_entry(guild_table, name)

        # No details found, no entry found.
        if details is None:
            return None

        file = None
        # If a path exists, open and return it.
        if details.path:
            file = await self._file_manager.get_file(details.path)

        # Return all info gathered.
        return (details, file)

    # Gets a list of entries similar to the given name.
    # If the given name is a single letter, gets a list of
    #  entries that start with that letter.
    async def search_entries(self, name : str, guild_id):
        
        # Get all entries similar to the given name.
        guild_table = self._db_manager.get_table_name(guild_id)
        entries = await self._db_manager.search_db_entries(guild_table, name)

        # Clean up the result to just be a list of strings.

        result = []
        for i in entries:
            result.append(i[0])

        return result

