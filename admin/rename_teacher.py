import os
import glob
import re

directories = [
    r"C:\project\ALLBACKUP\GeoFense\admin",
    r"C:\project\ALLBACKUP\GeoFense\admin\js"
]

replacements = {
    r">Teacher<": ">Faculty<",
    r">Teachers<": ">Faculty<",
    r"Teacher(s)": "Faculty",
    r"Teachers": "Faculty",
    r"Active Teachers": "Active Faculty",
    r"Teacher \(A-Z\)": "Faculty (A-Z)",
    r"Teacher \(Z-A\)": "Faculty (Z-A)",
    r"Teacher Reg No": "Faculty Reg No",
    r"Register Teacher": "Register Faculty",
    r"Add Teacher": "Add Faculty",
    r"Edit Teacher": "Edit Faculty",
    r"Delete Teacher": "Delete Faculty",
    r"Teacher App Login": "Faculty App Login",
    r"GeoFace Teacher App": "GeoFace Faculty App",
    r"Teacher Profile": "Faculty Profile",
    r"Teacher Registration": "Faculty Registration",
    r"Teacher name": "Faculty name",
    r"Select Teacher": "Select Faculty",
    r"Teacher Details": "Faculty Details",
    r"teacher's": "faculty's",
    r"Teacher's": "Faculty's",
    r"teacher profile": "faculty profile",
    r"teacher credentials": "faculty credentials",
    r"Teacher Credentials": "Faculty Credentials",
    r"new teacher": "new faculty",
    r"New Teacher": "New Faculty",
    r"Registered Teacher": "Registered Faculty",
    r"Delete Teacher": "Delete Faculty",
}

for d in directories:
    for filepath in glob.glob(os.path.join(d, "*.*")):
        if filepath.endswith('.html') or filepath.endswith('.js') or filepath.endswith('.css'):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old, new in replacements.items():
                content = re.sub(old, new, content)
                
            # Extra manual replacements for specific tags without regex issues
            content = content.replace("Teacher</th>", "Faculty</th>")
            content = content.replace("Teacher(s)</th>", "Faculty</th>")
            content = content.replace("Teacher</div>", "Faculty</div>")
            content = content.replace("Teachers</div>", "Faculty</div>")
            content = content.replace("Teacher</span>", "Faculty</span>")
            content = content.replace("Teachers</span>", "Faculty</span>")
            content = content.replace("Teacher</a>", "Faculty</a>")
            content = content.replace("Teachers</a>", "Faculty</a>")
            content = content.replace("> Teachers <", "> Faculty <")
            content = content.replace("> Teacher <", "> Faculty <")
            content = content.replace('"Teacher"', '"Faculty"')
            content = content.replace('"Teachers"', '"Faculty"')
            content = content.replace("'Teacher'", "'Faculty'")
            content = content.replace("'Teachers'", "'Faculty'")
            content = content.replace("Teacher ", "Faculty ")
            content = content.replace("Teachers ", "Faculty ")
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {os.path.basename(filepath)}")

print("Done")
