from os import name as os_name, walk, getcwd

fs, path = "\\" if os_name == 'nt' else '/', getcwd()
for root, directories, filenames in walk(path):
    for a_file in filenames:
        if a_file.endswith('.html'):
            with open(root+fs+a_file, "r+", encoding="utf-8") as f:
                content = f.read().splitlines()
            css = [i.lstrip() for i in content if i.lstrip().find('<link href=')>=0 and i.lstrip().find('{{') < 0 and i.lstrip().find('http') < 0]
            js = [i.lstrip() for i in content if i.lstrip().find('<script src=')>=0 and i.lstrip().find('{{') < 0 and i.lstrip().find('http') < 0]
            replasador_css = [{x:x.replace('<link href="', """<link href="{{url_for('static', path='""").replace('''.css"''', '''.css') }}"''')} for x in css]
            replasador_js = [{x:x.replace('<script src="', """<script src="{{url_for('static', path='""").replace('''.js"''', '''.js') }}"''')} for x in js]
            content = '\n'.join(content)
            for x in replasador_css:
                for old, new in x.items():
                    content = content.replace(old, new)
            for x in replasador_js:
                for old, new in x.items():
                    content = content.replace(old, new)
            with open(root+fs+a_file, "w+", encoding="utf-8") as f:
                f.write(content)