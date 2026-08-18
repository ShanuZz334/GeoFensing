import glob
import re

files = glob.glob('admin/*.html')
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update app.js cache buster
    new_content = re.sub(r'src="js/app\.js(\?[^"]+)?"', 'src="js/app.js?v=1028"', content)
    
    # Update api.js cache buster to be safe
    new_content = re.sub(r'src="js/api\.js(\?[^"]+)?"', 'src="js/api.js?v=1028"', new_content)
    
    # Update css/styles.css cache buster
    new_content = re.sub(r'href="css/styles\.css(\?[^"]+)?"', 'href="css/styles.css?v=1028"', new_content)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")
