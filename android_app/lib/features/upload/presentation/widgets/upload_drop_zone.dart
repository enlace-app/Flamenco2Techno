import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../../../../core/theme/app_theme.dart';

/// Zona visual para soltar/seleccionar archivos de audio.
/// Muestra animación de pulso con el color neon cyan.
class UploadDropZone extends StatelessWidget {
  const UploadDropZone({
    super.key,
    required this.onFilePicked,
    required this.pulseController,
  });

  final VoidCallback onFilePicked;
  final AnimationController pulseController;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onFilePicked,
      child: AnimatedBuilder(
        animation: pulseController,
        builder: (context, child) {
          final pulseValue = pulseController.value;
          return Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: AppTheme.surface,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: Color.lerp(
                  AppTheme.neonCyan.withOpacity(0.3),
                  AppTheme.neonCyan.withOpacity(0.7),
                  pulseValue,
                )!,
                width: 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: AppTheme.neonCyan.withOpacity(0.05 + 0.05 * pulseValue),
                  blurRadius: 24 + 8 * pulseValue,
                  spreadRadius: 0,
                ),
              ],
            ),
            child: child,
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(40),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Icono principal
              Container(
                width: 96,
                height: 96,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      AppTheme.neonCyan.withOpacity(0.15),
                      AppTheme.neonCyan.withOpacity(0.02),
                    ],
                  ),
                  border: Border.all(
                    color: AppTheme.neonCyan.withOpacity(0.4),
                    width: 1.5,
                  ),
                ),
                child: const Icon(
                  Icons.music_note,
                  color: AppTheme.neonCyan,
                  size: 44,
                ),
              )
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .scale(
                    begin: const Offset(1.0, 1.0),
                    end: const Offset(1.05, 1.05),
                    duration: 2000.ms,
                    curve: Curves.easeInOut,
                  ),

              const SizedBox(height: 24),

              Text(
                'SELECCIONAR ARCHIVO',
                style: Theme.of(context).textTheme.labelLarge?.copyWith(
                      fontSize: 15,
                    ),
              ),

              const SizedBox(height: 8),

              Text(
                'Toca aquí para abrir el explorador\nde archivos de tu dispositivo',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      height: 1.5,
                    ),
                textAlign: TextAlign.center,
              ),

              const SizedBox(height: 32),

              // Separador "O"
              Row(
                children: [
                  Expanded(
                    child: Divider(
                      color: AppTheme.border.withOpacity(0.6),
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(
                      'O',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: AppTheme.textDisabled,
                            letterSpacing: 2.0,
                          ),
                    ),
                  ),
                  Expanded(
                    child: Divider(
                      color: AppTheme.border.withOpacity(0.6),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 24),

              // Tips de formatos
              Wrap(
                spacing: 12,
                runSpacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  _buildTipChip(context, Icons.audio_file, 'MP3'),
                  _buildTipChip(context, Icons.audio_file, 'WAV'),
                  _buildTipChip(context, Icons.audio_file, 'FLAC'),
                ],
              ),

              const SizedBox(height: 16),

              Text(
                'Tamaño máximo: 100 MB',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.textDisabled,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTipChip(BuildContext context, IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: AppTheme.surfaceVariant,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppTheme.border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: AppTheme.neonCyan),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppTheme.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
          ),
        ],
      ),
    );
  }
}
