import os, re

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\screens\\verification_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r"if \(provider\.demoMode\)[\s\S]*?DEMO[\s\S]*?\]\),\s*\),\s*\),", "", content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
