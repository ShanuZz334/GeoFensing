import re

with open(r'admin/map.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """          <div class="form-group">
            <label>Color</label>
            <input type="color" id="sub-color" class="form-control" value="#ff0000" style="padding:4px; height:42px;" />
          </div>"""

replacement = """          <div class="form-group">
            <label>Color</label>
            <input type="hidden" id="sub-color" value="#ff4d4d" />
            <div class="color-swatch-container">
              <div class="color-swatch selected" style="background-color: #ff4d4d;" data-color="#ff4d4d" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #ff9f43;" data-color="#ff9f43" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #feca57;" data-color="#feca57" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #1dd1a1;" data-color="#1dd1a1" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #54a0ff;" data-color="#54a0ff" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #5f27cd;" data-color="#5f27cd" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #ff9ff3;" data-color="#ff9ff3" onclick="selectColor(this)"></div>
              <div class="color-swatch" style="background-color: #c8d6e5;" data-color="#c8d6e5" onclick="selectColor(this)"></div>
            </div>
          </div>"""

if target in html:
    html = html.replace(target, replacement)
    with open(r'admin/map.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Replaced color input with swatches in map.html!")
else:
    print("Color input target not found.")
