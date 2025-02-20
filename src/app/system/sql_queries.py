DBQueries = {
    "create_DBQueries_table": {  # TODO
        "Query": [
            """ DROP SEQUENCE IF EXISTS "DBQueries_ID_seq"; """,
            """ DROP SEQUENCE IF EXISTS "Endpoints_ID_seq"; """,
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
                    (2, '{}',   'create_endpoints_table',  'DROP SEQUENCE IF EXISTS "Endpoints_ID_seq";
                    CREATE SEQUENCE "Endpoints_ID_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1;
                    CREATE TABLE IF NOT EXISTS "public"."Endpoints" (
                            "ID" integer DEFAULT nextval(''"Endpoints_ID_seq"'') NOT NULL,
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
                    (5, '{"External": 1}', 'test2', 'SELECT * FROM base WHERE "ID"=3;');""",
        ],
        "meta": {"External": 0},
    },
    "load_all_DBQueries": {"Query": """ SELECT * FROM "DBQueries"; """},
    "load_endpoints": {"Query": """ SELECT * FROM "Endpoints"; """},
    "load_users": {"Query": """ SELECT * FROM "Users"; """},
    "load_sessions": {"Query": """ SELECT "ID", metadata AS "m" FROM "Sessions"; """},
    "populate_endpoints": {
        "Query": """ INSERT INTO "Endpoints"("endpoint", "roles", "meta") VALUES({endpoint}, {roles}, {meta}); """,
        "meta": {"Payload": {"endpoint": "text", "roles": "json", "meta": "json"}},
    },
    "update_endpoints": {
        "Query": """ UPDATE "Endpoints" SET "meta" = {meta} WHERE "ID"={ID}; """,
        "meta": {"Payload": {"ID": "int", "meta": "json"}},
    },
    "create_new_user": {
        "Query": """ INSERT INTO "Users" ("username", "password", "roles", "metadata") VALUES({username}, {hashpass}, {roles}, {metadata}); """,
        "meta": {
            "Payload": {
                "username": "text",
                "hashpass": "text",
                "roles": "json",
                "metadata": "json",
            }
        },
    },
    "remove_deprecated_endpoints": {
        "Query": """ DELETE FROM "Endpoints" WHERE endpoint IN ({deprecated_db_endpoints})""",
        "meta": {
            "Payload": {
                "deprecated_db_endpoints": "text",
            }
        }
    }
}

system_db_tables = ["Users", "Endpoints", "DBQueries", "Sessions",]

single_table_tempalte = """
    EXISTS(
        SELECT FROM information_schema.tables WHERE table_schema = 'public' AND 
        table_name = '{0}'
    ) AS "{0}"{1} 
"""

fin_q = """ SELECT """
for i, template_name in enumerate(system_db_tables):
    cte_end = ','
    if i == len(system_db_tables) - 1:
        cte_end = ';'
    fin_q += single_table_tempalte.format(template_name, cte_end)

DBQueries["check_if_basic_DB_tables_exist"] = {"Query": fin_q}