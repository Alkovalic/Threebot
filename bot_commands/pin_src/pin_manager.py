import os
import discord
import youtube_dl
import time

from bot_commands.pin_src import file_manager


class PinManager:

    """ Helper class for pin that handles database transactions and file storage. """

    def __init__(self, pool, output_path):
        self._pool = pool
        self._file_manager = file_manager.FileManager(f"{os.getcwd()}/{output_path}/guild_file_data")
        self._sound_extensions = [".webm", ".mp3", ".wav"]
        self._table_format = "PIN_{}"

    # Returns the name format the manager uses for guild tables.
    def get_table_name(self, guild_id):
        return self._table_format.format(guild_id)

    # MAIN METHODS #

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
        guild_table = self.get_table_name(guild_id)

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
                raise FileExistsError((await self.filter_db_entries(guild_table, e.args[0], "path"))[0].name)
        
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
                    raise FileExistsError((await self.filter_db_entries(guild_table, e.args[0], "path"))[0].name)

            if entry_path:
                entry_type = 'SOUND'

        # At this point, everything is ready to be added to the database.

        entry_tuple = entry_type, name, author, entry_value, entry_path
        result = await self.insert_db_entry(guild_table, (entry_tuple))
        
        # If the insert fails, then the name is already in use, and cannot be reused.
        if not result:
            try:
                await self._file_manager.remove_file(entry_path)
            except TypeError: # Handling case where no file was saved.
                pass
            raise FileExistsError(name)

    # Remove an entry, given a name, author, and guild_id.
    # If the author is not the owner of the entry, raise the error.
    # Else, remove the entry if it exists, and return True or False, depending on whether an entry was removed.
    # If override is true, remove the entry regardless of ownership.
    async def remove_entry(self, name : str, author : str, guild_id, override=False):

        # Check if the name isn't blank.
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # Attempt to remove the given entry.
        guild_table = self.get_table_name(guild_id)
        result = None
        try:
            result = await self.remove_db_entry(guild_table, name, author, override=override)
        except PermissionError as e:  # Here just to show that this error is supposed to happen.
            raise e

        # Handle the case where the entry didn't exist.
        if result is None:
            return False
        
        # From here, something has been removed from the database.
        # Get whatever was removed, remove it from the disk, and send it.
        
        # Handle the case where the entry was a file.
        if result.path:
            return await self._file_manager.remove_file(result.path)

        return True
        

    # Get an entry, given a name and guild_id.
    # Returns either a discord.File object or a string.
    # Returns None when the entry isn't found.
    async def get_entry(self, name : str, guild_id):
        
        if name.isspace() or not name:
            raise ValueError("Name cannot be an empty value!")

        # Get the entry associated with the given name.
        guild_table = self.get_table_name(guild_id)
        details = await self.get_db_entry(guild_table, name)

        # No details found, no entry found.
        if details is None:
            return None

        # If a path exists, open and return it, as long as the file is small enough to upload.
        if details.path:
            # Getting filesize.
            is_oversized = (os.stat(details.path).st_size > 8000000)
            if not is_oversized:
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
        guild_table = self.get_table_name(guild_id)
        details = await self.get_db_entry(guild_table, name)

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
        guild_table = self.get_table_name(guild_id)
        entries = await self.search_db_entries(guild_table, name)

        # Clean up the result to just be a list of strings.

        result = []
        for i in entries:
            result.append(i[0])

        return result

    # DATABASE QUERIES #

    # Creates guild tables for a given guild id.
    # Only creates new tables if the table does not already exist.
    async def add_new_guild_table(self, guild_id):

        # Create the cursor, and the table name.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                table_name = self.get_table_name(guild_id)

                # Check if the table already exists.
                check = await c.tables(table=table_name, tableType='TABLE')
                if check.fetchone():
                    return

                # Create the table.
                execute_input = (rf"CREATE TABLE {table_name}("
                                 "type TEXT, "  # The type of entry.  ie SOUND, ARC, etc
                                 "name TEXT, "  # The name of the entry. 
                                 "authorid TEXT, "  # The authorid of the entry
                                 "value TEXT, "  # The value of the entry.
                                 "path TEXT, "   # The path for the entry.  Optional.
                                 "timestamp REAL)")  # The unix timestap the entry was placed.  Optional.
                await c.execute(execute_input)
                await c.commit()

    # Remove pin table associated with a given guild id.
    async def remove_guild_table(self, guild_id):
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                execute_input = rf"DROP TABLE IF EXISTS {self.get_table_name(guild_id)}"
                await c.execute(execute_input)
                await c.commit()

    # Inserts an entry into the database, given a guild table, and the entry values.
    # Entry values will be a tuple, in the order of:
    #  (type, name, author, value, path), where path is None if no path is needed.
    # Returns True on success, and False on failure.
    # Failure involves the entry already existing.
    async def insert_db_entry(self, table, values):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if the entry exists, and return False if it does.
                if await self.get_db_entry(table, values[1]):
                    return False

                # From here, the entry doesn't already exist, and we can add it.

                execute_input = (rf"INSERT INTO {table} "
                                 rf"(type, name, authorid, value, path, timestamp) VALUES (?, ?, ?, ?, ?, ?)")
                await c.execute(execute_input, (values + (time.time(),)))
                await c.commit()
                return True

    # Removes an entry from the database, given a guild table, and the name of the entry.
    # If override is True, the author check is ignored.
    # Returns the removed entry tuple on success, and None on failure.
    # Failure involves the entry not existing.
    # Raises PermissionError if the author check fails.
    async def remove_db_entry(self, table, name, author, override=False):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if entry exists, and return false if it doesn't.
                check = await self.get_db_entry(table, name)

                if check is None:
                    return None

                # At this point, the entry exists
                # Check if the author is able to remove the entry.
                if check.authorid != str(author) and not override:
                    raise PermissionError(check.authorid)

                # From here, we are able to remove the entry from the database.
                execute_input = (rf"DELETE FROM {table} "
                                 rf"WHERE (type='PIN' or type='SOUND') and name=(?)")
                await c.execute(execute_input, name)
                await c.commit()
                return check

    # Get an entry from the database, given a guild table, and the name of the entry.
    # Returns the entry tuple on success, and None on failure.
    # Failure typically includes the entry not existing.
    async def get_db_entry(self, table, name):

        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
                execute_input = (rf"SELECT * FROM {table} "
                                 rf"WHERE (type='PIN' OR type='SOUND') AND name=(?)")
                await c.execute(execute_input, name)
                result = await c.fetchone()
                return result

    # Returns a list of names similar to a given string.
    # If the string is a single character, return all names starting with that letter.
    async def search_db_entries(self, table, name):
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:
            
                execute_input = (rf"SELECT name FROM {table} "
                                 rf"WHERE name LIKE (?)")

                if name is None:
                    await c.execute(rf"SELECT name FROM {table}")
                elif len(name) == 1:  # Single letter input.
                    await c.execute(execute_input, f"{name}%")
                else:
                    await c.execute(execute_input, f"%{name}%")

                result = await c.fetchall()
                return result

    # Get the entry associated with some provided piece of information.
    # Takes a guild table, the data to search, and the type of the data.
    # For example, getting all entries created by a specific author
    #  would be called as filter_db_entries(<table_id>, "John_Doe", "AUTHOR")
    # As of 07/16/18, the current valid values for the <type> argument are..
    #   - "type"
    #   - "name"
    #   - "authorid"
    #   - "value"
    #   - "path"
    #   - "timestamp"
    # Returns a list of all entries that match the criteria.
    async def filter_db_entries(self, table, data, data_type):

        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Currently, the table and data type are directly inserted into the string.
                # This could cause problems with improper data types being passed,
                #  but it allows this function to remain dynamic.
                # Should raise errors if a wrong type is passed, anyway.

                execute_input = (rf"SELECT * FROM {table} "
                                 rf"WHERE ({data_type}=(?))")
                await c.execute(execute_input, data)
                result = await c.fetchall()
                return result
                

