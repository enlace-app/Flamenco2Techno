import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';
import 'package:just_audio/just_audio.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/providers/api_client.dart';
import '../providers/result_provider.dart';
import '../../upload/presentation/widgets/neon_progress_bar.dart';

/// Pantalla final: preview del audio convertido, descarga y compartir.
class ResultScreen extends ConsumerStatefulWidget {
  const ResultScreen({super.key, required this.jobId});

  final String jobId;

  @override
  ConsumerState<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends ConsumerState<ResultScreen> {
  late AudioPlayer _player;
  bool _isPlaying = false;
  Duration _position = Duration.zero;
  Duration _duration = Duration.zero;
  String? _localFilePath;

  @override
  void initState() {
    super.initState();
    _player = AudioPlayer();
    _setupPlayer();
    _downloadAndPrepare();
  }

  void _setupPlayer() {
    _player.positionStream.listen((pos) {
      if (mounted) setState(() => _position = pos);
    });
    _player.durationStream.listen((dur) {
      if (mounted) setState(() => _duration = dur ?? Duration.zero);
    });
    _player.playerStateStream.listen((state) {
      if (mounted) {
        setState(() {
          _isPlaying = state.playing;
        });
      }
    });
  }

  Future<void> _downloadAndPrepare() async {
    try {
      final dir = await getTemporaryDirectory();
      final path = '${dir.path}/preview_${widget.jobId}.mp3';

      final client = ref.read(apiClientProvider);
      await client.downloadResult(
        jobId: widget.jobId,
        savePath: path,
        onProgress: (p) {
          ref.read(resultDownloadProgressProvider.notifier).state = p;
        },
      );

      setState(() => _localFilePath = path);

      await _player.setFilePath(path);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error descargando: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }

  // ── Player controls ────────────────────────────────────────────────

  Future<void> _togglePlay() async {
    if (_isPlaying) {
      await _player.pause();
    } else {
      await _player.play();
    }
  }

  Future<void> _seekTo(double value) async {
    final ms = (value * _duration.inMilliseconds).round();
    await _player.seek(Duration(milliseconds: ms));
  }

  // ── Export ─────────────────────────────────────────────────────────

  Future<void> _saveToDevice() async {
    if (_localFilePath == null) return;

    try {
      final dir = await getExternalStorageDirectory();
      if (dir == null) {
        _showError('No se pudo acceder al almacenamiento');
        return;
      }

      final musicDir = Directory('${dir.path}/Flamenco2Techno');
      if (!musicDir.existsSync()) musicDir.createSync(recursive: true);

      final destPath = '${musicDir.path}/techno_${widget.jobId.substring(0, 8)}.mp3';
      await File(_localFilePath!).copy(destPath);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const Icon(Icons.check_circle, color: AppTheme.neonGreen),
                const SizedBox(width: 12),
                Expanded(child: Text('Guardado en: $destPath')),
              ],
            ),
          ),
        );
      }
    } catch (e) {
      _showError('Error al guardar: $e');
    }
  }

  Future<void> _shareFile() async {
    if (_localFilePath == null) return;
    await Share.shareXFiles(
      [XFile(_localFilePath!)],
      text: '¡Mira esta canción convertida a Techno por Flamenco2Techno AI!',
    );
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  // ── Build ──────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final downloadProgress = ref.watch(resultDownloadProgressProvider);
    final isDownloading = _localFilePath == null;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded),
          onPressed: () => context.go(AppRoutes.upload),
        ),
        title: const Text('RESULTADO'),
        actions: [
          if (!isDownloading)
            IconButton(
              icon: const Icon(Icons.share_outlined),
              onPressed: _shareFile,
              tooltip: 'Compartir',
            ),
        ],
      ),
      body: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(AppConstants.padding),
              child: Column(
                children: [
                  // Success banner
                  _buildSuccessBanner(),

                  const SizedBox(height: 24),

                  // Player
                  isDownloading
                      ? _buildDownloadingPlayer(downloadProgress)
                      : _buildPlayer(),

                  const SizedBox(height: 32),

                  // Botones de exportación
                  if (!isDownloading) ...[
                    _buildExportButtons(),
                    const SizedBox(height: 24),
                  ],

                  // Nueva conversión
                  OutlinedButton.icon(
                    onPressed: () => context.go(AppRoutes.upload),
                    icon: const Icon(Icons.add),
                    label: const Text('NUEVA CONVERSIÓN'),
                  ).animate().fadeIn(delay: 800.ms),

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessBanner() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppTheme.neonGreen.withOpacity(0.1),
            AppTheme.neonCyan.withOpacity(0.05),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.neonGreen.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.check_circle_outline, color: AppTheme.neonGreen, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '¡CONVERSIÓN COMPLETADA!',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                        color: AppTheme.neonGreen,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Tu canción ha sido transformada al estilo Techno',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    ).animate().fadeIn().scale(begin: const Offset(0.95, 0.95));
  }

  Widget _buildDownloadingPlayer(double progress) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.border),
      ),
      child: Column(
        children: [
          const Icon(
            Icons.cloud_download_outlined,
            color: AppTheme.neonCyan,
            size: 48,
          ).animate(onPlay: (c) => c.repeat(reverse: true)).scale(
                begin: const Offset(1.0, 1.0),
                end: const Offset(1.1, 1.1),
              ),
          const SizedBox(height: 16),
          Text(
            'DESCARGANDO AUDIO',
            style: Theme.of(context).textTheme.labelLarge,
          ),
          const SizedBox(height: 8),
          Text('${(progress * 100).toInt()}%',
              style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: 16),
          NeonProgressBar(progress: progress),
        ],
      ),
    );
  }

  Widget _buildPlayer() {
    final progressValue = _duration.inMilliseconds > 0
        ? _position.inMilliseconds / _duration.inMilliseconds
        : 0.0;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.neonCyan.withOpacity(0.3)),
        boxShadow: [
          BoxShadow(
            color: AppTheme.neonCyan.withOpacity(0.08),
            blurRadius: 24,
          ),
        ],
      ),
      child: Column(
        children: [
          // Botón play/pause
          GestureDetector(
            onTap: _togglePlay,
            child: Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: AppTheme.cyanGradient,
                boxShadow: [
                  BoxShadow(
                    color: AppTheme.neonCyan.withOpacity(0.4),
                    blurRadius: 20,
                  ),
                ],
              ),
              child: Icon(
                _isPlaying ? Icons.pause_rounded : Icons.play_arrow_rounded,
                color: AppTheme.background,
                size: 36,
              ),
            ),
          )
              .animate(key: ValueKey(_isPlaying))
              .scale(begin: const Offset(0.9, 0.9), duration: 200.ms),

          const SizedBox(height: 20),

          // Barra de tiempo
          GestureDetector(
            onHorizontalDragUpdate: (details) {
              final renderBox = context.findRenderObject() as RenderBox?;
              if (renderBox != null) {
                final localPos = renderBox.globalToLocal(details.globalPosition);
                final ratio = (localPos.dx / renderBox.size.width).clamp(0.0, 1.0);
                _seekTo(ratio);
              }
            },
            child: NeonProgressBar(progress: progressValue.clamp(0.0, 1.0)),
          ),

          const SizedBox(height: 8),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _formatDuration(_position),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'Orbitron',
                      fontSize: 11,
                    ),
              ),
              Text(
                _formatDuration(_duration),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'Orbitron',
                      fontSize: 11,
                    ),
              ),
            ],
          ),
        ],
      ),
    ).animate().fadeIn(delay: 200.ms);
  }

  Widget _buildExportButtons() {
    return Column(
      children: [
        // Guardar
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: _saveToDevice,
            icon: const Icon(Icons.save_alt),
            label: const Text('GUARDAR EN DISPOSITIVO'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ).animate().fadeIn(delay: 400.ms).slideY(begin: 0.2),

        const SizedBox(height: 12),

        // Compartir
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: _shareFile,
            icon: const Icon(Icons.share),
            label: const Text('COMPARTIR'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
          ),
        ).animate().fadeIn(delay: 500.ms).slideY(begin: 0.2),
      ],
    );
  }

  String _formatDuration(Duration d) {
    final mins = d.inMinutes.remainder(60).toString().padLeft(2, '0');
    final secs = d.inSeconds.remainder(60).toString().padLeft(2, '0');
    return '$mins:$secs';
  }
}
