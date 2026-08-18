import os, re

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\providers\\verification_provider.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove state variables and getters and setDemoMode method
content = re.sub(r"// -- Demo Mode --[\s\S]*?notifyListeners\(\);\n  }\n", "", content)

# 2. Remove API service arguments
content = re.sub(r"demoLat:[^\n]*\n", "", content)
content = re.sub(r"demoLng:[^\n]*\n", "", content)
content = re.sub(r"demoRadius:[^\n]*\n", "", content)
content = re.sub(r"bypassLimits: _demoMode && _bypassLimits,", "bypassLimits: _bypassLimits,", content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
