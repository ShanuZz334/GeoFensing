import os

file_path = r'c:\project\ALLBACKUP\GeoFense\backend\app\routes\admin.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'leave_type = data.get("leave_type", "full") # \'full\' or \'half\'' in line:
        new_lines.append(line)
        new_lines.append('    quota_type = data.get("quota_type", "semester") # \'semester\' or \'monthly\'\n')
    elif 'teacher.extra_half_leaves = int(extra_half_leaves)' in line:
        new_lines.append('        if quota_type == "monthly":\n')
        new_lines.append('            teacher.extra_half_monthly_leaves = int(extra_half_leaves)\n')
        new_lines.append('            msg = f"Updated monthly half-day leaves for {teacher.full_name}"\n')
        new_lines.append('        else:\n')
        new_lines.append('            teacher.extra_half_leaves = int(extra_half_leaves)\n')
    elif 'msg = f"Updated half-day leaves for {teacher.full_name}"' in line:
        continue
    elif 'teacher.extra_leaves = int(extra_leaves)' in line:
        new_lines.append('        if quota_type == "monthly":\n')
        new_lines.append('            teacher.extra_monthly_leaves = int(extra_leaves)\n')
        new_lines.append('            msg = f"Updated monthly full-day leaves for {teacher.full_name}"\n')
        new_lines.append('        else:\n')
        new_lines.append('            teacher.extra_leaves = int(extra_leaves)\n')
    elif 'msg = f"Updated full-day leaves for {teacher.full_name}"' in line:
        continue
    elif 'return jsonify({"message": msg, "extra_leaves": teacher.extra_leaves, "extra_half_leaves": teacher.extra_half_leaves}), 200' in line:
        new_lines.append('    return jsonify({"message": msg, "extra_leaves": teacher.extra_leaves, "extra_half_leaves": teacher.extra_half_leaves, "extra_monthly_leaves": teacher.extra_monthly_leaves, "extra_half_monthly_leaves": teacher.extra_half_monthly_leaves}), 200\n')
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
