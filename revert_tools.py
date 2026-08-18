import re

# Fix map.html
with open(r'admin/map.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Define the start and end of the block to replace
start_marker = "<!-- Editor Mode Selection (Visible only in Edit Mode) -->"
end_marker = "</div>\n          <button class=\"btn-secondary\" id=\"btn-clear-geofence\""

try:
    start_idx = html.index(start_marker)
    end_idx = html.index(end_marker)
    
    replacement = """<!-- Editor Mode Selection (Visible only in Edit Mode) -->
          <div id="editor-tools" style="display:none; gap: 8px;">
            <button class="btn-secondary" id="tool-main" onclick="setEditorTool('main')" style="margin:0; white-space: nowrap;">Main Polygon</button>
            <button class="btn-secondary" id="tool-sub" onclick="setEditorTool('sub')" style="margin:0; white-space: nowrap;">Dept Block</button>
            <button class="btn-secondary" id="tool-cp" onclick="setEditorTool('cp')" style="margin:0; white-space: nowrap;">Checkpoint</button>
          """
    
    new_html = html[:start_idx] + replacement + html[end_idx:]
    with open(r'admin/map.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("Reverted map.html editor tools!")
except ValueError:
    print("Could not find markers in map.html")


# Fix map.js
with open(r'admin/js/map.js', 'r', encoding='utf-8') as f:
    js = f.read()

target = """function updateToolUI() {
  ['main', 'sub', 'cp'].forEach(t => {
    const radio = document.getElementById(`tool-${t}-radio`);
    if (radio) {
      radio.checked = (activeTool === t);
    }
  });
}"""

replacement = """function updateToolUI() {
  ['main', 'sub', 'cp'].forEach(t => {
    const btn = document.getElementById(`tool-${t}`);
    if(btn) {
      if (activeTool === t) {
        btn.style.background = 'var(--primary)';
        btn.style.color = 'white';
        btn.style.borderColor = 'var(--primary)';
      } else {
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '';
      }
    }
  });
}"""

if target in js:
    js = js.replace(target, replacement)
    print("Reverted updateToolUI in map.js!")
else:
    print("Could not find updateToolUI target in map.js")

with open(r'admin/js/map.js', 'w', encoding='utf-8') as f:
    f.write(js)
