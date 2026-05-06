import glob
import re

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(r'src="js/api\.js\?[^"]+"', 'src="js/api.js?v=4"', content)
    new_content = new_content.replace('src="js/api.js"', 'src="js/api.js?v=4"')
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")
