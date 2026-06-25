import os, re

admin_dir = 'C:\\project\\ALLBACKUP\\GeoFense\\admin'
for file in os.listdir(admin_dir):
    if file.endswith('.html'):
        path = os.path.join(admin_dir, file)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        content = re.sub(r'(<td[^>]*class=["\'][^"\']*td-loading[^"\']*["\'][^>]*>)Loading[^<]*(</td>)', r'\g<1><div class="gear-loader"></div>\g<2>', content)
        
        # Also replace "Loading&hellip;" or "Loading..." inside p tags if it has id="current-date"
        content = re.sub(r'(<p[^>]*id=["\']current-date["\'][^>]*>)Loading[^<]*(</p>)', r'\g<1><div class="gear-loader"></div>\g<2>', content)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
