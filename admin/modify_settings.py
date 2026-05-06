import os

file_path = r'c:\project\ALLBACKUP\GeoFense\admin\settings.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if '<input type="radio" name="leave_type" value="half" onchange="toggleLeaveType(this)" /> Half Day' in line:
        new_lines.append(line)
        new_lines.append('              </div>\n')
        new_lines.append('              <div style="display:flex; gap:12px; margin-bottom:12px;">\n')
        new_lines.append('                <label style="display:flex; align-items:center; gap:4px; font-size:14px;">\n')
        new_lines.append('                  <input type="radio" name="quota_type" value="semester" checked onchange="toggleLeaveType()" /> Semester Quota\n')
        new_lines.append('                </label>\n')
        new_lines.append('                <label style="display:flex; align-items:center; gap:4px; font-size:14px;">\n')
        new_lines.append('                  <input type="radio" name="quota_type" value="monthly" onchange="toggleLeaveType()" /> Monthly Quota\n')
        new_lines.append('                </label>\n')
    elif 'function toggleLeaveType(' in line:
        new_lines.append('    function toggleLeaveType() {\n')
    elif "const isHalf = document.querySelector('input[name=\"leave_type\"]:checked').value === 'half';" in line:
        new_lines.append(line)
        new_lines.append("      const isMonthly = document.querySelector('input[name=\"quota_type\"]:checked').value === 'monthly';\n")
    elif "document.getElementById('extra-leaves-label').textContent = isHalf ? 'Extra Semester Leaves (Half Day)' : 'Extra Semester Leaves (Full Day)';" in line:
        new_lines.append("      const quotaText = isMonthly ? 'Monthly' : 'Semester';\n")
        new_lines.append("      document.getElementById('extra-leaves-label').textContent = isHalf ? `Extra ${quotaText} Leaves (Half Day)` : `Extra ${quotaText} Leaves (Full Day)`;\n")
        new_lines.append("      document.getElementById('extra-leaves-help').textContent = `Additional leaves for THIS ${isMonthly ? 'month' : 'semester'} only.`;\n")
    elif "        document.getElementById('extra-leaves-input').value = isHalf" in line:
        new_lines.append("        if (isMonthly) {\n")
        new_lines.append("          document.getElementById('extra-leaves-input').value = isHalf \n")
        new_lines.append("            ? (currentTeacherData.extra_half_monthly_leaves || 0) \n")
        new_lines.append("            : (currentTeacherData.extra_monthly_leaves || 0);\n")
        new_lines.append("        } else {\n")
        new_lines.append("          document.getElementById('extra-leaves-input').value = isHalf \n")
        new_lines.append("            ? (currentTeacherData.extra_half_leaves || 0) \n")
        new_lines.append("            : (currentTeacherData.extra_leaves || 0);\n")
        new_lines.append("        }\n")
    elif "          ? (currentTeacherData.extra_half_leaves || 0)" in line:
        continue
    elif "          : (currentTeacherData.extra_leaves || 0);" in line:
        continue
    elif "const leaveType = document.querySelector('input[name=\"leave_type\"]:checked').value;" in line:
        new_lines.append(line)
        new_lines.append("        const quotaType = document.querySelector('input[name=\"quota_type\"]:checked').value;\n")
    elif "        document.getElementById('extra-leaves-input').value = leaveType === 'half'" in line:
        new_lines.append("        if (quotaType === 'monthly') {\n")
        new_lines.append("          document.getElementById('extra-leaves-input').value = leaveType === 'half' \n")
        new_lines.append("            ? (data.extra_half_monthly_leaves || 0) \n")
        new_lines.append("            : (data.extra_monthly_leaves || 0);\n")
        new_lines.append("        } else {\n")
        new_lines.append("          document.getElementById('extra-leaves-input').value = leaveType === 'half' \n")
        new_lines.append("            ? (data.extra_half_leaves || 0) \n")
        new_lines.append("            : (data.extra_leaves || 0);\n")
        new_lines.append("        }\n")
    elif "          ? (data.extra_half_leaves || 0)" in line:
        continue
    elif "          : (data.extra_leaves || 0);" in line:
        continue
    elif "      const leaveType = document.querySelector('input[name=\"leave_type\"]:checked').value;" in line:
        new_lines.append(line)
        new_lines.append("      const quotaType = document.querySelector('input[name=\"quota_type\"]:checked').value;\n")
    elif "        leave_type: leaveType" in line:
        new_lines.append("        leave_type: leaveType,\n")
        new_lines.append("        quota_type: quotaType\n")
    elif 'Additional leaves for THIS semester only.' in line:
        new_lines.append('                <div id="extra-leaves-help" class="help-text" style="font-size:12px; color:var(--text-muted); margin-top:4px;">Additional leaves for THIS semester only.</div>\n')
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
