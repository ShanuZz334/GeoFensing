import os

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\features\\verification\\providers\\verification_provider.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the synchronous call with the compute call
content = content.replace("final compressed = _compressFrame(bytes);", "final compressed = await compute(_compressFrameTask, bytes);")

# Replace the method signature to be static
content = content.replace("Uint8List? _compressFrame(Uint8List rawBytes) {", "static Uint8List? _compressFrameTask(Uint8List rawBytes) {")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Optimized for smooth UI')
