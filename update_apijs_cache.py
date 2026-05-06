import glob
import os

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'src="js/api.js?v=1001"' in content:
        content = content.replace('src="js/api.js?v=1001"', 'src="js/api.js?v=3"')
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
