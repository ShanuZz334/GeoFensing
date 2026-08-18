import glob
import re

files = glob.glob('admin/*.html')
for file in files:
    # Skip index.html and audit.html as they don't have header with buttons
    if 'index.html' in file or 'audit.html' in file:
        continue
        
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match `<header class="page-header"[^>]*>` and check if it is already followed by `<div></div>`
    # If not, insert `<div></div>` immediately after it
    def replace_header(match):
        header_tag = match.group(0)
        # Avoid double-inserting
        rest_of_file = content[match.end():]
        if rest_of_file.strip().startswith('<div></div>'):
            return header_tag
        return header_tag + '\n      <div></div>'

    new_content = re.sub(r'<header class="page-header"[^>]*>', replace_header, content, flags=re.IGNORECASE)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated header in {file}")
