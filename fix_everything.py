import re

with open(r'admin/settings.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Compact Demo Mode Toggle
header_actions_target = """<div class="header-actions" style="margin: 0; display: flex; gap: 8px;">
          <button id="btn-reset-all-devices\""""
          
demo_toggle_compact = """<div class="header-actions" style="margin: 0; display: flex; gap: 8px; align-items: center;">
          <div style="display:flex; align-items:center; gap:8px; margin-right: 12px; background: rgba(124, 58, 237, 0.1); padding: 4px 12px; border-radius: 8px; border: 1px solid rgba(124, 58, 237, 0.3);">
            <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #7c3aed; box-shadow: 0 0 6px #7c3aed;"></span>
            <span style="font-size: 13px; font-weight: 600; color: #a78bfa;">Demo Mode</span>
            <label class="uiverse-switch" style="transform: scale(0.8); margin: 0; display: flex; align-items: center;">
              <input type="checkbox" id="set-demo-mode" />
              <span class="uiverse-slider"></span>
            </label>
          </div>
          <button id="btn-reset-all-devices\""""

if header_actions_target in html:
    html = html.replace(header_actions_target, demo_toggle_compact)

# 2. Remove old System Demo Mode Toggle Card safely
old_demo_card_regex = re.compile(r'<!-- System Demo Mode Toggle Card -->.*?<p.*?Perfect for testing and demonstrations.*?</p>.*?</div>.*?</div>.*?</div>', re.DOTALL)
html = old_demo_card_regex.sub('', html)

# 3. Insert Attendance Geofence Mode just before Extra Leaves
extra_leaves_target = '<!-- Per-Teacher Extra Leaves -->'

geofence_html = """      <!-- Attendance Geofence Mode Toggle -->
      <div class="card" style="padding: 24px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);">
        <h2 style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Attendance Geofence Mode</h2>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px; line-height: 1.4;">
          Select the active geofencing mode for the campus. This determines where teachers are allowed to check in and check out.
        </p>
        
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <label style="cursor: pointer;">
            <input type="radio" name="geofence_mode" value="1" id="mode-1" style="display: none;" checked>
            <div class="mode-toggle-btn" style="padding: 16px; text-align: center; border-radius: 12px; font-size: 15px; font-weight: 600; transition: all 0.2s; background: var(--surface-2); border: 1px solid var(--border);">
              <div style="color: var(--text); margin-bottom: 4px;">Global Campus</div>
              <div style="font-size: 12px; color: var(--text-muted); font-weight: 400;">Single Polygon (Teachers can check-in anywhere inside the main campus)</div>
            </div>
          </label>
          <div style="display: flex; gap: 8px;">
            <label style="flex: 1; cursor: pointer;">
              <input type="radio" name="geofence_mode" value="2" id="mode-2" style="display: none;">
              <div class="mode-toggle-btn" style="padding: 12px; text-align: center; border-radius: 8px; font-size: 14px; font-weight: 500; transition: all 0.2s; background: var(--surface-2); border: 1px solid var(--border);">
                Department Blocks
              </div>
            </label>
            <label style="flex: 1; cursor: pointer;">
              <input type="radio" name="geofence_mode" value="3" id="mode-3" style="display: none;">
              <div class="mode-toggle-btn" style="padding: 12px; text-align: center; border-radius: 8px; font-size: 14px; font-weight: 500; transition: all 0.2s; background: var(--surface-2); border: 1px solid var(--border);">
                Special Checkpoints
              </div>
            </label>
          </div>
        </div>
        
        <style>
          input[name="geofence_mode"]:checked + .mode-toggle-btn {
            background: var(--primary) !important;
            border-color: var(--primary) !important;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
          }
          input[name="geofence_mode"]:checked + .mode-toggle-btn div {
            color: white !important;
          }
          .mode-toggle-btn:hover {
            border-color: rgba(124, 58, 237, 0.5) !important;
          }
        </style>
      </div>

"""

html = html.replace(extra_leaves_target, geofence_html + extra_leaves_target)

# 4. Inject JavaScript for Geofence Mode
load_settings_target = """        if (data.demo_mode !== undefined) {
          document.getElementById('set-demo-mode').checked = data.demo_mode === true;
        }"""
        
load_settings_inject = load_settings_target + """
        if (data.geofence_config) {
          window._currentGeofenceConfig = data.geofence_config || { mode: 1 };
          const mode = window._currentGeofenceConfig.mode || 1;
          const modeRadio = document.getElementById(`mode-${mode}`);
          if (modeRadio) modeRadio.checked = true;
        } else {
          window._currentGeofenceConfig = { mode: 1 };
        }"""

if load_settings_target in html:
    html = html.replace(load_settings_target, load_settings_inject)

save_settings_target = """        demo_mode: document.getElementById('set-demo-mode').checked
      };"""
      
save_settings_inject = save_settings_target + """
      const modeRadio = document.querySelector('input[name="geofence_mode"]:checked');
      if (modeRadio) {
        const selectedMode = parseInt(modeRadio.value);
        if (window._currentGeofenceConfig) {
          window._currentGeofenceConfig.mode = selectedMode;
          payload.geofence_config = window._currentGeofenceConfig;
        } else {
          payload.geofence_config = { mode: selectedMode };
        }
      }"""

if save_settings_target in html:
    html = html.replace(save_settings_target, save_settings_inject)


with open(r'admin/settings.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Applied UI fixes successfully.")
