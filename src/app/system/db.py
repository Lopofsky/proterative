# SOURCE: https://github.com/tiangolo/fastapi/issues/1800
# #2: https://github.com/encode/starlette/issues/658
# from collections import defaultdict, deque
from asyncpg import create_pool
from json import loads
from os import environ
from re import findall
from inspect import iscoroutinefunction
from urllib.parse import quote as urllib_quote
from contextlib import asynccontextmanager
from urllib.parse import unquote
from copy import deepcopy

from app.system.sql_queries import DBQueries
from app.system.utilities import text_san, date_checker, to_json
from app.system.constants import (
    FORBIDDEN_DB_STRINGS,
)

class Database:
    def __init__(self):
        self.db = {
            "MAIN_DB": {
                k.replace("POSTGRES_", ""): environ[k]
                for k in [
                    "POSTGRES_USER",
                    "POSTGRES_PASSWORD",
                    "POSTGRES_SERVER",
                    "POSTGRES_DB",
                    "POSTGRES_PORT",
                ]
            }
        }
        if "EXTRA_DBS" in environ:
            dbs = environ["EXTRA_DBS"].split("|")
            for adb in dbs:
                try:
                    db_name = findall(r"^\^(.*)\^", adb)[0]
                    if db_name.find("^") >= 0:
                        db_name = db_name[: db_name.find("^")]
                    self.db.update({db_name: adb[len(db_name) + 2 :]})
                except IndexError:
                    pass
        self._cursor, self._connection_pool, self._con = None, None, None
        self._cursor_2nd, self._connection_pool_2nd, self._con_2nd = None, None, None
        self.DBQueries = deepcopy(DBQueries)

    async def connect(self, custom_DB=None):
        if not self._connection_pool:
            try:
                self._connection_pool = await create_pool(
                    min_size=1,
                    max_size=10,
                    command_timeout=60,
                    host=self.db["MAIN_DB"]["SERVER"],
                    port=self.db["MAIN_DB"]["PORT"],
                    user=self.db["MAIN_DB"]["USER"],
                    password=self.db["MAIN_DB"]["PASSWORD"],
                    database=self.db["MAIN_DB"]["DB"],
                )
            except Exception as e:
                raise Exception("@MAIN_DB POOL CONNECTION ERROR: " + str(e))

        if not self._connection_pool_2nd:
            try:
                self._connection_pool_2nd = {}
                for adb, dsn in self.db.items():
                    if isinstance(dsn, str):
                        dsn = dsn.replace("#", urllib_quote("#"))
                    if adb != "MAIN_DB":
                        self._connection_pool_2nd[adb] = await create_pool(
                            min_size=1,
                            max_size=10,
                            command_timeout=60,
                            dsn=dsn,
                        )
            except Exception as e:
                raise Exception(
                    "@MASSIVE EXTRA_DBS POOL CONNECTIONS - ERROR: " + str(e)
                )
    

    @asynccontextmanager
    async def get_connection(self, pool_name):
        mapping = {
            True: {pool_name: self._connection_pool},
            False: self._connection_pool_2nd
        }
        connection_pool = mapping[pool_name == "MAIN_DB"][pool_name]
        if connection_pool in [False, None]:
            await self.connect()
            connection_pool = mapping[pool_name == "MAIN_DB"][pool_name]

        conn = await connection_pool.acquire()
        try:
            yield conn
        finally:
            await connection_pool.release(conn)

    async def fetch_rows(self, queries, pool=None, multiple_queries_splitter=";"):
        # Make a copy if its a list:
        queries = [*queries] if isinstance(queries, list) else [queries]
        pool = pool if pool is not None else {"MAIN_DB":{}}
        results = []

        for db_pool in pool.keys():
            async with self.get_connection(db_pool) as con:
                async with con.transaction():
                    for query in queries:
                        sub_queries = [query]
                        if multiple_queries_splitter in query:
                            sub_queries = [
                                sub_query
                                for sub_query in query.split(multiple_queries_splitter)
                                if len(sub_query) > 0
                            ]
                        
                        for sub_query in sub_queries:
                            try:
                                query_result = await con.fetch(sub_query)
                                if db_pool != "MAIN_DB":
                                    query_result = {db_pool: query_result}
                                results.append(query_result)
                            except Exception as e:
                                raise Exception(f"""
                                    {str(e)}
                                    |>THE SUB_QUERY->|
                                    {str(sub_query)}
                                """)
        return results

DB = Database()


async def check_type(the_type, subject):
    async def text_san_local(x, forbidden_s=FORBIDDEN_DB_STRINGS):
        return await text_san(x, forbidden_s)

    types = {
        "int": {"convertor": int, "prefix": "", "endfix": ""},
        "float": {"convertor": float, "prefix": "", "endfix": ""},
        "text": {"convertor": text_san_local, "prefix": "'", "endfix": "'"},
        "raw": {"convertor": str, "prefix": "", "endfix": ""},
        "json": {
            "convertor": to_json,
            "prefix": "",
            "endfix": "::jsonb",
            None: "NULL::jsonb",
        },
        "date": {"convertor": date_checker, "prefix": "'", "endfix": "'::timestamptz"},
    }

    if the_type not in types.keys():
        raise Exception("We don't Support this Type Yet.")

    f = types[the_type]["convertor"]

    processed = await f(subject) if iscoroutinefunction(f) else f(subject)
    if (
        "none" in str(processed).lower()
        and types[the_type].get(None) is not None
    ):
        return types[the_type][None]

    if isinstance(processed, (int, float)):
        processed = str(processed)

    result = "".join([
        types[the_type]["prefix"], 
        processed, 
        types[the_type]["endfix"]
    ])
    return result


async def _db_query(r_obj, query_name, External, query_payload=None):
    _query_payload = None
    # Make copies:
    queries = deepcopy(r_obj.DBQueries)
    if query_payload is not None:
        _query_payload = deepcopy(query_payload)

    if isinstance(query_name, list) and len(query_name) == 1:
        query_name = query_name[0]

    if _query_payload is not None:
        allowed_types = (
            queries
            .get(query_name, {})
            .get("meta", {})
            .get("Payload", None)
        )
        if allowed_types is not None:
            query_payload_keywords_counter = len(allowed_types.keys())

            for var, condition in _query_payload.items():
                if var in allowed_types.keys():
                    fin_check = await check_type(allowed_types[var], condition)

                    if fin_check is False:
                        raise Exception(f'''
                            Illegal Payload Type -> {str(var)} | {str(condition)}
                        ''')
                    
                    # Can't use format, due to jsonb content within postgres.
                    # i.e. a place holder within brackets: `{{placeholder}}`
                    # Also a postgres jsonb key, like `{a_key}`, for which python's 
                    # `format` is not supposed to find a substitude, within 
                    # `_query_payload`.
                    queries[query_name]["Query"] = queries[query_name]["Query"].replace(
                        ''.join(['{', var, '}']), 
                        fin_check
                    )

                    query_payload_keywords_counter -= 1
            
            if query_payload_keywords_counter != 0:
                raise Exception(f"""
                    Payload was not complete!
                    {query_name=}
                    {query_payload_keywords_counter=}
                    {_query_payload=}
                    {allowed_types=}
                """)

    if External:
        allowed_external_queries = {
            k: v
            for k, v in queries.items()
            if v.get("meta", {}).get("External", 0) == 1
        }

        if query_name in allowed_external_queries:
            query_data = allowed_external_queries[query_name]
            db_data = await r_obj.fetch_rows(
                queries=query_data["Query"], 
                pool=query_data["meta"].get("DB", None)
            )
            
            if isinstance(db_data[0], list):
                return [
                    {k: v for k, v in rec.items()}
                    for results in db_data
                    for rec in results
                ]
            elif isinstance(db_data[0], dict):
                return {
                    DB: [{k: v for k, v in rec.items()} for rec in dbr]
                    for results in db_data
                    for DB, dbr in results.items()
                }
            else:
                raise Exception("UNKNOWN RETURN RESULTS FROM DB QUERIES!")
        
        return [
            {
                "Requested Query": str(query_name),
                "Result": "Error! Query Name Not Found ~OR~ Not Allowed to be Exposed Externally!.",
            }
        ]
    else:
        if query_name in queries:
            db_data = await r_obj.fetch_rows(
                queries=queries[query_name]["Query"],
                pool=queries[query_name].get("DB", None)
            )

            return [
                {k: v for k, v in rec.items()} 
                for results in db_data 
                for rec in results
            ]
        return [{
            "Requested Query": str(query_name),
            "Result": "Error! Query Name Not Found.",
        }]


async def Query_DB(
    payload, 
    request=None, 
    init_query=None, 
    server_side=False
):
    db_data = {"DB": {
        "Queries": [], 
        "Results": [], 
        "query_payload": None
    }}
    Query_Obj = request.app.state.db if request is not None else DB

    if isinstance(init_query, str):
        init_query = [init_query]

    if (
        server_side and 
        isinstance(init_query, list) and 
        init_query[0] is not None
    ):
        db_data["DB"]["Queries"].append(init_query)
        # Make a copy
        db_data["DB"]["query_payload"] = deepcopy(payload)
        db_data["DB"]["Results"] = {
            init_query[0]: await _db_query(
                r_obj=Query_Obj,
                query_name=init_query,
                External=False,
                query_payload=db_data["DB"]["query_payload"],
            )
        }
        return db_data
    

    DB_query_payload_resources = [
        {'key': 'init_query', 'container': 'query_params'},
        {'key': 'query_names', 'container': 'form_data'},
    ]
    process_POST_GET = any([
        combo['key'] in payload[combo['container']] 
        for combo in DB_query_payload_resources
    ])

    if init_query is not None:
        db_data["DB"]["Queries"] += init_query
        for combo in DB_query_payload_resources:
            temp_query_payload = {
                k: v
                for k, v in payload[combo['container']].items()
                if k != combo['key'] and not k.startswith("-")
            }
            if db_data["DB"].get("query_payload") is None:
                db_data["DB"]["query_payload"] = temp_query_payload
            else:
                db_data["DB"]["query_payload"].update(temp_query_payload)

    if process_POST_GET:
        for combo in DB_query_payload_resources:
            if combo['key'] in payload[combo['container']]:
                ele = payload[combo['container']][combo['key']]
                if isinstance(ele, list):
                    ele = ele[0]
                ele = unquote(ele)
                for rep in ["'", '"']:
                    ele = ele.replace(rep, '')
                db_data["DB"]["Queries"] += ele.split(",")

                temp_query_payload = {
                    k: v
                    for k, v in payload[combo['container']].items()
                    if k != combo['key'] and not k.startswith("-")
                }
                if db_data["DB"].get("query_payload") is None:
                    db_data["DB"]["query_payload"] = temp_query_payload
                else:
                    db_data["DB"]["query_payload"].update(temp_query_payload)
                    
    # aka init_query==None AND process_POST_GET==False
    if len(db_data["DB"]["Queries"]) == 0:
        return db_data

    db_data["DB"]["Results"] = {}
    db_data["DB"]["Queries"] = [x.strip() for x in db_data["DB"]["Queries"]]
    # The dict's value is a FIFO list. Since the `init_queries` will always 
    # be added first, we want the per endpoint (or request) queries that end
    # up last on the list, to get executed first, so that the `init_queries` 
    # will have the latest data.
    # tl;dr: we need LIFO db query execution order.
    db_data["DB"]["Queries"].reverse()
    for a_query in db_data["DB"]["Queries"]:
        # 
        # NOT HERE 
        # 
        query_result = await _db_query(
            r_obj=Query_Obj,
            query_name=a_query,
            External=True,
            query_payload=db_data["DB"]["query_payload"],
        )
        
        # Error handling takes place here, not within db inner functions:
        match query_result:
            case [{'Result': value, **rest}] if (
                isinstance(value, str) and 
                'error' in value.lower()
            ):
                raise Exception(value)
                
        db_data["DB"]["Results"][a_query] = query_result
    #
    # NOT HERE
    #
    return db_data


async def generate_basic_DB_tables(
    db_conn,
    do_you_want_users,
    active_endpoints,
    endpoints=None
):
    results = (
        await _db_query(
            r_obj=db_conn,
            query_name="check_if_basic_DB_tables_exist",
            External=False,
        )
    )[0]

    if not isinstance(results, dict):
        raise Exception(f"{type(results)=} should be a dict!")

    if not results["DBQueries"]:
        await _db_query(
            r_obj=db_conn, 
            query_name="create_DBQueries_table", 
            External=False
        )

    if do_you_want_users is True:
        actions = {
            "Users": "create_users_table",
            "Sessions": "create_sessions_table",
            "Endpoints": "create_endpoints_table",
        }
        for _table, _query in actions.items():
            if not results[_table]:
                await _db_query(
                    r_obj=db_conn, 
                    query_name=_query, 
                    External=False
                )
        
        if None not in [endpoints, active_endpoints]:
            await populate_endpoints_DB_table(db_conn, active_endpoints, endpoints)


async def reload_all_queries(db_conn):
    all_queries = await _db_query(
        r_obj=db_conn, 
        query_name="load_all_DBQueries", 
        External=False
    )
    db_conn.DBQueries.update(
        {
            query["Name"]: {
                "Query": query["Query"],
                "meta": loads(query["meta"]) if "meta" in query else {},
            }
            for query in all_queries
        }
    )


async def populate_endpoints_DB_table(db_conn, active_endpoints, endpoints):
    query_payload = {}
    for a_endpoint, renderer_type in active_endpoints.items():
        query_name = None
        if a_endpoint not in endpoints.available.keys():
            query_name = "populate_endpoints"
            query_payload = {
                "endpoint": a_endpoint,
                "roles": {},
                "meta": {"renderer_type": renderer_type},
            }
        elif endpoints.available[a_endpoint]["meta"]["renderer_type"] != renderer_type:
            endpoints.available[a_endpoint]["meta"]["renderer_type"] = renderer_type
            query_name = "update_endpoints"
            query_payload = {
                "ID": endpoints.available[a_endpoint]["ID"],
                "meta": endpoints.available[a_endpoint]["meta"],
            }
        
        if query_name is not None:
            await _db_query(
                r_obj=db_conn,
                query_name=query_name,
                External=False,
                query_payload=query_payload,
            )