import os
import re

files = [
    'admin/index.html', 
    'admin/teachers.html', 
    'admin/logs.html', 
    'admin/map.html', 
    'admin/alerts.html', 
    'admin/settings.html'
]

new_links = """
      <a href="admins.html" class="nav-item" id="nav-admins">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0z" /></svg>
        Manage Admins
      </a>
      <a href="audit.html" class="nav-item" id="nav-audit">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>
        Audit Logs
      </a>"""

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if "Manage Admins" not in content:
        # Match from <a href="settings.html... to the closing </a>
        updated_content = re.sub(r'(<a href="settings\.html.*?</a>)', r'\g<1>' + new_links, content, flags=re.DOTALL)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f"Updated {f}")
    else:
        print(f"Already updated {f}")
