import glob

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace logo.png?v=something with logo.png?v=3
    import re
    new_content = re.sub(r'images/logo\.png\?v=[0-9]+', 'images/logo.png?v=3', content)
    new_content = new_content.replace('images/logo.png', 'images/logo.png?v=3')
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")
