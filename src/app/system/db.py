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

    async def fetch_rows(self, queries):
        queries, results = queries if type(queries) == list else [queries], []
        if not self._connection_pool: await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            for query in queries:
                try: results.append(await self.con.fetch(query))
                except Exception as e: 
                    self._connection_pool.release(self.con)
                    raise e
            await self._connection_pool.release(self.con)
            return results

async def db_query(r_obj, query_name, External):
    queries = {
        "test":{
            "query":'''SELECT * FROM base WHERE "ID" IN (1,2); ''', 
            "metadata": {"External":1}
        }, 
        "test2":{
            "query":'''SELECT * FROM base WHERE "ID"=3; ''', 
            "metadata": {"External":1}
        },
        "check_if_users_privileges_tables_exist": {
            "query":''' SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'Users') AS "Users", EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'Privileges') AS "Privileges"; '''
        },
        "create_users_table": {
            "query": [''' DROP TABLE IF EXISTS "Users"; ''', ''' DROP SEQUENCE IF EXISTS "Users_ID_seq"; ''', ''' CREATE SEQUENCE "Users_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; ''', 
                '''CREATE TABLE IF NOT EXISTS "public"."Users" (
                    "ID" integer DEFAULT nextval('"Users_ID_seq"') NOT NULL,
                    "username" text NOT NULL,
                    "password" text NOT NULL,
                    "roles" jsonb,
                    "metadata" jsonb
                ) WITH (oids = false); '''],
            "metadata": {}
        },
        "create_privileges_table": { # TODO
            "query": [''' DROP TABLE IF EXISTS "Privileges"; ''', ''' DROP SEQUENCE IF EXISTS "Privileges_ID_seq"; ''', ''' CREATE SEQUENCE "Privileges_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; ''', 
                '''CREATE TABLE IF NOT EXISTS "public"."Privileges" (
                    "ID" integer DEFAULT nextval('"Privileges_ID_seq"') NOT NULL,
                    "username" text NOT NULL,
                    "password" text NOT NULL,
                    "roles" jsonb,
                    "metadata" jsonb
                ) WITH (oids = false); '''],
            "metadata": {"External":0}
        },
        "create_DB_queries_table":{ # TODO
            "query":[''' DROP TABLE IF EXISTS "DBQueries"; ''', ''' DROP SEQUENCE IF EXISTS "DBQueries"; ''', ''' CREATE SEQUENCE "DBQueries_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; ''', 
            ''' CREATE TABLE IF NOT EXISTS "public"."DBQueries" ( '''],
            "metadata": {"External":0}
        }
    } # todo: Redis
    allowed_external_queries = {k:v for k,v in queries.items() if 'metadata' in v and 'External' in v['metadata'] and v['metadata']['External'] == 1}
    if External: return [{k:v for k,v in rec.items()} for results in await r_obj.fetch_rows(allowed_external_queries[query_name]["query"]) for rec in results ] if query_name in allowed_external_queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found ~OR~ Not Allowed to be Exposed Externally!."}]
    else: return [{k:v for k,v in rec.items()} for results in await r_obj.fetch_rows(queries[query_name]["query"]) for rec in results ] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]

async def front_End_2DB(payload, request):
    db_data = {"DB":{"Queries":[], "Results":[]}}
    if 'query_names' in payload['form_data'] or 'init_query' in payload['query_params']:
        db_data["DB"]["Queries"] = payload['form_data']['query_names'].split(',') if 'query_names' in payload['form_data'] else payload['query_params']['init_query'].split(',')
        db_data["DB"]["Queries"] = [x.strip() for x in db_data["DB"]["Queries"]]
        db_data["DB"]["Results"] = [await db_query(r_obj=request.app.state.db, query_name=a_query, External=True) for a_query in db_data["DB"]["Queries"]]
    return db_data

async def generate_users_privileges_tables(db_conn):
    results = (await db_query(r_obj=db_conn, query_name="check_if_users_privileges_tables_exist", External=False))[0]
    if not results['Users']: await db_query(r_obj=db_conn, query_name="create_users_table", External=False)
    if not results['Privileges']: await db_query(r_obj=db_conn, query_name="create_privileges_table", External=False)