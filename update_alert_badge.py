import glob
import os

target_str = '''      <a href="alerts.html" class="nav-item" id="nav-alerts">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        <span style="flex-grow: 1;">Alert Center</span>
        <span id="sidebar-alert-badge" style="display:none; background:var(--error, #ef4444); color:white; font-size:11px; font-weight:bold; height:20px; min-width:20px; border-radius:10px; align-items:center; justify-content:center; padding:0 6px;">0</span>
      </a>'''

replacement_str = '''      <a href="alerts.html" class="nav-item" id="nav-alerts">
        <div style="position: relative; display: flex;">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
          </svg>
          <span id="sidebar-alert-badge" style="display:none; position:absolute; top:-4px; right:-6px; background:var(--error, #ef4444); color:white; font-size:10px; font-weight:bold; height:16px; min-width:16px; border-radius:8px; align-items:center; justify-content:center; padding:0 4px; box-shadow: 0 0 0 2px var(--surface);">0</span>
        </div>
        <span>Alert Center</span>
      </a>'''

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if target_str in content:
        content = content.replace(target_str, replacement_str)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")
    else:
        print(f"Target string not found in {file}")
