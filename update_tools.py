import re

with open(r'admin/map.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """          <!-- Editor Mode Selection (Visible only in Edit Mode) -->
          <div id="editor-tools" style="display:none; background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 4px; gap: 4px;">
            <button class="btn-secondary" id="tool-main" onclick="setEditorTool('main')" style="margin:0; background: var(--primary); color: white; border-color: var(--primary);">Main</button>
            <button class="btn-secondary" id="tool-sub" onclick="setEditorTool('sub')" style="margin:0;">+ Sub-Polygon</button>
            <button class="btn-secondary" id="tool-cp" onclick="setEditorTool('cp')" style="margin:0;">+ Checkpoint</button>
          </div>"""

replacement = """          <!-- Editor Mode Selection (Visible only in Edit Mode) -->
          <div id="editor-tools" style="display:none; background: var(--surface-2); border: 1px solid var(--border); border-radius: 12px; padding: 4px; gap: 4px; align-items: stretch;">
            <label style="cursor: pointer; margin: 0; flex: 1;">
              <input type="radio" name="editor_tool" value="main" id="tool-main-radio" onchange="if(this.checked) setEditorTool('main')" style="display: none;" checked>
              <div class="mode-toggle-btn" style="padding: 8px 16px; text-align: center; border-radius: 8px; font-size: 13px; font-weight: 500; transition: all 0.2s; color: var(--text); height: 100%; display:flex; align-items:center; justify-content:center;">
                Main Polygon
              </div>
            </label>
            <label style="cursor: pointer; margin: 0; flex: 1;">
              <input type="radio" name="editor_tool" value="sub" id="tool-sub-radio" onchange="if(this.checked) setEditorTool('sub')" style="display: none;">
              <div class="mode-toggle-btn" style="padding: 8px 16px; text-align: center; border-radius: 8px; font-size: 13px; font-weight: 500; transition: all 0.2s; color: var(--text); height: 100%; display:flex; align-items:center; justify-content:center;">
                Department Block
              </div>
            </label>
            <label style="cursor: pointer; margin: 0; flex: 1;">
              <input type="radio" name="editor_tool" value="cp" id="tool-cp-radio" onchange="if(this.checked) setEditorTool('cp')" style="display: none;">
              <div class="mode-toggle-btn" style="padding: 8px 16px; text-align: center; border-radius: 8px; font-size: 13px; font-weight: 500; transition: all 0.2s; color: var(--text); height: 100%; display:flex; align-items:center; justify-content:center;">
                Checkpoint
              </div>
            </label>
            
            <style>
              input[name="editor_tool"]:checked + .mode-toggle-btn {
                background: var(--primary);
                box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
                color: white !important;
              }
              .mode-toggle-btn:hover {
                background: rgba(255, 255, 255, 0.05);
              }
              input[name="editor_tool"]:checked + .mode-toggle-btn:hover {
                background: var(--primary);
              }
            </style>
          </div>"""

if target in html:
    html = html.replace(target, replacement)
    print("Replaced HTML editor tools!")
else:
    print("Could not find target string in map.html")

with open(r'admin/map.html', 'w', encoding='utf-8') as f:
    f.write(html)
