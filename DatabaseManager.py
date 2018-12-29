import aioodbc
import time


class DatabaseManager:

    """ Database Manager, mostly separated from Threebot for changeability reasons."""

    # db_args currently only has DRIVER and DATABASE keys.
    # table_format is the format of the name for each guild table,
    #  where {} is used where the server ID should go.
    def __init__(self, db_args):
        self._driver = db_args["DRIVER"]
        self._database = db_args["DATABASE"]
        self._pool = None

    # Allows other scripts to access the database pool,
    #  but not modify it.  Legacy.
    @property
    def pool(self):
        return self._pool

    # Create the database pool to get connections from.
    # Takes an async loop, in this case, from a discord bot.
    async def init_db(self, loop):
        dsn = rf'DRIVER={self._driver};DATABASE={self._database};TIMEOUT=10'
        self._pool = await aioodbc.create_pool(dsn=dsn, loop=loop)