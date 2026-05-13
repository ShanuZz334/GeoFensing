import os, re

files = [
  'lib/features/auth/screens/login_screen.dart',
  'lib/features/auth/screens/splash_screen.dart',
  'lib/features/auth/screens/teacher_register_auth_screen.dart',
  'lib/features/auth/screens/teacher_register_details_screen.dart',
  'lib/features/auth/widgets/demo_setup_dialog.dart',
  'lib/features/verification/screens/attendance_stats_screen.dart',
  'lib/features/verification/screens/verification_screen.dart',
  'lib/shared/widgets/app_widgets.dart'
]

for f in files:
    path = os.path.join('C:\\project\\ALLBACKUP\\GeoFense\\mobile', f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if 'GearLoader' not in content:
        import_stmt = "import 'package:geoface_auth/core/widgets/gear_loader.dart';\n"
        last_import = content.rfind('import ')
        end_of_last_import = content.find('\n', last_import)
        content = content[:end_of_last_import+1] + import_stmt + content[end_of_last_import+1:]
        
    content = re.sub(r'const SizedBox\([^)]+child:\s*CircularProgressIndicator\([^)]*\)\)', 'const GearLoader(size: 20, color: Colors.white)', content)
    content = re.sub(r'SizedBox\([^)]+child:\s*CircularProgressIndicator\([^)]*\),?\s*\)', 'const GearLoader(size: 20, color: Colors.white)', content)
    content = re.sub(r'CircularProgressIndicator\(\s*color:\s*Colors\.white\s*,\s*strokeWidth:\s*2\s*\)', 'GearLoader(size: 20, color: Colors.white)', content)
    content = re.sub(r'CircularProgressIndicator\([^)]*\)', 'GearLoader(size: 40)', content)
    
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)
