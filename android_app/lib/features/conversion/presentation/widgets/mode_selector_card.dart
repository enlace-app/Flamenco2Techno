import 'package:flutter/material.dart';
import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';

/// Tarjeta de selección de modo Techno con descripción y colores únicos.
class ModeSelectorCard extends StatelessWidget {
  const ModeSelectorCard({
    super.key,
    required this.mode,
    required this.isSelected,
    required this.onTap,
  });

  final TechnoMode mode;
  final bool isSelected;
  final VoidCallback onTap;

  Color get _accentColor => switch (mode) {
        TechnoMode.soft => AppTheme.neonGreen,
        TechnoMode.peak => AppTheme.neonCyan,
        TechnoMode.hard => AppTheme.neonMagenta,
      };

  IconData get _icon => switch (mode) {
        TechnoMode.soft => Icons.waves,
        TechnoMode.peak => Icons.bolt,
        TechnoMode.hard => Icons.whatshot,
      };

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: isSelected
              ? _accentColor.withOpacity(0.1)
              : AppTheme.surface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? _accentColor : AppTheme.border,
            width: isSelected ? 1.5 : 1.0,
          ),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: _accentColor.withOpacity(0.15),
                    blurRadius: 16,
                    spreadRadius: 0,
                  ),
                ]
              : null,
        ),
        child: Row(
          children: [
            // Icono del modo
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _accentColor.withOpacity(isSelected ? 0.2 : 0.08),
                border: Border.all(
                  color: _accentColor.withOpacity(isSelected ? 0.5 : 0.2),
                ),
              ),
              child: Icon(
                _icon,
                color: _accentColor,
                size: 24,
              ),
            ),

            const SizedBox(width: 16),

            // Texto
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    mode.displayName.toUpperCase(),
                    style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                          fontWeight: FontWeight.w700,
                          color: isSelected ? _accentColor : AppTheme.textPrimary,
                          letterSpacing: 0.5,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    mode.description,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),

            // Indicador de selección
            AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              width: 20,
              height: 20,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected ? _accentColor : Colors.transparent,
                border: Border.all(
                  color: isSelected ? _accentColor : AppTheme.border,
                  width: 1.5,
                ),
              ),
              child: isSelected
                  ? const Icon(
                      Icons.check,
                      color: Colors.black,
                      size: 12,
                    )
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}
