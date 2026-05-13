import os
import glob
import re

lib_dir = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib'
for root, _, files in os.walk(lib_dir):
    for file in files:
        if file.endswith('.dart'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'GearLoader' in content:
                # Remove imports
                content = re.sub(r"import\s+'package:geoface_auth/core/widgets/gear_loader\.dart';\n", "", content)
                content = re.sub(r"import\s+'[^']*gear_loader\.dart';\n", "", content)
                
                # Replace specific sizes/colors
                content = re.sub(
                    r"const GearLoader\(size: 20, color: Color\(0xFF9F00FF\)\)",
                    "const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF9F00FF)))",
                    content
                )
                content = re.sub(
                    r"const GearLoader\(size: 20, color: Colors\.white\)",
                    "const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))",
                    content
                )
                content = re.sub(
                    r"GearLoader\(size: (\d+),\s*color:\s*(.*?)\)",
                    r"CircularProgressIndicator(color: \2)",
                    content
                )
                content = re.sub(
                    r"const GearLoader\(size: (\d+),\s*color:\s*(.*?)\)",
                    r"const CircularProgressIndicator(color: \2)",
                    content
                )
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

print('Done removing GearLoader')
