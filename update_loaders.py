import os
import re

html_files = [f for f in os.listdir('admin') if f.endswith('.html')]
js_files = [os.path.join('admin', 'js', f) for f in os.listdir(os.path.join('admin', 'js')) if f.endswith('.js')]

for file_path in [os.path.join('admin', f) for f in html_files] + js_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace <td ... class="td-loading">Loading...</td>
    new_content = re.sub(
        r'(<td[^>]*?class="td-loading"[^>]*?>)[^<]+(</td>)',
        r'\g<1><div class="spinner"></div>\g<2>',
        content
    )
    
    # In alerts.html, there is:
    # <div id="alerts-loading" style="text-align:center; padding:40px; color:var(--text-muted);">
    #    Loading alerts...
    # </div>
    new_content = re.sub(
        r'(<div id="alerts-loading"[^>]*?>)\s*Loading alerts\.\.\.\s*(</div>)',
        r'\g<1><div class="spinner"></div>\g<2>',
        new_content
    )

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated loaders in {file_path}")
