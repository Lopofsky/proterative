from os import name as os_name, walk, getcwd, chdir, listdir
from re import search

async def text_san(x, r, w=''):
    mrep = lambda ss, dd, ww='': ss if not dd else mrep(ss.replace(dd.pop(), ww), dd)
    return mrep(ss=x, dd=r, ww=w)

async def href_regex(line, mode='check'):
    res = search(r'href\s*=\s*[\'"]?([^\'" >]+)(html)', line)
    if mode == 'replace':
        if res: return line.replace(res.group(1), '/'+res.group(1)).replace('.html', '')
        return line
    else: return not res is None

async def convert_your_html_files(where_am_i):
    fs = "\\" if os_name == 'nt' else '/'
    if where_am_i.find('docker') > -1:
        path = "/app"
        chdir(path)
    else: path = getcwd()
    for root, directories, filenames in walk(path):
        for a_file in filenames:
            if a_file.endswith('.html'):
                len_css, len_js, len_href = 0, 0, 0
                with open(root+fs+a_file, "r+", encoding="utf-8") as f:
                    content = f.read().splitlines()
                css = [i.lstrip() for i in content if i.lstrip().find('<link href=')>=0 and i.lstrip().find('{{') < 0 and i.lstrip().find('http') < 0]
                js = [i.lstrip() for i in content if i.lstrip().find('<script src=')>=0 and i.lstrip().find('{{') < 0 and i.lstrip().find('http') < 0]
                href = [i.lstrip() for i in content if await href_regex(i.lstrip(), mode='check') and i.lstrip().find('{{')==i.lstrip().find('http')==i.lstrip().find('<script src=')==i.lstrip().find('<link href=') and i.lstrip().find('<link href=') < 0]
                replasador_css = [{x:x.replace('<link href="', """<link href="{{url_for('static', path='""").replace('''.css"''', '''.css') }}"''')} for x in css]
                replasador_js = [{x:x.replace('<script src="', """<script src="{{url_for('static', path='""").replace('''.js"''', '''.js') }}"''')} for x in js]
                replasador_href = [{x:await href_regex(x, mode='replace')} for x in href]
                content = '\n'.join(content)
                check_results = lambda x: 0 if x is None else len(x)
                len_css, len_js, len_href = check_results(css), check_results(js), check_results(href)
                if len_css > 0:
                    for x in replasador_css:
                        for old, new in x.items():
                            content = content.replace(old, new)
                if len_js > 0:
                    for x in replasador_js:
                        for old, new in x.items():
                            content = content.replace(old, new)
                if len_href > 0:
                    for x in replasador_href:
                        for old, new in x.items():
                            content = content.replace(old, new)
                if len_js > 0 or len_css > 0 or len_href > 0:
                    with open(root+fs+a_file, "w+", encoding="utf-8") as f:
                        f.write(content)