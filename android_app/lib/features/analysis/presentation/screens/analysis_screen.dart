import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/providers/api_client.dart';
import '../providers/analysis_provider.dart';
import '../widgets/analysis_card.dart';
import '../widgets/waveform_placeholder.dart';

/// Pantalla que muestra el análisis musical del archivo subido:
/// BPM, tonalidad, stems detectados y estructura.
class AnalysisScreen extends ConsumerWidget {
  const AnalysisScreen({super.key, required this.jobId});

  final String jobId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final analysisAsync = ref.watch(analysisProvider(jobId));

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => context.go(AppRoutes.upload),
        ),
        title: const Text('ANÁLISIS MUSICAL'),
      ),
      body: analysisAsync.when(
        loading: () => _buildLoading(context),
        error: (e, st) => _buildError(context, e.toString()),
        data: (analysis) => _buildResult(context, analysis, ref),
      ),
    );
  }

  // ── Loading ────────────────────────────────────────────────────────

  Widget _buildLoading(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Animación de análisis
          SizedBox(
            width: 80,
            height: 80,
            child: Stack(
              alignment: Alignment.center,
              children: [
                for (int i = 0; i < 3; i++)
                  Container(
                    width: 80.0 - i * 20,
                    height: 80.0 - i * 20,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: AppTheme.neonCyan.withOpacity(0.4 - i * 0.1),
                        width: 1.5,
                      ),
                    ),
                  )
                      .animate(onPlay: (c) => c.repeat())
                      .scale(
                        begin: const Offset(0.8, 0.8),
                        end: const Offset(1.2, 1.2),
                        duration: Duration(milliseconds: 1200 + i * 200),
                        curve: Curves.easeInOut,
                      )
                      .fadeIn(),
                const Icon(
                  Icons.equalizer,
                  color: AppTheme.neonCyan,
                  size: 28,
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'ANALIZANDO',
            style: Theme.of(context).textTheme.labelLarge,
          )
              .animate(onPlay: (c) => c.repeat(reverse: true))
              .fadeIn(duration: 800.ms),
          const SizedBox(height: 8),
          Text(
            'Detectando BPM, tonalidad y estructura...',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }

  // ── Error ──────────────────────────────────────────────────────────

  Widget _buildError(BuildContext context, String error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppConstants.padding),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: AppTheme.neonMagenta, size: 64),
            const SizedBox(height: 16),
            Text(
              'Error en el análisis',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(error, textAlign: TextAlign.center),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.go(AppRoutes.upload),
              child: const Text('VOLVER'),
            ),
          ],
        ),
      ),
    );
  }

  // ── Result ─────────────────────────────────────────────────────────

  Widget _buildResult(
    BuildContext context,
    AnalysisResult analysis,
    WidgetRef ref,
  ) {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(AppConstants.padding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Waveform placeholder
                WaveformPlaceholder(durationSeconds: analysis.durationSeconds),

                const SizedBox(height: 24),

                Text(
                  'RESULTADOS',
                  style: Theme.of(context).textTheme.labelLarge,
                ).animate().fadeIn(delay: 200.ms),

                const SizedBox(height: 16),

                // Grid de métricas
                Row(
                  children: [
                    Expanded(
                      child: AnalysisCard(
                        icon: Icons.speed,
                        label: 'BPM',
                        value: analysis.bpm.toStringAsFixed(1),
                        accent: AppTheme.neonCyan,
                      ).animate().fadeIn(delay: 300.ms).slideY(begin: 0.3),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: AnalysisCard(
                        icon: Icons.music_note,
                        label: 'TONALIDAD',
                        value: '${analysis.key} ${analysis.scale}',
                        accent: AppTheme.neonMagenta,
                      ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.3),
                    ),
                  ],
                ),

                const SizedBox(height: 12),

                // Stems detectados
                _buildStemsCard(context, analysis),

                const SizedBox(height: 12),

                // Duración
                AnalysisCard(
                  icon: Icons.timer_outlined,
                  label: 'DURACIÓN',
                  value: _formatDuration(analysis.durationSeconds),
                  accent: AppTheme.neonGreen,
                  fullWidth: true,
                ).animate().fadeIn(delay: 600.ms).slideY(begin: 0.3),

                const SizedBox(height: 12),

                // Estructura
                if (analysis.structureSections.isNotEmpty)
                  _buildStructureCard(context, analysis),

                const SizedBox(height: 32),

                // Info de conversión
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppTheme.neonCyan.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: AppTheme.neonCyan.withOpacity(0.2),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.info_outline,
                        color: AppTheme.neonCyan,
                        size: 20,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'El BPM será ajustado al rango ${AppConstants.bpmMin}-${AppConstants.bpmMax} BPM durante la conversión',
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppTheme.neonCyan.withOpacity(0.8),
                              ),
                        ),
                      ),
                    ],
                  ),
                ).animate().fadeIn(delay: 700.ms),

                const SizedBox(height: 32),

                // Botón continuar
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      context.go(AppRoutes.conversionRoute(jobId));
                    },
                    icon: const Icon(Icons.arrow_forward),
                    label: const Text('CONFIGURAR CONVERSIÓN'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ).animate().fadeIn(delay: 800.ms),
                ),

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStemsCard(BuildContext context, AnalysisResult analysis) {
    final stems = {
      'Voz': (analysis.vocalsDetected, Icons.mic_none),
      'Batería': (analysis.drumsDetected, Icons.drum),
      'Bajo': (analysis.bassDetected, Icons.queue_music),
    };

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'STEMS DETECTADOS',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
          ),
          const SizedBox(height: 12),
          Row(
            children: stems.entries.map((entry) {
              final (detected, icon) = entry.value;
              return Expanded(
                child: Column(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: detected
                            ? AppTheme.neonGreen.withOpacity(0.12)
                            : AppTheme.border.withOpacity(0.5),
                        border: Border.all(
                          color: detected
                              ? AppTheme.neonGreen.withOpacity(0.4)
                              : AppTheme.border,
                        ),
                      ),
                      child: Icon(
                        icon,
                        color: detected
                            ? AppTheme.neonGreen
                            : AppTheme.textDisabled,
                        size: 22,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      entry.key,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: detected
                                ? AppTheme.textSecondary
                                : AppTheme.textDisabled,
                          ),
                    ),
                    Text(
                      detected ? 'Detectado' : 'No hallado',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            fontSize: 10,
                            color: detected
                                ? AppTheme.neonGreen
                                : AppTheme.textDisabled,
                          ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    ).animate().fadeIn(delay: 500.ms).slideY(begin: 0.3);
  }

  Widget _buildStructureCard(BuildContext context, AnalysisResult analysis) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'ESTRUCTURA',
            style: Theme.of(context).textTheme.labelLarge?.copyWith(
                  fontSize: 11,
                  color: AppTheme.textSecondary,
                ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: analysis.structureSections.map((section) {
              return Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: AppTheme.surfaceVariant,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppTheme.border),
                ),
                child: Text(
                  section.toUpperCase(),
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        fontWeight: FontWeight.w600,
                        letterSpacing: 1.0,
                      ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    ).animate().fadeIn(delay: 650.ms).slideY(begin: 0.3);
  }

  String _formatDuration(double seconds) {
    final mins = (seconds / 60).floor();
    final secs = (seconds % 60).floor();
    return '${mins}m ${secs.toString().padLeft(2, '0')}s';
  }
}
