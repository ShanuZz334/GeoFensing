import os
import re

html_files = [f for f in os.listdir('admin') if f.endswith('.html')]

# The exact new order of nav items
new_order_ids = [
    'nav-dashboard',
    'nav-alerts',
    'nav-teachers',
    'nav-logs',
    'nav-map',
    'nav-admins',
    'nav-audit',
    'nav-settings'
]

for filename in html_files:
    filepath = os.path.join('admin', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the nav block
    match = re.search(r'(<nav class="sidebar-nav">)(.*?)(</nav>)', content, re.DOTALL)
    if not match:
        continue
        
    nav_start = match.group(1)
    nav_inner = match.group(2)
    nav_end = match.group(3)
    
    # Extract individual items
    items = {}
    item_matches = re.finditer(r'<a href="[^"]+" class="nav-item[^"]*" id="([^"]+)">.*?</a>', nav_inner, re.DOTALL)
    for m in item_matches:
        items[m.group(1)] = m.group(0)
        
    # Rebuild nav inner content in new order
    new_nav_inner = "\n      " + "\n      ".join([items[id] for id in new_order_ids if id in items]) + "\n    "
    
    # Replace in file
    new_content = content[:match.start()] + nav_start + new_nav_inner + nav_end + content[match.end():]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Updated {filename}")
