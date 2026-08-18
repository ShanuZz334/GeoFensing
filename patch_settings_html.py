import re

with open("admin/settings.html", "r", encoding="utf-8") as f:
    html = f.read()

# Replace Leave Quotas section
leave_quotas_pattern = r'<!-- Leave Quotas -->.*?</div>'
salary_deduction_html = '''<!-- Salary Deduction Config -->
        <div class="card" style="padding: 24px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);">
          <h2 style="font-size: 16px; font-weight: 600; margin-bottom: 16px;">Leave & Salary Deduction</h2>
          <div class="form-group">
            <label>Full-Day Absence Deduction (%) <span class="info-icon" data-tip="Percentage of salary deducted for 1 unapproved full day absence.">i</span></label>
            <input type="number" id="set-full-deduction" class="form-control" step="0.1" min="0" max="100" />
          </div>
          <div class="form-group">
            <label>Half-Day Absence Deduction (%) <span class="info-icon" data-tip="Percentage of salary deducted for 1 unapproved half day absence.">i</span></label>
            <input type="number" id="set-half-deduction" class="form-control" step="0.1" min="0" max="100" />
          </div>
          <div class="form-group">
            <label>Emergency Leave Deduction (%) <span class="info-icon" data-tip="Percentage of salary deducted for 1 emergency leave.">i</span></label>
            <input type="number" id="set-emergency-deduction" class="form-control" step="0.1" min="0" max="100" />
          </div>
          <div class="form-group">
            <label>Emergency Leave Monthly Limit <span class="info-icon" data-tip="Maximum number of emergency leaves allowed per month.">i</span></label>
            <input type="number" id="set-emergency-limit" class="form-control" min="0" max="10" />
          </div>
        </div>'''
html = re.sub(leave_quotas_pattern, salary_deduction_html, html, flags=re.DOTALL, count=1)

# Remove Per-Teacher Extra Leaves section
extra_leaves_pattern = r'<!-- Per-Teacher Extra Leaves -->.*?<!-- Holiday Manager Calendar -->'
html = re.sub(extra_leaves_pattern, '<!-- Holiday Manager Calendar -->', html, flags=re.DOTALL, count=1)

# Fix JavaScript loading logic to populate the new fields
load_js_pattern = r'if \(data\.monthly_allotted_leaves !== undefined\) \{.*?document\.getElementById\(\'set-monthly-half-leaves\'\)\.value = data\.monthly_allotted_half_leaves;\s*\}'

load_js_replacement = '''if (data.full_day_deduction_pct !== undefined) {
          document.getElementById('set-full-deduction').value = data.full_day_deduction_pct;
        }
        if (data.half_day_deduction_pct !== undefined) {
          document.getElementById('set-half-deduction').value = data.half_day_deduction_pct;
        }
        if (data.emergency_leave_deduction_pct !== undefined) {
          document.getElementById('set-emergency-deduction').value = data.emergency_leave_deduction_pct;
        }
        if (data.emergency_leave_limit !== undefined) {
          document.getElementById('set-emergency-limit').value = data.emergency_leave_limit;
        }'''
html = re.sub(load_js_pattern, load_js_replacement, html, flags=re.DOTALL)

# Fix JavaScript saving logic to gather the new fields
save_js_pattern = r'monthly_allotted_leaves:\s*parseInt\(document\.getElementById\(\'set-monthly-leaves\'\)\.value\) \|\| 0,\s*monthly_allotted_half_leaves:\s*parseInt\(document\.getElementById\(\'set-monthly-half-leaves\'\)\.value\) \|\| 0,'

save_js_replacement = '''full_day_deduction_pct: parseFloat(document.getElementById('set-full-deduction').value) || 3.0,
        half_day_deduction_pct: parseFloat(document.getElementById('set-half-deduction').value) || 1.5,
        emergency_leave_deduction_pct: parseFloat(document.getElementById('set-emergency-deduction').value) || 0.5,
        emergency_leave_limit: parseInt(document.getElementById('set-emergency-limit').value) || 2,'''
html = re.sub(save_js_pattern, save_js_replacement, html, flags=re.DOTALL)

# Remove Per-Teacher Leave Management JS logic
per_teacher_js_pattern = r'// ── Per-Teacher Leave Management ─────────────────────────────────────────.*?async function loadSystemLogs'
html = re.sub(per_teacher_js_pattern, 'async function loadSystemLogs', html, flags=re.DOTALL)

with open("admin/settings.html", "w", encoding="utf-8") as f:
    f.write(html)
