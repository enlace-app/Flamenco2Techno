import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Barra de progreso con efecto neon glow.
class NeonProgressBar extends StatelessWidget {
  const NeonProgressBar({
    super.key,
    required this.progress,
    this.height = 6.0,
    this.color = AppTheme.neonCyan,
    this.showGlow = true,
  });

  final double progress; // 0.0 a 1.0
  final double height;
  final Color color;
  final bool showGlow;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: AppTheme.border,
        borderRadius: BorderRadius.circular(height / 2),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final filledWidth = constraints.maxWidth * progress.clamp(0.0, 1.0);
          return Stack(
            children: [
              // Barra llena
              AnimatedContainer(
                duration: const Duration(milliseconds: 300),
                width: filledWidth,
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [color.withOpacity(0.8), color],
                  ),
                  borderRadius: BorderRadius.circular(height / 2),
                  boxShadow: showGlow
                      ? [
                          BoxShadow(
                            color: color.withOpacity(0.6),
                            blurRadius: 8,
                            spreadRadius: 1,
                          ),
                        ]
                      : null,
                ),
              ),

              // Punto final brillante
              if (progress > 0.02)
                AnimatedPositioned(
                  duration: const Duration(milliseconds: 300),
                  left: filledWidth - height * 1.5,
                  top: -height * 0.5,
                  child: Container(
                    width: height * 2,
                    height: height * 2,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: color,
                      boxShadow: showGlow
                          ? [
                              BoxShadow(
                                color: color.withOpacity(0.8),
                                blurRadius: 6,
                                spreadRadius: 1,
                              ),
                            ]
                          : null,
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
