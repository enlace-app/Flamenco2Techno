import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';

/// Tarjeta de métrica de análisis con icono, label y valor.
class AnalysisCard extends StatelessWidget {
  const AnalysisCard({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    required this.accent,
    this.fullWidth = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final Color accent;
  final bool fullWidth;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.border),
        boxShadow: [
          BoxShadow(
            color: accent.withOpacity(0.05),
            blurRadius: 12,
            spreadRadius: 0,
          ),
        ],
      ),
      child: fullWidth
          ? Row(
              children: [
                _buildIcon(accent),
                const SizedBox(width: 16),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildLabel(context),
                    const SizedBox(height: 4),
                    _buildValue(context, accent),
                  ],
                ),
              ],
            )
          : Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _buildIcon(accent),
                    const SizedBox(width: 8),
                    _buildLabel(context),
                  ],
                ),
                const SizedBox(height: 12),
                _buildValue(context, accent),
              ],
            ),
    );
  }

  Widget _buildIcon(Color color) {
    return Container(
      width: 36,
      height: 36,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color.withOpacity(0.12),
      ),
      child: Icon(icon, color: color, size: 18),
    );
  }

  Widget _buildLabel(BuildContext context) {
    return Text(
      label,
      style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: AppTheme.textDisabled,
            letterSpacing: 1.5,
            fontSize: 10,
          ),
    );
  }

  Widget _buildValue(BuildContext context, Color color) {
    return Text(
      value,
      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
            color: color,
            fontFamily: 'Orbitron',
          ),
    );
  }
}
