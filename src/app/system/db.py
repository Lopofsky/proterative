# SOURCE: https://github.com/tiangolo/fastapi/issues/1800
import asyncpg, json, time, os, copy

class Database:
    def __init__(self):
        self.db = {k.replace('POSTGRES_', ''):os.environ[k] for k in ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_SERVER', 'POSTGRES_DB', 'POSTGRES_PORT']}
        self._cursor, self._connection_pool, self.con = None, None, None
        self.DBQueries = {
            "check_if_basic_DB_tables_exist":{
                "Query":''' SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'Users') AS "Users", EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'Privileges') AS "Privileges", EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'DBQueries') AS "DBQueries", EXISTS(SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'Sessions') AS "Sessions"; '''
            },
            "create_DBQueries_table":{ # TODO
                "Query":[""" DROP SEQUENCE IF EXISTS "DBQueries_ID_seq"; """,
                    """ DROP SEQUENCE IF EXISTS "Privileges_ID_seq"; """,
                    """ CREATE SEQUENCE "DBQueries_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; """,
                    """ CREATE TABLE IF NOT EXISTS "public"."DBQueries" (
                        "ID" integer DEFAULT nextval('"DBQueries_ID_seq"') NOT NULL,
                        "meta" jsonb NOT NULL,
                        "Name" text,
                        "Query" text
                    ) WITH (oids = false); """,
                    """ INSERT INTO "DBQueries" ("ID", "meta", "Name", "Query") VALUES
                    (1, '{}',  'create_users_table', 'DROP SEQUENCE IF EXISTS "Users_ID_seq";
                    CREATE SEQUENCE "Users_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1; 
                    CREATE TABLE IF NOT EXISTS "public"."Users" (
                            "ID" integer DEFAULT nextval(''"Users_ID_seq"'') NOT NULL,
                            "username" text NOT NULL,
                            "password" text NOT NULL,
                            "roles" jsonb,
                            "metadata" jsonb
                        ) WITH (oids = false);'
                    ),
                    (2, '{}',   'create_privileges_table',  'DROP SEQUENCE IF EXISTS "Privileges_ID_seq";
                    CREATE SEQUENCE "Privileges_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;
                    CREATE TABLE IF NOT EXISTS "public"."Privileges" (
                            "ID" integer DEFAULT nextval(''"Privileges_ID_seq"'') NOT NULL,
                            "endpoint" text NOT NULL,
                            "roles" jsonb NOT NULL,
                            "meta" jsonb NOT NULL
                        ) WITH (oids = false);'
                    ),
                    (3, '{}', 'create_sessions_table', 'DROP SEQUENCE IF EXISTS "Sessions_ID_seq";
                    CREATE SEQUENCE "Sessions_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;
                    CREATE TABLE IF NOT EXISTS "public"."Sessions" (
                            "ID" integer DEFAULT nextval(''"Sessions_ID_seq"'') NOT NULL,
                            "metadata" jsonb NOT NULL
                        ) WITH (oids = false);'
                    ),
                    (4, '{"External": 1}', 'test', 'SELECT * FROM base WHERE "ID" IN (1,2);'),
                    (5, '{"External": 1}', 'test2', 'SELECT * FROM base WHERE "ID"=3;');"""],
                "meta": {"External":0}
            },
            "load_all_DBQueries":{
                "Query":''' SELECT * FROM "DBQueries"; '''
            },
            "load_privileges":{
                "Query":''' SELECT * FROM "Privileges"; '''
            },
            "load_users":{
                "Query":''' SELECT * FROM "Users"; '''
            },
            "load_sessions":{
                "Query":''' SELECT "ID", metadata AS "m" FROM "Sessions"; '''
            },
            "populate_privileges":{
                "Query":''' INSERT INTO "Privileges"("endpoint", "roles", "meta") VALUES({endpoint}, {roles}, {meta}); ''',
                "meta":{"Payload":{"endpoint":"text", "roles":"json", "meta":"json"}}
            },
            "update_privileges":{
                "Query":''' UPDATE "Privileges" SET "meta" = {meta} WHERE "ID"={ID}; ''',
                "meta":{"Payload":{"ID":"int", "meta":"json"}}
            }
        } # todo: Redis

    async def connect(self):
        if not self._connection_pool:
            try: self._connection_pool = await asyncpg.create_pool(min_size=1, max_size=10, command_timeout=60, host=self.db['SERVER'], port=self.db['PORT'], user=self.db['USER'], password=self.db['PASSWORD'], database=self.db['DB'],)
            except Exception as e: raise e

    async def fetch_rows(self, queries, multiple_queries_splitter=";"):
        queries, results = queries if type(queries) == list else [queries], []
        if not self._connection_pool: await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            for query in queries:
                try: results.append(await self.con.fetch(query))
                except Exception as e: 
                    if str(e)=="cannot insert multiple commands into a prepared statement":
                        if query.find(multiple_queries_splitter) >= 0:
                            for sub_query in [x for x in query.split(multiple_queries_splitter) if len(x) > 0]:
                                try: results.append(await self.con.fetch(sub_query))
                                except Exception as e:
                                    await self._connection_pool.release(self.con)
                                    raise Exception(str(e)+"|>THE SUB_QUERY->|"+str(sub_query))
                    else:
                        await self._connection_pool.release(self.con)
                        raise Exception(str(e)+"|>THE QUERY->|"+str(query))
            await self._connection_pool.release(self.con)
            return results

async def check_type(the_type, subject):
    types = {"int":{"convertor":int, "prefix":"", "endfix":""}, "float":{"convertor":float, "prefix":"", "endfix":""}, "text":{"convertor":str, "prefix":"'", "endfix":"'"}, "json":{"convertor":lambda x: json.dumps(x).replace("'", '"'), "prefix":"'", "endfix":"'::jsonb"}}
    if the_type not in types.keys(): raise Exception("We don't Support this Type Yet.")
    else: f = types[the_type]["convertor"]
    try: return types[the_type]['prefix']+str(f(subject))+types[the_type]['endfix']
    except: return False

async def db_query(r_obj, query_name, External, query_payload=None):
    queries = copy.deepcopy(r_obj.DBQueries)
    if query_payload is not None:
        if query_name in queries and 'meta' in queries[query_name] and 'Payload' in queries[query_name]['meta']:
            allowed_types = queries[query_name]['meta']['Payload']
            for var, cont in query_payload.items():
                if var in allowed_types.keys():
                    fin_check = await check_type(allowed_types[var], cont)
                    if fin_check is False: raise Exception("Illegal Payload Type -> "+str(var))
                    queries[query_name]["Query"] = queries[query_name]["Query"].replace("{"+var+"}", fin_check)
                else: raise Exception("Unknown Keyword in Payload.")
        else: pass # Why the dev provided this query with a payload? Deprecated query maybe? -> todo handling: notification.
    if External: 
        allowed_external_queries = {k:v for k,v in queries.items() if 'meta' in v and 'External' in v['meta'] and v['meta']['External'] == 1}
        return [{k:v for k,v in rec.items()} for results in await r_obj.fetch_rows(allowed_external_queries[query_name]["Query"]) for rec in results ] if query_name in allowed_external_queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found ~OR~ Not Allowed to be Exposed Externally!."}]
    else: return [{k:v for k,v in rec.items()} for results in await r_obj.fetch_rows(queries[query_name]["Query"]) for rec in results ] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]

async def front_End_2DB(payload, request):
    db_data = {"DB":{"Queries":[], "Results":[]}}
    if 'query_names' in payload['form_data'] or 'init_query' in payload['query_params']:
        db_data["DB"]["Queries"] = payload['form_data']['query_names'].split(',') if 'query_names' in payload['form_data'] else payload['query_params']['init_query'].split(',')
        db_data["DB"]["Queries"] = [x.strip() for x in db_data["DB"]["Queries"]]
        db_data["DB"]["Results"] = [await db_query(r_obj=request.app.state.db, query_name=a_query, External=True) for a_query in db_data["DB"]["Queries"]]
    return db_data

async def generate_basic_DB_tables(db_conn, do_you_want_users, endpoints, privileges=None, reload_Queries=False):
    results = (await db_query(r_obj=db_conn, query_name="check_if_basic_DB_tables_exist", External=False))[0]
    if not results['DBQueries']: await db_query(r_obj=db_conn, query_name="create_DBQueries_table", External=False)
    all_queries = await db_query(r_obj=db_conn, query_name="load_all_DBQueries", External=False)
    db_conn.DBQueries.update({query["Name"]:{"Query":query["Query"], "meta":json.loads(query["meta"]) if "meta" in query else {}} for query in all_queries})
    if do_you_want_users == True:
        if not results['Users']: await db_query(r_obj=db_conn, query_name="create_users_table", External=False)
        if not results['Privileges']: await db_query(r_obj=db_conn, query_name="create_privileges_table", External=False)
        if not results['Sessions']: await db_query(r_obj=db_conn, query_name="create_sessions_table", External=False)
        await populate_privileges_DB_table(db_conn, endpoints, privileges)

async def populate_privileges_DB_table(db_conn, endpoints, privileges):
    query_payload = {}
    for endpoint, renderer_type in endpoints.items():
        if endpoint not in privileges.available.keys():
            query_payload = {"endpoint":endpoint, "roles":{}, "meta":{"renderer_type":renderer_type}}
            await db_query(r_obj=db_conn, query_name="populate_privileges", External=False, query_payload=query_payload)
        elif privileges.available[endpoint]['meta']['renderer_type'] != renderer_type:
            query_payload = {"ID":privileges.available[endpoint]["ID"], "meta":{"renderer_type":renderer_type}}
            await db_query(r_obj=db_conn, query_name="update_privileges", External=False, query_payload=query_payload)
        else: pass
