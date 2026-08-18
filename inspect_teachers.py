import re
with open("admin/teachers.html", "r", encoding="utf-8") as f:
    html = f.read()
modal = re.search(r'<div id="teacherModal".*?</div>\s*</div>\s*</div>', html, re.DOTALL)
if modal:
    print(modal.group(0)[:1500])
