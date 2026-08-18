import os

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\providers\\verification_provider.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("final compressed = _compressFrame(bytes);", "final compressed = await compute(_compressFrameTask, bytes);")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
