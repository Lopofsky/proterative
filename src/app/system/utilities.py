from starlette.responses import RedirectResponse

from datetime import datetime as dt
from json import dumps, loads, JSONDecodeError
from os import walk
from re import search

from app.system.constants import (
    FS,
    VALID_DATE_FORMATS,
    SUB_PATH,
    html_elements_to_convert as html2c,
)


def GET_Redirect(url: str):
    if not url.startswith('/'):
        url = f'/{url}'
    return RedirectResponse(url=url, status_code=303)

def path_san(x, suppl=False, s=SUB_PATH):
    standard_formatting = x.replace(s, "").replace("\\", "/")
    if standard_formatting == "" and suppl:
        return "/ "
    return standard_formatting


async def text_san(x, r, w=""):
    mrep = lambda ss, dd, ww="": ss if not dd else mrep(ss.replace(dd.pop(), ww), dd)
    return mrep(ss=x, dd=r, ww=w)


async def href_regex(line, mode="check"):
    res = search(r'href\s*=\s*[\'"]?([^\'" >]+)(html)', line)
    if mode == "replace":
        if res:
            return line.replace(res.group(1), "/" + res.group(1)).replace(".html", "")
        return line
    return res is not None


async def to_json(x):
    res = x
    if isinstance(x, dict):
        res = dumps(x).replace("'", "''")
    elif isinstance(x, str):
        try:
            res = loads(x)
        except JSONDecodeError:
            res = loads(x.replace("'", '"'))
        res = dumps(res)
    elif x is None:
        res = "None"
    else:
        raise Exception(f'''
            Unknown handling for {type(x)=}
            _______________________________
            {x=}
        ''')
    result = "'" + res + "'"
    return result


async def date_checker(date, valid_formats=VALID_DATE_FORMATS):
    INVALID_EXCEPTION = Exception(f"""
        Invalid Date Format! Acceptable formats are:
        {" or ".join(valid_formats)},
    """)
    if not isinstance(date, str):
        raise INVALID_EXCEPTION
    
    valid_date = False
    for f in valid_formats:
        try:
            date = dt.strptime(date, f)
            valid_date = True
        except:
            pass
    if valid_date:
        return date
    raise INVALID_EXCEPTION


async def convert_your_html_files(decoration_dir, where_am_i=None):
    for root, directories, filenames in walk(decoration_dir):
        for a_file in filenames:
            if a_file.endswith(".html"):
                filepath = FS.join([root, a_file])

                with open(filepath, "r+", encoding="utf-8") as f:
                    content = f.read().splitlines()

                for line in content:
                    line = line.lstrip()
                    common_exclude = any(
                        [
                            x in line
                            for x in ("{{", "http",)
                        ]
                    )
                    if not common_exclude:
                        element_type, new_line = None, None

                        if "<link href=" in line:
                            element_type = "css"
                        elif "<script src=" in line:
                            element_type = "js"
                        elif href_regex(line, mode="check"):
                            element_type = "href"
                            new_line = href_regex(line, mode="replace")

                        if element_type is not None:
                            if new_line is None:
                                actions = html2c[element_type]["replace"]
                                # Create new object reference:
                                new_line = line + ""
                                for rec in actions:
                                    new_line = new_line.replace(rec["from"], rec["to"])
                            old_new = {"old": line, "new": new_line}
                            html2c[element_type]["lines"].append(old_new)

                content = "\n".join(content)
                detected_changes = False
                for element_category, data in html2c.items():
                    if len(data["lines"]) > 0:
                        detected_changes = True
                        for line in data["lines"]:
                            content = content.replace(line["old"], line["new"])

                if detected_changes:
                    with open(filepath, "w+", encoding="utf-8") as f:
                        f.write(content)
