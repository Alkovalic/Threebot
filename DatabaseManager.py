import aioodbc
import time


class DatabaseManager:

    """ Database Manager, mostly separated from Threebot for changeability reasons."""

    # db_args currently only has DRIVER and DATABASE keys.
    # table_format is the format of the name for each guild table,
    #  where {} is used where the server ID should go.
    def __init__(self, db_args, table_format):
        self._driver = db_args["DRIVER"]
        self._database = db_args["DATABASE"]
        self._pool = None
        self._table_format = table_format

    # Allows other scripts to access the database pool,
    #  but not modify it.  Legacy.
    @property
    def pool(self):
        return self._pool

    # Returns the name format the manager uses for guild tables.
    def get_table_name(self, guild_id):
        return self._table_format.format(guild_id)

    # Create the database pool to get connections from.
    # Takes an async loop, in this case, from a discord bot.
    async def init_db(self, loop):
        dsn = rf'DRIVER={self._driver};DATABASE={self._database};TIMEOUT=10'
        self._pool = await aioodbc.create_pool(dsn=dsn, loop=loop)

    # Creates guild tables for a given guild id.
    # Only creates new tables if the table does not already exist.
    async def add_new_guild_table(self, guild_id, conn):

        # Create the cursor, and the table name.
        c = await conn.cursor()
        table_name = self.get_table_name(guild_id)

        # Check if the table already exists.
        check = await c.tables(table=table_name, tableType='TABLE')
        if check.fetchone():
            return

        # Create the table.
        execute_input = (rf"CREATE TABLE {table_name}("
                         "type TEXT, "  # The type of entry.  ie SOUND, ARC, etc
                         "name TEXT, "  # The name of the entry. 
                         "authorid INT, "  # The authorid of the entry
                         "value TEXT, "  # The value of the entry.
                         "path TEXT, "   # The path for the entry.  Optional.
                         "timestamp REAL)")  # The unix timestap the entry was placed.  Optional.
        await c.execute(execute_input)

        # Add default entries to the table.
        defaults = self.get_default_entries()
        for args in defaults:
            entry = (f"INSERT INTO {table_name}"
                     f"(type, name, authorid, value, path) VALUES (?, ?, ?, ?, ?)")
            await c.execute(entry, args)

        await c.commit()
        await c.close()

    # Remove all guild tables associated with a given guild id.
    async def remove_guild_table(self, guild_id, conn):
        c = await conn.cursor()
        execute_input = rf"DROP TABLE IF EXISTS {self.get_table_name(guild_id)}"
        await c.execute(execute_input)
        await c.commit()
        await c.close()

    # Returns a list of default table entries to put into a new table.
    # Each tuple in the entry is in the following format:
    #  (<type>, <name>, <author>, <value>, <path>)
    def get_default_entries(self):
        dice_entry = (r"RNG", None, None, r"3d6", None)
        return [dice_entry]

    # Inserts an entry into the database, given a guild table, and the entry values.
    # Entry values will be a tuple, in the order of:
    #  (type, name, author, value, path), where path is None if no path is needed.
    # Returns True on success, and False on failure.
    # Failure involves the entry already existing.
    async def insert_db_entry(self, guild_table, values):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if the entry exists, and return False if it does.
                if await self.get_db_entry(guild_table, values[1], cursor=c):
                    #await c.close()
                    #await conn.close()
                    return False

                # From here, the entry doesn't already exist, and we can add it.

                execute_input = (rf"INSERT INTO {guild_table} "
                                 rf"(type, name, authorid, value, path, timestamp) VALUES (?, ?, ?, ?, ?, ?)")
                await c.execute(execute_input, (values + (time.time(),)))
                await c.commit()
                #await c.close()
                #await conn.close()
                return True

    # Removes an entry from the database, given a guild table, and the name of the entry.
    # If override is True, the author check is ignored.
    # Returns the entry tuple on success, and None on failure.
    # Failure involves the entry not existing.
    # Raises PermissionError if the author check fails.
    async def remove_db_entry(self, guild_table, name, author, override=False):

        # Get the connection and cursor.
        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                # Check if entry exists, and return false if it doesn't.
                check = await self.get_db_entry(guild_table, name, cursor=c)

                if check is None:
                    #await c.close()
                    #await conn.close()
                    return None

                # At this point, the entry exists
                # Check if the author is able to remove the entry.
                if check.authorid != author and not override:
                    #await c.close()
                    #await conn.close()
                    raise PermissionError(check.authorid)

                # From here, we are able to remove the entry from the database.
                execute_input = (rf"DELETE FROM {guild_table} "
                                 rf"WHERE (type='PIN' or type='SOUND') and name=(?)")
                await c.execute(execute_input, name)
                await c.commit()
                #await c.close()
                #await conn.close()
                return check

    # Get an entry from the database, given a guild table, and the name of the entry.
    # Returns the entry tuple on success, and None on failure.
    # Failure typically includes the entry not existing.
    async def get_db_entry(self, guild_table, name, cursor=None):

        # Handling case where no db cursor is passed.
        conn = None
        if cursor is None:
            conn = await self._pool.acquire()
            c = await conn.cursor()
        else:
            c = cursor

        # Find the values associated with the name.
        execute_input = (rf"SELECT * FROM {guild_table} "
                         r"WHERE (type='PIN' OR type='SOUND') AND name=(?)")
        await c.execute(execute_input, name)

        # Save the result.  If there's more than one entry, something went wrong.
        result = await c.fetchone()

        # Close connections if we had to make them earlier.
        if conn is not None:
            await c.close()
            await conn.close()

        # Result will be None if no entries were found.
        return result

    # Returns a given number of names similar to a given string.
    #
    async def search_db_entries(self):
        pass

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
    async def filter_db_entries(self, guild_table, data, data_type):

        async with self._pool.acquire() as conn:
            async with conn.cursor() as c:

                #try:
                # Currently, the table and data type are directly inserted into the string.
                # This could cause problems with improper data types being passed,
                #  but it allows this function to remain dynamic.
                # Should raise errors if a wrong type is passed, anyway.

                execute_input = (rf"SELECT * FROM {guild_table} "
                                 rf"WHERE ({data_type}=(?))")
                await c.execute(execute_input, data)
                result = await c.fetchall()
                return result

                #finally:
                #    await c.close()
                #    await conn.close()
                

