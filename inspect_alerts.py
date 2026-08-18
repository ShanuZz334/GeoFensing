import re

with open("admin/alerts.html", "r", encoding="utf-8") as f:
    html = f.read()

# I want to add a Tabs UI at the top of main content to switch between "System Alerts" and "Leave Requests"
main_header_pattern = r'<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 24px;">.*?</div>\s*</div>'
main_header_match = re.search(main_header_pattern, html, re.DOTALL)

# Let's just add the Leave Requests table below the alerts table
table_section = r'(<div class="card" style="padding: 0; overflow: hidden; background: var\(--surface\); border: 1px solid var\(--border\); border-radius: var\(--radius-lg\);">\s*<table class="data-table">.*?</table>\s*</div>)'

# Read and print the part of HTML to see what to replace
print(re.search(r'<main class="main-content">.*?</main>', html, re.DOTALL).group(0)[:1500])
