import re

with open(r'admin/settings.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Move Demo Mode to header-actions as a simple toggle
# Find header-actions
header_actions_target = """<div class="header-actions" style="margin: 0; display: flex; gap: 8px;">
          <button id="btn-reset-all-devices\""""
          
demo_toggle_compact = """<div class="header-actions" style="margin: 0; display: flex; gap: 8px;">
          <div style="display:flex; align-items:center; gap:8px; margin-right: 12px; background: rgba(124, 58, 237, 0.1); padding: 4px 12px; border-radius: 8px; border: 1px solid rgba(124, 58, 237, 0.3);">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #7c3aed; box-shadow: 0 0 6px #7c3aed;"></span>
            <span style="font-size: 13px; font-weight: 600; color: #a78bfa;">Demo Mode</span>
            <label class="uiverse-switch" style="transform: scale(0.8); margin: 0;">
              <input type="checkbox" id="set-demo-mode" />
              <span class="uiverse-slider"></span>
            </label>
          </div>
          <button id="btn-reset-all-devices\""""

if header_actions_target in html:
    html = html.replace(header_actions_target, demo_toggle_compact)

# 2. Remove the old System Demo Mode Toggle Card
old_demo_card_regex = re.compile(r'<!-- System Demo Mode Toggle Card -->.*?</div>\s*</div>\s*</div>', re.DOTALL)
html = old_demo_card_regex.sub('', html)


# 3. Move Attendance Geofence Mode and change it to a normal card
geofence_card_regex = re.compile(r'<!-- Attendance Geofence Mode Toggle -->\s*<div class="card settings-span-3"(.*?)</div>\s*</div>\s*</div>\s*<style>.*?</style>\s*</div>', re.DOTALL)
match = geofence_card_regex.search(html)

if match:
    geofence_html = match.group(0)
    html = html.replace(geofence_html, '')
    
    # Change it to a normal card
    geofence_html = geofence_html.replace('class="card settings-span-3"', 'class="card"')
    
    # Insert it before Extra Leaves
    extra_leaves_target = '<!-- Per-Teacher Extra Leaves -->'
    html = html.replace(extra_leaves_target, geofence_html + '\n\n      ' + extra_leaves_target)

with open(r'admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Done rearranging settings.html")
