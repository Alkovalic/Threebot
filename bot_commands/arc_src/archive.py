import os
import discord
from bot_commands.arc_src import file_manager


class Archive:

    """ Helper class for arc that handles database transactions and file storage. """

    def __init__(self, bot):
        self._bot = bot
        self._db_manager = bot.db_manager
        self._file_manager = file_manager.FileManager(os.getcwd() + "/guild_file_data")
        self._sound_extentions = [".webm", ".mp3", ".wav"]

    # PRIMARY METHODS #

    # Add an entry, given a name, author, and value.
    # If value is a discord.Attachment, save the file, and add the entry to the database.
    # If value is a string, just add the entry to the database.
    async def add_entry(self, name : str, author : str, guild_id, guild_table, value):

        # (type, name, author, value, path)
        # name and author are given from arguments
        # value is given if value is a string, and must be saved if it is an attachment.
        # path is the path of the attachment provided, or None if there was no attachment.
        # type is either SOUND or ARC, depending on these conditions:
        # - if value is an attachment of filetypes .mp3, .wav, and .webm,
        #   or if value is a Youtube URL, the type will be SOUND.
        # - otherwise, the type will be ARC.

        # Make sure name is not none.
        if name.isspace() or not name:
            raise ValueError("Key (name) cannot be empty!")

        # First, get the type of entry that has been passed.

        entry_type = "ARC"
        entry_path = None
        entry_value = None

        # Handle case where value is an attachment, a.k.a an image, file, etc.
        if isinstance(value, discord.Attachment):
            
            # Check for sound related files.
            for e in self._sound_extentions:
                if value.filename.endswith(e):
                    entry_type = "SOUND"
                    break
            
            # From here, the type has been set, and we need to save the file.
            try:
                entry_path = await self._file_manager.add_file(value, guild_id)

            # Handle case where the file already exists.
            # Raise an exception that has the entry name as the argument.
            except FileExistsError as e:
                async with self._bot.pool.acquire() as conn:
                    async with conn.cursor() as c:

                        # Find the values associated with the path.
                        execute_input = (rf"SELECT * FROM {guild_table} "
                                         r"WHERE (type='ARC' OR type='SOUND') AND path=(?)")
                        await c.execute(execute_input, e.args[0])
                        result = await c.fetchone()
                        await c.close()
                        await conn.close()

                        # Raise an exception, with the found entry as the result.
                        raise FileExistsError(result.name)
        
        # Handle special cases when value is a string.
        else:
            
            # If value doesn't exist, raise error.
            if value.isspace() or not value:
                raise ValueError("Value cannot be empty!")

            entry_value = value

            # Handle Youtube URLs.
            if "youtu.be" in value or "watch?v=" in value:
                print("pretending to handle youtube videos")
                entry_type = "SOUND"
                entry_path = None  # This would be the path of the downloaded youtube video.

        # At this point, everything is ready to be added to the database.

        entry_tuple = entry_type, name, author, entry_value, entry_path
        result = await self._db_manager.insert_db_entry(guild_table, (entry_tuple))
        
        # If the insert fails, then the name is already in use, and cannot be reused.
        if not result:
            try:
                await self._file_manager.remove_file(entry_path)
            except TypeError: # Handling case where no file was saved.
                print("gay")
                pass
            raise FileExistsError(name)


    # Remove an entry, given a name, author, and guild_id.
    # If the author is not the owner of the entry, return None.
    # Else, remove the entry, and return the file as a string or a discord.File object.
    # If override is true, remove the entry regardless of ownership.
    async def remove_entry(self, name : str, author : str, guild_id, override=False):
        pass

    # Get an entry, given a name and guild_id.
    # TODO:  IMPLEMENT SUGGESTIONS
    # Returns either a discord.File object, or a string.
    async def get_entry(self, name : str, guild_id):
        pass