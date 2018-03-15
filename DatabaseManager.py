import aioodbc


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
    #  but not modify it.  Useful if a connection needs to be reused.
    @property
    def pool(self):
        return self._pool

    # Returns the name format the manager uses for guild tables.
    def get_table_name(self, guild_id):
        return self._table_format.format(guild_id)

    # Create the database pool to get connections from.
    # Takes an async loop, in this case, from a discord bot.
    async def init_db(self, loop):
        dsn = rf'DRIVER={self._driver};DATABASE={self._database}'
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
                         "author TEXT, "  # The author of the entry
                         "value TEXT, "  # The value of the entry.
                         "path TEXT)")  # The path for the entry.  Optional.
        await c.execute(execute_input)

        # Add default entries to the table.
        defaults = self.get_default_entries()
        for args in defaults:
            entry = (f"INSERT INTO {table_name}"
                     f"(type, name, author, value, path) VALUES (?, ?, ?, ?, ?)")
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
        dice_entry = (r"RNG", r"", r"", r"3d6", r"")
        return [dice_entry]
