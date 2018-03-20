import os
from bot_commands.arc_src import file_manager


class Archive:

    """ Helper class for arc that handles database transactions and file storage. """

    def __init__(self, pool):
        self._pool = pool
        self._file_manager = file_manager.FileManager(os.getcwd() + "\\guild_file_data")

    # PRIMARY METHODS #

    # Add an entry, given a name, author, and value.
    # If value is a discord.Attachment, save the file, and add the entry to the database.
    # If value is a string, just add the entry to the database.
    def add_entry(self):
        pass

    # Remove an entry, given a name, author, and guild_id.
    # If the author is not the owner of the entry, return None.
    # Else, remove the entry, and return the file as a string or a discord.File object.
    # If override is true, remove the entry regardless of ownership.
    def remove_entry(self, name, author, guild_id, override=False):
        pass

    # Get an entry, given a name and guild_id.
    # TODO:  IMPLEMENT SUGGESTIONS
    # Returns either a discord.File object, or a string.
    def get_entry(self, name, guild_id):
        pass

    # HELPER METHODS #

    # Inserts an entry into the database, given a guild table, and the entry values.
    # Entry values will be a tuple, in the order of:
    #  (type, name, author, value, path), where path is None if no path is needed.
    # Returns True on success, and False on failure.
    # Failure involves the entry already existing.
    async def __insert_db_entry(self, guild_table, values):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if the entry exists, and return False if it does.
                if await self.__get_db_entry(guild_table, values[1], cursor=c):
                    await c.close()
                    await conn.close()
                    return False

                # From here, the entry doesn't already exist, and we can add it.

                execute_input = (rf"INSERT INTO {guild_table} "
                                 rf"(type, name, author, value, path) VALUES (?, ?, ?, ?, ?)")
                await c.execute(execute_input, values)
                await c.commit()
                await c.close()
                await conn.close()
                return True

    # Removes an entry from the database, given a guild table, and the name of the entry.
    # If override is True, the author check is ignored.
    # Returns True on success, and False on failure.
    # Failure involves the entry not existing.
    # Raises PermissionError if the author check fails.
    async def __remove_db_entry(self, guild_table, name, author, override=False):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if entry exists, and return false if it doesn't.
                check = await self.__get_db_entry(guild_table, name, cursor=c)

                if check is None:
                    await c.close()
                    await conn.close()
                    return False

                # At this point, the entry exists
                # Check if the author is able to remove the entry.
                if check[2] != author and not override:
                    await c.close()
                    await conn.close()
                    raise PermissionError(f"User {author} is not able to remove entry by {check[2]}")

                # From here, we are able to remove the entry from the database.
                execute_input = (rf"DELETE FROM {guild_table} "
                                 rf"WHERE (type='ARC' or type='SOUND') and name=(?)")
                await c.execute(execute_input, name)
                await c.commit()
                await c.close()
                await conn.close()
                return True

    # Get an entry from the database, given a guild table, and the name of the entry.
    # Returns the entry tuple on success, and None on failure.
    # Failure typically includes the entry not existing.
    async def __get_db_entry(self, guild_table, name, cursor=None):

        # Handling case where no db cursor is passed.
        conn = None
        if cursor is None:
            conn = await self._pool.acquire()
            c = await conn.cursor()
        else:
            c = cursor

        # Find the values associated with the name.
        execute_input = (rf"SELECT * FROM {guild_table} "
                         r"WHERE (type='ARC' OR type='SOUND') AND name=(?)")
        await c.execute(execute_input, name)

        # Save the result.  If there's more than one entry, something went wrong.
        result = await c.fetchone()

        # Close connections if we had to make them earlier.
        if conn is not None:
            await c.close()
            await conn.close()

        # Result will be None if no entries were found.
        return result
