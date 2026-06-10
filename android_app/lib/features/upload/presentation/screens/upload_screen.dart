import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:file_picker/file_picker.dart';
import 'package:permission_handler/permission_handler.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/providers/api_client.dart';
import '../widgets/upload_drop_zone.dart';
import '../widgets/neon_progress_bar.dart';
import '../providers/upload_provider.dart';

/// Pantalla principal de carga de archivo de audio.
/// Permite seleccionar un MP3/WAV/FLAC y subirlo al backend.
class UploadScreen extends ConsumerStatefulWidget {
  const UploadScreen({super.key});

  @override
  ConsumerState<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends ConsumerState<UploadScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  // ── Selección de archivo ─────────────────────────────────────────

  Future<void> _pickFile() async {
    // Solicitar permiso de almacenamiento en Android < 13
    if (Platform.isAndroid) {
      final status = await Permission.audio.request();
      if (!status.isGranted) {
        if (mounted) {
          _showError('Se necesita permiso para acceder al audio');
        }
        return;
      }
    }

    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: AppConstants.allowedExtensions,
        allowMultiple: false,
        withData: false,
        withReadStream: false,
      );

      if (result == null || result.files.isEmpty) return;

      final picked = result.files.first;
      if (picked.path == null) {
        _showError('No se pudo acceder al archivo');
        return;
      }

      final file = File(picked.path!);
      await _validateAndUpload(file);
    } catch (e) {
      _showError('Error al seleccionar archivo: $e');
    }
  }

  Future<void> _validateAndUpload(File file) async {
    // Validar tamaño
    final size = await file.length();
    if (size > AppConstants.maxFileSizeBytes) {
      _showError(
        'El archivo es demasiado grande.\nMáximo ${AppConstants.maxFileSizeMb} MB.',
      );
      return;
    }

    // Validar extensión
    final ext = file.path.split('.').last.toLowerCase();
    if (!AppConstants.allowedExtensions.contains(ext)) {
      _showError(
        'Formato no compatible.\nUsa MP3, WAV o FLAC.',
      );
      return;
    }

    // Subir al backend
    final notifier = ref.read(uploadNotifierProvider.notifier);
    final jobId = await notifier.uploadFile(file);

    if (jobId != null && mounted) {
      context.go(AppRoutes.analysisRoute(jobId));
    }
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            const Icon(Icons.error_outline, color: AppTheme.neonMagenta),
            const SizedBox(width: 12),
            Expanded(child: Text(message)),
          ],
        ),
        backgroundColor: AppTheme.surfaceVariant,
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final uploadState = ref.watch(uploadNotifierProvider);

    return Scaffold(
      body: Stack(
        children: [
          // Fondo con gradiente y efectos
          _buildBackground(),

          // Contenido principal
          SafeArea(
            child: CustomScrollView(
              slivers: [
                // Header
                SliverToBoxAdapter(
                  child: _buildHeader(context),
                ),

                // Drop zone o estado de carga
                SliverFillRemaining(
                  hasScrollBody: false,
                  child: Padding(
                    padding: const EdgeInsets.all(AppConstants.padding),
                    child: uploadState.when(
                      idle: () => _buildIdleContent(),
                      uploading: (progress) => _buildUploadingContent(progress),
                      error: (message) => _buildErrorContent(message),
                      success: (jobId) => _buildSuccessContent(jobId),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBackground() {
    return Positioned.fill(
      child: Stack(
        children: [
          // Color base
          Container(color: AppTheme.background),

          // Glows decorativos
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppTheme.neonCyan.withOpacity(0.08),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          Positioned(
            bottom: 100,
            left: -80,
            child: Container(
              width: 250,
              height: 250,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    AppTheme.neonMagenta.withOpacity(0.06),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Logo / título
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppTheme.neonCyan.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: AppTheme.neonCyan.withOpacity(0.3),
                    width: 1,
                  ),
                ),
                child: const Icon(
                  Icons.graphic_eq,
                  color: AppTheme.neonCyan,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'FLAMENCO2TECHNO',
                    style: Theme.of(context).textTheme.labelLarge?.copyWith(
                          fontSize: 16,
                          letterSpacing: 2.5,
                        ),
                  ),
                  Text(
                    'AI MUSIC CONVERTER',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: AppTheme.textDisabled,
                          fontSize: 10,
                          letterSpacing: 2.0,
                        ),
                  ),
                ],
              ),
            ],
          )
              .animate()
              .fadeIn(duration: 600.ms)
              .slideY(begin: -0.2, end: 0, curve: Curves.easeOut),

          const SizedBox(height: 32),

          // Título principal
          Text(
            'CONVIERTE\nTU MÚSICA',
            style: Theme.of(context).textTheme.displayMedium?.copyWith(
                  height: 1.1,
                ),
          )
              .animate()
              .fadeIn(delay: 150.ms, duration: 600.ms)
              .slideY(begin: 0.2, end: 0, curve: Curves.easeOut),

          const SizedBox(height: 8),

          Text(
            'Sube un MP3, WAV o FLAC y la IA\ntransformará tu canción en Techno.',
            style: Theme.of(context).textTheme.bodyMedium,
          )
              .animate()
              .fadeIn(delay: 250.ms, duration: 600.ms),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _buildIdleContent() {
    return Column(
      children: [
        // Zona de drop
        Expanded(
          child: UploadDropZone(
            onFilePicked: _pickFile,
            pulseController: _pulseController,
          ).animate().fadeIn(delay: 350.ms, duration: 600.ms),
        ),

        const SizedBox(height: 24),

        // Formatos soportados
        _buildFormatsRow(),

        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildUploadingContent(double progress) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Icono animado
        Container(
          width: 80,
          height: 80,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: AppTheme.neonCyan.withOpacity(0.1),
            border: Border.all(color: AppTheme.neonCyan.withOpacity(0.4)),
          ),
          child: const Icon(
            Icons.cloud_upload_outlined,
            color: AppTheme.neonCyan,
            size: 36,
          ),
        )
            .animate(onPlay: (c) => c.repeat())
            .shimmer(duration: 1500.ms, color: AppTheme.neonCyan),

        const SizedBox(height: 24),

        Text(
          'SUBIENDO ARCHIVO',
          style: Theme.of(context).textTheme.labelLarge,
        ),

        const SizedBox(height: 8),

        Text(
          '${(progress * 100).toInt()}%',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                color: AppTheme.neonCyan,
              ),
        ),

        const SizedBox(height: 24),

        NeonProgressBar(progress: progress),

        const SizedBox(height: 12),

        Text(
          'Preparando análisis musical...',
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  Widget _buildErrorContent(String message) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(
          Icons.error_outline,
          color: AppTheme.neonMagenta,
          size: 64,
        ),
        const SizedBox(height: 16),
        Text(
          'ERROR',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                color: AppTheme.neonMagenta,
              ),
        ),
        const SizedBox(height: 8),
        Text(
          message,
          style: Theme.of(context).textTheme.bodyMedium,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 32),
        ElevatedButton.icon(
          onPressed: () {
            ref.read(uploadNotifierProvider.notifier).reset();
          },
          icon: const Icon(Icons.refresh),
          label: const Text('INTENTAR DE NUEVO'),
        ),
      ],
    );
  }

  Widget _buildSuccessContent(String jobId) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        const Icon(
          Icons.check_circle_outline,
          color: AppTheme.neonGreen,
          size: 64,
        ),
        const SizedBox(height: 16),
        Text(
          '¡SUBIDO!',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
                color: AppTheme.neonGreen,
              ),
        ),
        const SizedBox(height: 8),
        Text(
          'Redirigiendo al análisis...',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
      ],
    );
  }

  Widget _buildFormatsRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'FORMATOS: ',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textDisabled,
                letterSpacing: 1.0,
              ),
        ),
        for (final fmt in ['MP3', 'WAV', 'FLAC']) ...[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: AppTheme.border,
              borderRadius: BorderRadius.circular(4),
            ),
            child: Text(
              fmt,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppTheme.textSecondary,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.0,
                  ),
            ),
          ),
          if (fmt != 'FLAC') const SizedBox(width: 8),
        ],
        const SizedBox(width: 12),
        Text(
          '· Máx. 100 MB',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppTheme.textDisabled,
              ),
        ),
      ],
    );
  }
}
