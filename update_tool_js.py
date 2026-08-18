import re

with open(r'admin/js/map.js', 'r', encoding='utf-8') as f:
    js = f.read()

target = """function updateToolUI() {
  ['main', 'sub', 'cp'].forEach(t => {
    const btn = document.getElementById(`tool-${t}`);
    if (activeTool === t) {
      btn.style.background = 'var(--primary)';
      btn.style.color = 'white';
      btn.style.borderColor = 'var(--primary)';
    } else {
      btn.style.background = '';
      btn.style.color = '';
      btn.style.borderColor = '';
    }
  });
}"""

replacement = """function updateToolUI() {
  ['main', 'sub', 'cp'].forEach(t => {
    const radio = document.getElementById(`tool-${t}-radio`);
    if (radio) {
      radio.checked = (activeTool === t);
    }
  });
}"""

if target in js:
    js = js.replace(target, replacement)
    print("Replaced updateToolUI!")
else:
    print("Could not find updateToolUI target in map.js")

with open(r'admin/js/map.js', 'w', encoding='utf-8') as f:
    f.write(js)
