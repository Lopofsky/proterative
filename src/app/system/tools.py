from starlette.responses import FileResponse
from starlette.templating import Jinja2Templates
from inspect import getmembers, isfunction
from copy import deepcopy as dc
from pathlib import Path
from shutil import copyfileobj
from urllib import parse as html_dec
from glob import glob
from importlib import import_module
from os.path import basename, isfile, join
from os import chdir, listdir, walk

from app.system.db import (
    generate_basic_DB_tables,
    reload_all_queries,
    Query_DB,
    populate_endpoints_DB_table
)

from app.system.utilities import (
    convert_your_html_files, text_san, path_san
)
from app.system.constants import (
    FS, BASE_DIR, static_dir, SUB_PATH, UPLOADS_PATH,
    WHERE_AM_I, MODULE_2_IMPORT, INCOMPATIBLE_HTML_PATHS, 
    DO_YOU_WANT_USERS
)
from app.system import jinja_filters
from app.system.constants import (
    templates_dir
)


templates = Jinja2Templates(directory=templates_dir)
templates.env.add_extension("jinja2.ext.do")
templates.env.enable_async = True
# Disable caching by setting auto_reload to True
templates.env.auto_reload = True
custom_jinja_filters = {
    f[0]: f[1]
    for f in getmembers(jinja_filters, isfunction)
}
templates.env.filters.update(custom_jinja_filters)


async def utility_initializers():
    await convert_your_html_files(static_dir, WHERE_AM_I)


async def re_eval(validators, payload_, return_result=False):
    forbidden_s = ["from", "import", "exec", "eval", "__"]
    payload = dc(payload_)

    async def conditioning(validators, payload=payload):
        if validators is None:
            return True
        valid_conditions = False
        if isinstance(validators, str):
            validators = [validators]
        for x in validators:
            try:
                valid_conditions += int(
                    eval(
                        await text_san(x, forbidden_s),
                        locals(),
                        {"__builtins__": {}}
                    )
                )
            except:
                pass
        if valid_conditions != len(validators):
            return False
        return True

    if return_result:
        if isinstance(validators, dict):
            evaluated_result = {}
            for val, check in validators.items():
                cc = await conditioning(check, payload)
                if cc:
                    try:
                        result = eval(
                            await text_san(val, forbidden_s),
                            locals(),
                            {"__builtins__": {}},
                        )
                        if isinstance(result, dict):
                            evaluated_result.update(result)
                        else:
                            raise Exception("Evalution Failed #2!")
                    except:
                        raise Exception("Evalution Failed #1!")
            return evaluated_result
    else:
        return await conditioning(validators)


async def discovered_endpoints(_py_render, _html_templates):
    endpoints = {x.replace("_main", ""): "py" for x in _py_render.keys()}
    endpoints.update(
        {
            path + x.replace(".html", ""): "html"
            for path, end in _html_templates.items()
            for x in end
            if x.replace(".html", "") not in endpoints.keys()
        }
    )
    return endpoints


async def load_all():
    modules = glob(join(BASE_DIR+FS+MODULE_2_IMPORT, "*.py"))
    __all__ = [
        basename(f)[:-3]
        for f in modules
        if isfile(f) and not f.endswith("__init__.py")
    ]
    module_name_prefix = ""
    try:
        all_modules = [
            import_module(f"{MODULE_2_IMPORT}.{i}") 
            for i in __all__
        ]
    except ModuleNotFoundError:
        # if getcwd().find(module_2_import) >= 0:
        #     chdir('..')
        module_name_prefix = "app."
        all_modules = [
            import_module(f"{module_name_prefix}{MODULE_2_IMPORT}.{i}") 
            for i in __all__
        ]
        # raise e
    names = {
        (m.__name__, x): m
        for m in all_modules
        for x in m.__dict__
        if x == "main"
    }

    globals_dict = {}
    for module_meta, module_data in names.items():
        file_module_name_pos = len(MODULE_2_IMPORT) + \
            len(module_name_prefix) + 1
        module_func_name = f"{module_meta[0][file_module_name_pos:]}_{module_meta[1]}"
        main_func_body = getattr(module_data, module_meta[1])
        globals_dict[module_func_name] = main_func_body

    py_renders = {str(x): y for x, y in globals_dict.items()}
    base_path = templates_dir.replace(SUB_PATH, "")
    chdir(base_path)

    html_templates = {
        "/".join([path_san(dirpath), a_dir]) + "/": [
            a_file
            for a_file in listdir(f"{base_path}{dirpath}/{a_dir}/")
            if (
                a_file.endswith(".html")
                and not a_dir.startswith(INCOMPATIBLE_HTML_PATHS)
            )
        ]
        for (dirpath, dirnames, filenames) in walk(SUB_PATH)
        for a_dir in dirnames
        if not (
            path_san(dirpath).startswith(INCOMPATIBLE_HTML_PATHS)
            if path_san(dirpath, True)[0].strip() != "/"
            else path_san(dirpath)[1:].startswith(INCOMPATIBLE_HTML_PATHS)
        )
    }
    html_templates[""] = [f for f in listdir(SUB_PATH) if f.endswith(".html")]
    html_templates = {
        k if not k.startswith(INCOMPATIBLE_HTML_PATHS) else k[1:]: v
        for k, v in html_templates.items()
    }
    globals_dict["html_templates"] = html_templates
    return py_renders, html_templates


async def basic_DB_tables(
    _py_renders, _html_templates, db_conn,
    _endpoints, reload_all_DBQueries=False
):
    active_endpoints = await discovered_endpoints(_py_renders, _html_templates)
    if reload_all_DBQueries is False:
        await generate_basic_DB_tables(
            db_conn=db_conn,
            do_you_want_users=DO_YOU_WANT_USERS,
            active_endpoints=active_endpoints,
            endpoints=_endpoints
        )
    else:
        await reload_all_queries(db_conn=db_conn)

    if None not in [_endpoints, active_endpoints]:
        await populate_endpoints_DB_table(db_conn, active_endpoints, _endpoints)

    await cleanup_deprecated_endpoints(
        _endpoints,
        _py_renders,
        _html_templates
    )


async def cleanup_deprecated_endpoints(
    _endpoints,
    _py_renders,
    _html_templates
):
    _active_endpoints_to_DB = {
        'py': [x.replace('_main', '') for x in _py_renders.keys()],
        'html': [ 
            '/'.join([
                folder.replace('/', ''), a_template
            ]).replace('.html', '')
            for folder, templates in _html_templates.items()
            for a_template in templates
        ],
    }
    _active_endpoints_to_DB['html'] = [
        rec if not rec.startswith('/') else rec[1:]
        for rec in _active_endpoints_to_DB['html']
    ]
    _active_endpoints_to_DB = set(
        _active_endpoints_to_DB['py'] + 
        _active_endpoints_to_DB['html']
    )

    deprecated_db_endpoints = set(
        _endpoints.available.keys()
    ) - _active_endpoints_to_DB
    if len(deprecated_db_endpoints) == 0:
        return False
    
    deprecated_db_endpoints = {
        'deprecated_db_endpoints': 
        f"""{"', '".join(deprecated_db_endpoints)}"""
    }

    result = await Query_DB(
        payload=deprecated_db_endpoints,
        request=None, 
        init_query='remove_deprecated_endpoints',
        server_side=True
    )


async def save_up_files(init_form, keyword="FILEUPLOAD", download=False):
    init_form = init_form
    if download is False:
        # make a copy:
        form = {} | init_form
        for k, v in form.items():
            if keyword in k:
                custom_path = (
                    k[k.find(keyword) + len(keyword):]
                    .replace(".", "")
                    .replace("/", FS)
                )
                path = FS.join([UPLOADS_PATH, custom_path])
                form_name = k[: k.find(keyword)]
                if form_name[-1] == ".":
                    form_name = form_name[:-1]

                Path(path).mkdir(parents=True, exist_ok=True)
                v.file.seek(0)
                init_form.pop(k, None)
                init_form[form_name] = None
                if v.filename != "":
                    with open(path + v.filename, "wb") as buffer:
                        copyfileobj(v.file, buffer)
                    init_form[form_name] = {
                        v.filename: {"path": path,
                                     "content_type": v.content_type}
                    }
        return init_form
    else:
        unquoted_form = {}
        for k, v in init_form.items():
            v_unquoted = html_dec.unquote(v)  # unquote_plus
            if v_unquoted[0] in ["'", '"']:
                v_unquoted = v_unquoted[1:]
            if v_unquoted[-1] in ["'", '"']:
                v_unquoted = v_unquoted[:-1]
            unquoted_form[k] = v_unquoted

        if not all([key in unquoted_form for key in ["uuid", "file"]]):
            # TODO: handle missing file request data
            ...

        fileresponse = FileResponse(
            FS.join([UPLOADS_PATH, unquoted_form["uuid"], unquoted_form["file"]]),
            media_type="application/octet-stream",
            filename=unquoted_form["file"],
        )
        return fileresponse

