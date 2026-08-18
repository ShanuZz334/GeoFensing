import glob
import re

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match the div containing the page-title h1 and page-subtitle p
    pattern = r'<div>\s*<h1 class="page-title">.*?</h1>\s*<p class="page-subtitle">.*?</p>\s*</div>'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # If the header element is now empty, remove the header element completely
    header_pattern = r'<header class="page-header"[^>]*>\s*</header>'
    new_content = re.sub(header_pattern, '', new_content, flags=re.DOTALL | re.IGNORECASE)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")
