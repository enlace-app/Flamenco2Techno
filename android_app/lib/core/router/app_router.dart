import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/upload/presentation/screens/upload_screen.dart';
import '../../features/analysis/presentation/screens/analysis_screen.dart';
import '../../features/conversion/presentation/screens/conversion_screen.dart';
import '../../features/conversion/presentation/screens/result_screen.dart';
import '../constants/app_constants.dart';

part 'app_router.g.dart';

/// Provider del router principal de la aplicación.
@riverpod
GoRouter appRouter(AppRouterRef ref) {
  return GoRouter(
    initialLocation: AppRoutes.upload,
    debugLogDiagnostics: true,
    routes: [
      // ── Ruta principal: Subir archivo ──────────────────────────────
      GoRoute(
        path: AppRoutes.upload,
        name: 'upload',
        pageBuilder: (context, state) => _buildPage(
          state: state,
          child: const UploadScreen(),
        ),
      ),

      // ── Análisis del archivo subido ────────────────────────────────
      GoRoute(
        path: AppRoutes.analysis,
        name: 'analysis',
        pageBuilder: (context, state) {
          final jobId = state.pathParameters['jobId']!;
          return _buildPage(
            state: state,
            child: AnalysisScreen(jobId: jobId),
          );
        },
      ),

      // ── Configurar y lanzar conversión ─────────────────────────────
      GoRoute(
        path: AppRoutes.conversion,
        name: 'conversion',
        pageBuilder: (context, state) {
          final jobId = state.pathParameters['jobId']!;
          return _buildPage(
            state: state,
            child: ConversionScreen(jobId: jobId),
          );
        },
      ),

      // ── Resultado: preview y exportación ──────────────────────────
      GoRoute(
        path: AppRoutes.result,
        name: 'result',
        pageBuilder: (context, state) {
          final jobId = state.pathParameters['jobId']!;
          return _buildPage(
            state: state,
            child: ResultScreen(jobId: jobId),
          );
        },
      ),
    ],

    // Manejo global de errores de navegación
    errorBuilder: (context, state) => Scaffold(
      backgroundColor: const Color(0xFF0A0A0F),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Color(0xFFFF006E), size: 64),
            const SizedBox(height: 16),
            Text(
              'RUTA NO ENCONTRADA',
              style: Theme.of(context).textTheme.displaySmall?.copyWith(
                    color: const Color(0xFFFF006E),
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              state.error?.message ?? 'Error desconocido',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(AppRoutes.upload),
              child: const Text('VOLVER AL INICIO'),
            ),
          ],
        ),
      ),
    ),
  );
}

/// Helper para construir páginas con transición personalizada neon
CustomTransitionPage _buildPage({
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 350),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return FadeTransition(
        opacity: CurveTween(curve: Curves.easeInOut).animate(animation),
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0.05, 0),
            end: Offset.zero,
          ).animate(CurveTween(curve: Curves.easeOutCubic).animate(animation)),
          child: child,
        ),
      );
    },
  );
}
