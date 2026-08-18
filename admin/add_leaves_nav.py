import os
import glob
import re

html_files = glob.glob(r"C:\project\ALLBACKUP\GeoFense\admin\*.html")

nav_block = """        <a href="leaves.html" class="nav-item" id="nav-leaves">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5m-9-6h.008v.008H12v-.008zM12 15h.008v.008H12V15zm0 2.25h.008v.008H12v-.008zM9.75 15h.008v.008H9.75V15zm0 2.25h.008v.008H9.75v-.008zM7.5 15h.008v.008H7.5V15zm0 2.25h.008v.008H7.5v-.008zm6.75-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008V15zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H16.5v-.008zm0 2.25h.008v.008H16.5V15z"/></svg>
          Leaves
        </a>"""

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'id="nav-leaves"' in content:
        print(f"Skipping {os.path.basename(file)}, already has nav-leaves")
        continue
        
    # Find the end of the Reports anchor tag
    pattern = re.compile(r'(id="nav-audit".*?</a>)', re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(r'\1\n' + nav_block, content)
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {os.path.basename(file)}")
    else:
        print(f"Could not find Reports block in {os.path.basename(file)}")
