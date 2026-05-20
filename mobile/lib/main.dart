import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import 'core/services/remote_config_service.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/providers/auth_provider.dart';
import 'features/auth/screens/splash_screen.dart';
import 'features/auth/screens/login_screen.dart';
import 'features/verification/providers/verification_provider.dart';
import 'features/verification/screens/home_screen.dart';
import 'features/verification/screens/verification_screen.dart';
import 'features/verification/screens/result_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Fetch live server URL from GitHub (updates without APK rebuild)
  await RemoteConfigService.initialize();

  try {
    await SystemChrome.setPreferredOrientations([
      DeviceOrientation.portraitUp,
      DeviceOrientation.portraitDown,
    ]);

    SystemChrome.setSystemUIOverlayStyle(
      const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.dark,
      ),
    );
  } catch (_) {
    // Ignore on unsupported platforms (e.g. Web)
  }

  runApp(const GeoFaceApp());
}

final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

class GeoFaceApp extends StatefulWidget {
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
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => VerificationProvider()),
      ],
      child: Consumer<AuthProvider>(
        builder: (context, auth, _) {
          return MaterialApp(
            navigatorKey: navigatorKey,
            title: 'GeoFace Auth',
            debugShowCheckedModeBanner: false,
            themeMode: ThemeMode.light,
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.lightTheme,
            initialRoute: '/splash',
            routes: {
              '/splash': (_) => const SplashScreen(),
              '/login': (_) => const LoginScreen(),
              '/home': (_) => const HomeScreen(),
              '/verification': (_) => const VerificationScreen(),
              '/result': (_) => const ResultScreen(),
            },
          );
        },
      ),
    );
  }
}
