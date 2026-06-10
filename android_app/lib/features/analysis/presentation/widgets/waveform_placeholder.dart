import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../core/theme/app_theme.dart';

/// Placeholder visual de forma de onda que simula la onda de audio.
class WaveformPlaceholder extends StatelessWidget {
  const WaveformPlaceholder({super.key, required this.durationSeconds});

  final double durationSeconds;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 80,
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: CustomPaint(
          painter: _WaveformPainter(),
          child: Align(
            alignment: Alignment.bottomRight,
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Text(
                _formatDuration(durationSeconds),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppTheme.neonCyan,
                      fontFamily: 'Orbitron',
                      fontSize: 11,
                    ),
              ),
            ),
          ),
        ),
      ),
    )
        .animate()
        .fadeIn(duration: 600.ms)
        .shimmer(delay: 300.ms, duration: 800.ms, color: AppTheme.neonCyan.withOpacity(0.1));
  }

  String _formatDuration(double seconds) {
    final mins = (seconds / 60).floor();
    final secs = (seconds % 60).floor();
    return '${mins.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
}

class _WaveformPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppTheme.neonCyan.withOpacity(0.4)
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    final random = math.Random(42); // seed fijo para consistencia visual
    final barCount = (size.width / 4).floor();
    final barWidth = size.width / barCount;
    final centerY = size.height / 2;

    for (int i = 0; i < barCount; i++) {
      final x = i * barWidth + barWidth / 2;
      final height = (random.nextDouble() * 0.7 + 0.1) * (size.height / 2);
      final opacity = 0.3 + random.nextDouble() * 0.7;

      paint.color = AppTheme.neonCyan.withOpacity(opacity * 0.5);
      canvas.drawLine(
        Offset(x, centerY - height),
        Offset(x, centerY + height),
        paint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
