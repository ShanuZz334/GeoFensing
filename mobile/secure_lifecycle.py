import os
import re

path = 'C:\\project\\ALLBACKUP\\GeoFense\\mobile\\lib\\main.dart'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add GlobalKey
if 'final GlobalKey<NavigatorState> navigatorKey' not in content:
    content = content.replace('runApp(const GeoFaceApp());', 'runApp(const GeoFaceApp());\n}\n\nfinal GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();')

# Change GeoFaceApp to StatefulWidget
if 'class GeoFaceApp extends StatelessWidget' in content:
    old_class = '''class GeoFaceApp extends StatelessWidget {
  const GeoFaceApp({super.key});

  @override
  Widget build(BuildContext context) {'''
    
    new_class = '''class GeoFaceApp extends StatefulWidget {
  const GeoFaceApp({super.key});

  @override
  State<GeoFaceApp> createState() => _GeoFaceAppState();
}

class _GeoFaceAppState extends State<GeoFaceApp> with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.paused || state == AppLifecycleState.detached) {
      // Force logout when app goes to background
      final auth = Provider.of<AuthProvider>(context, listen: false);
      auth.logout();
      navigatorKey.currentState?.pushNamedAndRemoveUntil('/login', (route) => false);
    }
  }

  @override
  Widget build(BuildContext context) {'''
    
    content = content.replace(old_class, new_class)
    
    # Add navigatorKey to MaterialApp
    content = content.replace("title: 'GeoFace Auth',", "navigatorKey: navigatorKey,\n            title: 'GeoFace Auth',")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Lifecycle security applied')
