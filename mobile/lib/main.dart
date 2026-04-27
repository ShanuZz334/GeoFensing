import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

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

  // Lock portrait orientation
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Transparent system UI overlays
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  runApp(const GeoFaceApp());
}

class GeoFaceApp extends StatelessWidget {
  const GeoFaceApp({super.key});

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
            title: 'GeoFace Auth',
            debugShowCheckedModeBanner: false,
            themeMode: ThemeMode.light,
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.lightTheme,
            initialRoute: AppRoutes.splash,
            routes: {
              AppRoutes.splash: (_) => const SplashScreen(),
              AppRoutes.login: (_) => const LoginScreen(),
              AppRoutes.home: (_) => const HomeScreen(),
              AppRoutes.verification: (_) => const VerificationScreen(),
              AppRoutes.result: (_) => const ResultScreen(),
            },
          );
        },
      ),
    );
  }
}

/// Application route name constants
class AppRoutes {
  static const splash = '/';
  static const login = '/login';
  static const home = '/home';
  static const verification = '/verify';
  static const result = '/result';
}
