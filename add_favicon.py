import glob

favicon_tag = '  <link rel="icon" type="image/png" href="favicon.png"/>'

for html_file in glob.glob('admin/*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    if 'favicon' not in content:
        new_content = content.replace('<meta charset="UTF-8"/>', '<meta charset="UTF-8"/>\n' + favicon_tag, 1)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Added favicon to {html_file}')
    else:
        print(f'favicon already present in {html_file}')
