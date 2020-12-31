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

async def db_query(r_obj, query_name):
    queries = {"test":'''SELECT * FROM base WHERE "ID" IN (1,2) ''', "test2":'''SELECT * FROM base WHERE "ID"=3 '''} # todo: Redis
    return [{k:v for k,v in item.items()} for item in await r_obj.fetch_rows(queries[query_name])] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]

async def form2DB(payload, request):
    db_data = {"DB":{"Query":None, "Result":None}}
    if 'query_name' in payload['form_data'] or 'init_query' in payload['query_params']:
        db_data["DB"]["Query"] = payload['form_data']['query_name'] if 'query_name' in payload['form_data'] else payload['query_params']['init_query']
        db_data["DB"]["Result"] = await db_query(r_obj=request.app.state.db, query_name=db_data["DB"]["Query"])
    return db_data