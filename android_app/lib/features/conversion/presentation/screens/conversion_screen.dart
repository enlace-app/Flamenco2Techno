import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../providers/conversion_provider.dart';
import '../widgets/mode_selector_card.dart';
import '../../upload/presentation/widgets/neon_progress_bar.dart';

/// Pantalla de configuración y ejecución de la conversión a Techno.
class ConversionScreen extends ConsumerStatefulWidget {
  const ConversionScreen({super.key, required this.jobId});

  final String jobId;

  @override
  ConsumerState<ConversionScreen> createState() => _ConversionScreenState();
}

class _ConversionScreenState extends ConsumerState<ConversionScreen> {
  TechnoMode _selectedMode = TechnoMode.peak;
  bool _keepVocals = true;
  String _exportFormat = 'mp3';
  int _targetBpm = 130;

  @override
  Widget build(BuildContext context) {
    final conversionState = ref.watch(conversionNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: conversionState.maybeWhen(
            converting: (_) => null, // Deshabilitar durante conversión
            orElse: () => () => context.go(
                  AppRoutes.analysisRoute(widget.jobId),
                ),
          ),
        ),
        title: const Text('CONFIGURAR'),
      ),
      body: conversionState.when(
        idle: () => _buildConfigContent(),
        converting: (progress) => _buildConvertingContent(progress),
        error: (msg) => _buildErrorContent(msg),
        success: (convId) => _buildSuccessContent(convId),
      ),
    );
  }

  // ── Config ─────────────────────────────────────────────────────────

  Widget _buildConfigContent() {
    return CustomScrollView(
      slivers: [
        SliverToBoxAdapter(
          child: Padding(
            padding: const EdgeInsets.all(AppConstants.padding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'MODO TECHNO',
                  style: Theme.of(context).textTheme.labelLarge,
                ).animate().fadeIn(),

                const SizedBox(height: 4),

                Text(
                  'Selecciona el estilo de conversión',
                  style: Theme.of(context).textTheme.bodyMedium,
                ).animate().fadeIn(delay: 100.ms),

                const SizedBox(height: 20),

                // Selector de modo
                ...TechnoMode.values.asMap().entries.map((entry) {
                  final idx = entry.key;
                  final mode = entry.value;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: ModeSelectorCard(
                      mode: mode,
                      isSelected: _selectedMode == mode,
                      onTap: () => setState(() => _selectedMode = mode),
                    ).animate().fadeIn(delay: Duration(milliseconds: 200 + idx * 100)).slideX(begin: 0.2),
                  );
                }),

                const SizedBox(height: 24),

                // Opciones adicionales
                Text(
                  'OPCIONES',
                  style: Theme.of(context).textTheme.labelLarge,
                ).animate().fadeIn(delay: 500.ms),

                const SizedBox(height: 16),

                // Toggle: mantener voz
                _buildToggleTile(
                  icon: Icons.mic,
                  title: 'Mantener voz original',
                  subtitle: 'Usa Demucs para preservar la voz',
                  value: _keepVocals,
                  onChanged: (v) => setState(() => _keepVocals = v),
                  delay: 550,
                ),

                const SizedBox(height: 12),

                // BPM target slider
                _buildBpmSlider(),

                const SizedBox(height: 12),

                // Formato de exportación
                _buildFormatSelector(),

                const SizedBox(height: 32),

                // Botón principal
                SizedBox(
                  width: double.infinity,
                  child: Container(
                    decoration: BoxDecoration(
                      gradient: AppTheme.technoGradient,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.neonCyan.withOpacity(0.3),
                          blurRadius: 20,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: ElevatedButton.icon(
                      onPressed: _startConversion,
                      icon: const Icon(Icons.play_arrow_rounded),
                      label: const Text('INICIAR CONVERSIÓN'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.transparent,
                        shadowColor: Colors.transparent,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ).animate().fadeIn(delay: 700.ms),
                ),

                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildToggleTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required bool value,
    required ValueChanged<bool> onChanged,
    int delay = 0,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: SwitchListTile(
        secondary: Icon(icon, color: AppTheme.neonCyan, size: 22),
        title: Text(title, style: Theme.of(context).textTheme.bodyLarge),
        subtitle: Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
        value: value,
        onChanged: onChanged,
        activeColor: AppTheme.neonCyan,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      ),
    ).animate().fadeIn(delay: Duration(milliseconds: delay));
  }

  Widget _buildBpmSlider() {
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
          Row(
            children: [
              const Icon(Icons.speed, color: AppTheme.neonMagenta, size: 22),
              const SizedBox(width: 12),
              Text('TARGET BPM', style: Theme.of(context).textTheme.bodyLarge),
              const Spacer(),
              Text(
                '$_targetBpm',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: AppTheme.neonMagenta,
                      fontFamily: 'Orbitron',
                    ),
              ),
            ],
          ),
          Slider(
            value: _targetBpm.toDouble(),
            min: AppConstants.bpmMin.toDouble(),
            max: AppConstants.bpmMax.toDouble(),
            divisions: AppConstants.bpmMax - AppConstants.bpmMin,
            onChanged: (v) => setState(() => _targetBpm = v.round()),
            activeColor: AppTheme.neonMagenta,
            thumbColor: AppTheme.neonMagenta,
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('${AppConstants.bpmMin} BPM',
                  style: Theme.of(context).textTheme.bodySmall),
              Text('${AppConstants.bpmMax} BPM',
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ],
< truncated lines 234-267 >
                        color: _exportFormat == fmt
                            ? AppTheme.neonGreen.withOpacity(0.15)
                            : AppTheme.surfaceVariant,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                          color: _exportFormat == fmt
                              ? AppTheme.neonGreen
                              : AppTheme.border,
                        ),
                      ),
                      child: Column(
                        children: [
                          Text(
                            fmt.toUpperCase(),
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                  color: _exportFormat == fmt
                                      ? AppTheme.neonGreen
                                      : AppTheme.textSecondary,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.5,
                                ),
                          ),
                          Text(
                            fmt == 'mp3' ? '320 kbps' : 'Lossless',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
                if (fmt != 'wav') const SizedBox(width: 12),
              ],
            ],
          ),
        ],
      ),
    ).animate().fadeIn(delay: 650.ms);
  }

  // ── Converting ─────────────────────────────────────────────────────

  Widget _buildConvertingContent(ConversionProgress progress) {
    return Padding(
      padding: const EdgeInsets.all(AppConstants.padding),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Animación central
          SizedBox(
            width: 120,
            height: 120,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: progress.overall,
                  strokeWidth: 3,
                  color: AppTheme.neonCyan,
                  backgroundColor: AppTheme.border,
                ),
                Text(
                  '${(progress.overall * 100).toInt()}%',
                  style: Theme.of(context).textTheme.displaySmall?.copyWith(
                        color: AppTheme.neonCyan,
                      ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 32),

          Text(
            'CONVIRTIENDO',
            style: Theme.of(context).textTheme.labelLarge,
          ),

          const SizedBox(height: 8),

          Text(
            progress.currentStep,
            style: Theme.of(context).textTheme.bodyMedium,
            textAlign: TextAlign.center,
          )
              .animate(key: ValueKey(progress.currentStep))
              .fadeIn(duration: 300.ms),

          const SizedBox(height: 40),

          // Pasos del proceso
          _buildConversionSteps(progress),

          const SizedBox(height: 40),

          Text(
            'Este proceso puede tardar 2-5 minutos\nsegún la duración del audio',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textDisabled,
                ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildConversionSteps(ConversionProgress progress) {
    final steps = [
      ('Separando stems', JobStatus.separating),
      ('Generando batería techno', JobStatus.generating),
      ('Procesando efectos', JobStatus.mixing),
      ('Exportando audio', JobStatus.exporting),
    ];

    return Column(
      children: steps.map((step) {
        final (label, status) = step;
        final isActive = progress.status == status;
        final isDone = progress.status.index > status.index;

        return Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(
            children: [
              Container(
                width: 28,
                height: 28,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: isDone
                      ? AppTheme.neonGreen.withOpacity(0.15)
                      : isActive
                          ? AppTheme.neonCyan.withOpacity(0.15)
                          : AppTheme.border.withOpacity(0.3),
                  border: Border.all(
                    color: isDone
                        ? AppTheme.neonGreen
                        : isActive
                            ? AppTheme.neonCyan
                            : AppTheme.border,
                    width: 1.5,
                  ),
                ),
                child: Icon(
                  isDone ? Icons.check : isActive ? Icons.hourglass_top : Icons.circle,
                  size: 14,
                  color: isDone
                      ? AppTheme.neonGreen
                      : isActive
                          ? AppTheme.neonCyan
                          : AppTheme.textDisabled,
                ),
              ),
              const SizedBox(width: 12),
              Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: isDone || isActive
                          ? AppTheme.textPrimary
                          : AppTheme.textDisabled,
                    ),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  // ── Error ──────────────────────────────────────────────────────────

  Widget _buildErrorContent(String message) {
    return Padding(
      padding: const EdgeInsets.all(AppConstants.padding),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, color: AppTheme.neonMagenta, size: 64),
          const SizedBox(height: 16),
          Text('ERROR EN CONVERSIÓN',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: AppTheme.neonMagenta,
                  )),
          const SizedBox(height: 8),
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => ref.read(conversionNotifierProvider.notifier).reset(),
                  child: const Text('REINTENTAR'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => context.go(AppRoutes.upload),
                  child: const Text('NUEVO ARCHIVO'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ── Success ────────────────────────────────────────────────────────

  Widget _buildSuccessContent(String conversionId) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.go(AppRoutes.resultRoute(conversionId));
    });
    return const Center(
      child: CircularProgressIndicator(color: AppTheme.neonGreen),
    );
  }

  // ── Actions ────────────────────────────────────────────────────────

  void _startConversion() {
    ref.read(conversionNotifierProvider.notifier).startConversion(
          jobId: widget.jobId,
          mode: _selectedMode,
          keepVocals: _keepVocals,
          targetBpm: _targetBpm,
          exportFormat: _exportFormat,
        );
  }
}
