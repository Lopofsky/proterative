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

    async def multi_statements_query_execution(self, queries: list):
        if not self._connection_pool: await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            results = []
            for query in queries:
                try: results.append(await self.con.fetch(query))
                except Exception as e: 
                    self._connection_pool.release(self.con)
                    raise e
            await self._connection_pool.release(self.con)
            return results

async def db_query(r_obj, query_name, External, MultiQueries=False):
    queries = {
        "test":{
            "query":'''SELECT * FROM base WHERE "ID" IN (1,2); ''', 
            "metadata": {"Esoteric":0}
        }, 
        "test2":{
            "query":'''SELECT * FROM base WHERE "ID"=3; ''', 
            "metadata": {}
        },
        "check_if_users_table_exist": {
            "query":''' SELECT EXISTS (SELECT FROM information_schema.tables WHERE  table_schema = 'public' AND table_name = 'Users'); ''', 
            "metadata": {"Esoteric":1}
        },
        "create_users_db": {
            "query": [''' DROP TABLE IF EXISTS "Users"; ''', ''' DROP SEQUENCE IF EXISTS "Users_ID_seq"; ''', ''' CREATE SEQUENCE "Users_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; ''', 
                '''CREATE TABLE IF NOT EXISTS "public"."Users" (
                    "ID" integer DEFAULT nextval('"Users_ID_seq"') NOT NULL,
                    "username" text NOT NULL,
                    "password" text NOT NULL,
                    "roles" jsonb,
                    "metadata" jsonb
                ) WITH (oids = false); '''],
            "metadata": {"Esoteric":1}
        }
    } # todo: Redis
    allowed_external_queries = {k:v for k,v in queries.items() if 'metadata' not in v or 'Esoteric' not in v['metadata'] or v['metadata']['Esoteric'] == 0}
    if MultiQueries:
        if External: return [{k:v for k,v in rec.items()} for results in await r_obj.multi_statements_query_execution(allowed_external_queries[query_name]["query"]) for rec in results ] if query_name in allowed_external_queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]
        else: return [{k:v for k,v in rec.items()} for results in await r_obj.multi_statements_query_execution(queries[query_name]["query"]) for rec in results ] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]
    else:
        if External: return [{k:v for k,v in item.items()} for item in await r_obj.fetch_rows(allowed_external_queries[query_name]["query"])] if query_name in allowed_external_queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]
        else: return [{k:v for k,v in item.items()} for item in await r_obj.fetch_rows(queries[query_name]["query"])] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]

async def frontEnd2DB(payload, request):
    db_data = {"DB":{"Queries":[], "Results":[]}}
    if 'query_names' in payload['form_data'] or 'init_query' in payload['query_params']:
        db_data["DB"]["Queries"] = payload['form_data']['query_names'].split(',') if 'query_names' in payload['form_data'] else payload['query_params']['init_query'].split(',')
        db_data["DB"]["Queries"] = [x.strip() for x in db_data["DB"]["Queries"]]
        db_data["DB"]["Results"] = [await db_query(r_obj=request.app.state.db, query_name=a_query, External=True) for a_query in db_data["DB"]["Queries"]]
    return db_data

async def checkIfUsersTableExist(db_conn):
    result = await db_query(r_obj=db_conn, query_name="check_if_users_table_exist", External=False)
    return result[0]['exists']

async def createUsersDB(db_conn):
    await db_query(r_obj=db_conn, query_name="create_users_db", External=False, MultiQueries=True)