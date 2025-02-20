from os import name as os_name, environ
from os.path import dirname, realpath, join as FS_join

FS = {"nt": "\\"}.get(os_name, "/")

BASE_DIR = dirname(dirname(realpath(__file__)))
templates_dir = FS_join(BASE_DIR, "decoration", "templates")
static_dir = FS_join(BASE_DIR, "decoration", "static")

SESSION_MAX_AGE = 86400
CORS_MAX_AGE = 120

WHERE_AM_I = (
    environ["WHERE_AM_I"]
    if environ.get("WHERE_AM_I", None) not in ("", None)
    else "PRODUCTION"
)
SESSION_SECRET = environ.get("SESSION_SECRET")
UPLOADS_PATH = environ["UPLOADS_PATH"].replace('"', "").replace("'", "")
COOKIE_SECRET = environ.get("COOKIE_SECRET")
CSRF_SECRET = environ.get("CSRF_SECRET")

SUB_PATH = "templates"
ERROR_PAGE = "404"
FORBIDDEN_DB_STRINGS = [";", "--"]
PATH_EXCEPTIONS, EXCEPTIONS = ["forbidden"], ["favicon.ico"]
INCOMPATIBLE_HTML_PATHS = ("/", "\\") + tuple(PATH_EXCEPTIONS)
RESERVED_KEYWORDS = {"form_data": "query_names"}
MODULE_2_IMPORT = "routers"

DO_YOU_WANT_USERS = bool(environ.get("DO_YOU_WANT_USERS", "False") == "True")

JWT_OPTIONS = {
    "verify_signature": True,
    "verify_exp": True,
    "verify_nbf": False,
    "verify_iat": True,
    "verify_aud": False,
}
ENDPOINT_KEYS_FROM_DB = [
    "init_query",
    "validators",
    "roles",
    "GET",
    "POST"
]
MULTI_QUERY_EXC = "cannot insert multiple commands into a prepared statement"
VALID_DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]

html_elements_to_convert = {
    "css": {
        "lines": [],
        "replace": [
            {
                "from": '<link href="',
                "to": """<link href="{{url_for('static', path='""",
            },
            {
                "from": '.css"',
                "to": '''.css') }}"''',
            },
        ],
    },
    "js": {
        "lines": [],
        "replace": [
            {
                "from": '<script src="',
                "to": """<script src="{{url_for('static', path='""",
            },
            {
                "from": '.js"',
                "to": '''.js') }}"''',
            },
        ],
    },
    "href": {"lines": []},
}
