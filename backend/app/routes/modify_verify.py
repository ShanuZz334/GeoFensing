import os

file_path = r'c:\project\ALLBACKUP\GeoFense\backend\app\routes\verify.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "extra_leaves = teacher.extra_leaves if teacher and teacher.extra_leaves else 0" in line:
        new_lines.append(line)
        new_lines.append("        extra_half_leaves = teacher.extra_half_leaves if teacher and hasattr(teacher, 'extra_half_leaves') and teacher.extra_half_leaves else 0\n")
        new_lines.append("        extra_monthly_leaves = teacher.extra_monthly_leaves if teacher and hasattr(teacher, 'extra_monthly_leaves') and teacher.extra_monthly_leaves else 0\n")
        new_lines.append("        extra_half_monthly_leaves = teacher.extra_half_monthly_leaves if teacher and hasattr(teacher, 'extra_half_monthly_leaves') and teacher.extra_half_monthly_leaves else 0\n")
    elif "extra_half_leaves = teacher.extra_half_leaves if teacher and hasattr(teacher, 'extra_half_leaves') and teacher.extra_half_leaves else 0" in line:
        continue # handled above
    elif "            # Current month quota" in line:
        new_lines.append(line)
        new_lines.append("            allotted = allotted_monthly + extra_monthly_leaves\n")
        new_lines.append("            allotted_half = allotted_half_monthly + extra_half_monthly_leaves\n")
    elif "            allotted = allotted_monthly" in line:
        continue
    elif "            allotted_half = allotted_half_monthly" in line:
        continue
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
