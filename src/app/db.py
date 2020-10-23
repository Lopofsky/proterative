# SOURCE: https://github.com/tiangolo/fastapi/issues/1800
import asyncpg
import os 

class Database:
    def __init__(self):
        self.db = {k.replace('POSTGRES_', ''):os.environ[k] for k in ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_SERVER', 'POSTGRES_DB', 'POSTGRES_PORT']}
        self._cursor, self._connection_pool, self.con = None, None, None

    async def connect(self):
        if not self._connection_pool:
            try: self._connection_pool = await asyncpg.create_pool(min_size=1, max_size=10, command_timeout=60, host=self.db['SERVER'], port=self.db['PORT'], user=self.db['USER'], password=self.db['PASSWORD'], database=self.db['DB'],)
            except Exception as e: raise e

    async def fetch_rows(self, query: str):
        if not self._connection_pool: await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            try: return await self.con.fetch(query)
            except Exception as e: raise e
            finally: await self._connection_pool.release(self.con)
