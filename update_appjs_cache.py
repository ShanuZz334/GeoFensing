import glob
import os

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'src="js/app.js"' in content:
        content = content.replace('src="js/app.js"', 'src="js/app.js?v=2"')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
