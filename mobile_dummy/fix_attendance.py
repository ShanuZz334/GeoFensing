import os
import re

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\screens\\attendance_stats_screen.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("? const Center(child: GearLoader(size: 40))", "? const Center(child: CircularProgressIndicator())")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
