import os
import re

files = [f for f in os.listdir('admin') if f.endswith('.html')]
old_str = r'<a href="alerts\.html" class="nav-item(\s+active)?" id="nav-alerts">\s*<svg.*?</svg>\s*Alert Center\s*</a>'

for f in files:
    path = os.path.join('admin', f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    def repl(m):
        active_cls = m.group(1) or ''
        return f'''<a href="alerts.html" class="nav-item{active_cls}" id="nav-alerts">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        <span style="flex-grow: 1;">Alert Center</span>
        <span id="sidebar-alert-badge" style="display:none; background:var(--error, #ef4444); color:white; font-size:11px; font-weight:bold; height:20px; min-width:20px; border-radius:10px; align-items:center; justify-content:center; padding:0 6px;">0</span>
      </a>'''
    
    new_content = re.sub(old_str, repl, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {path}')
