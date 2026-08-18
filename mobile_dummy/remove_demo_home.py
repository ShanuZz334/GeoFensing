import os, re

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\screens\\home_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove import
content = re.sub(r"import '../../auth/widgets/demo_setup_dialog.dart';\n", "", content)

# 2. Remove InkWell (play icon)
content = re.sub(r"const SizedBox\(width: 4\),\s*InkWell\([\s\S]*?size: 16\),\s*\),", "", content)

# 3. Remove DEMO badge block
# Find 'if (context.watch<VerificationProvider>().demoMode)' and remove the whole block
content = re.sub(r"if \(context\.watch<VerificationProvider>\(\)\.demoMode\)[\s\S]*?DEMO[\s\S]*?\]\),", "", content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
