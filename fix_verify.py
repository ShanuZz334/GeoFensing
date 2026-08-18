import os

with open('backend/app/routes/stats_logic.py', 'r', encoding='utf-8') as f:
    orig_lines = f.readlines()

new_logic = []
new_logic.append('def calculate_teacher_stats(teacher_id, start_date, end_date=None, is_sem=False):\n')
new_logic.append('    from ..models import LeaveRequest, Setting, AttendanceLog\n')
new_logic.append('    from datetime import datetime, timedelta, timezone\n')
new_logic.append('    now = datetime.now(timezone.utc)\n')
for line in orig_lines[9:157]:
    new_logic.append(line[4:])

new_logic.append('\n@verify_bp.route("/attendance/stats", methods=["GET"])\n')
new_logic.append('@jwt_required()\n')
new_logic.append('def get_attendance_stats():\n')
new_logic.append('    """GET /attendance/stats - returns attendance statistics for month and semester."""\n')
new_logic.append('    teacher_id = get_jwt_identity()\n')
new_logic.append('    from datetime import datetime, timezone, timedelta\n')
new_logic.append('    now = datetime.now(timezone.utc)\n')
new_logic.append('    from ..models import Setting\n')
for line in orig_lines[158:]:
    new_logic.append(line.replace('get_stats_for_range(', 'calculate_teacher_stats(teacher_id, '))

# Now read the full verify.py and replace lines 337 to 531 (where the mess is)
with open('backend/app/routes/verify.py', 'r', encoding='utf-8') as f:
    verify_lines = f.readlines()

start_idx = -1
for i, line in enumerate(verify_lines):
    if line.startswith('@verify_bp.route("/attendance/stats"') or 'def calculate_teacher_stats' in line:
        start_idx = i
        break

end_idx = -1
for i in range(start_idx + 1, len(verify_lines)):
    if verify_lines[i].startswith('@verify_bp.route('):
        end_idx = i
        break

if end_idx == -1: end_idx = len(verify_lines)

final_lines = verify_lines[:start_idx] + new_logic + verify_lines[end_idx:]

with open('backend/app/routes/verify.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print('Repaired verify.py')
