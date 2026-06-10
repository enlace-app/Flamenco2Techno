import 'dart:async';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../../../core/constants/app_constants.dart';
import '../../../../core/errors/app_errors.dart';
import '../../../../shared/providers/api_client.dart';

part 'conversion_provider.g.dart';
part 'conversion_provider.freezed.dart';

/// Progreso detallado de una conversión en curso
@freezed
class ConversionProgress with _$ConversionProgress {
  const factory ConversionProgress({
    required double overall,
    required JobStatus status,
    required String currentStep,
  }) = _ConversionProgress;
}

/// Estado de la pantalla de conversión
@freezed
class ConversionState with _$ConversionState {
  const factory ConversionState.idle() = _Idle;
  const factory ConversionState.converting(ConversionProgress progress) = _Converting;
  const factory ConversionState.success(String conversionId) = _Success;
  const factory ConversionState.error(String message) = _Error;
}

/// Notifier que gestiona la conversión y el polling de estado
@riverpod
class ConversionNotifier extends _$ConversionNotifier {
  Timer? _pollTimer;
  int _pollCount = 0;
  static const int _maxPolls = 300; // 10 minutos a 2s de intervalo

  @override
  ConversionState build() => const ConversionState.idle();

  /// Inicia la conversión a Techno
  Future<void> startConversion({
    required String jobId,
    required TechnoMode mode,
    required bool keepVocals,
    required int targetBpm,
    required String exportFormat,
  }) async {
    state = const ConversionState.converting(
      ConversionProgress(
        overall: 0.0,
        status: JobStatus.pending,
        currentStep: 'Iniciando conversión...',
      ),
    );

    try {
      final client = ref.read(apiClientProvider);

      // Iniciar job de conversión
      final response = await client.startConversion(
        jobId: jobId,
        mode: mode.apiValue,
        keepVocals: keepVocals,
        targetBpm: targetBpm,
        exportFormat: exportFormat,
      );

      // Iniciar polling de estado
      _startPolling(response.conversionId, client);
    } on AppFailure catch (e) {
      state = ConversionState.error(e.message);
    } catch (e) {
      state = ConversionState.error('Error inesperado: $e');
    }
  }

  void _startPolling(String conversionId, ApiClient client) {
    _pollCount = 0;
    _pollTimer = Timer.periodic(AppConstants.pollInterval, (_) async {
      _pollCount++;

      if (_pollCount > _maxPolls) {
        _stopPolling();
        state = const ConversionState.error(
          'Tiempo de espera agotado. El proceso tardó demasiado.',
        );
        return;
      }

      try {
        final status = await client.getJobStatus(conversionId);
        final jobStatus = status.status.toJobStatus();

        // Actualizar progreso
        state = ConversionState.converting(
          ConversionProgress(
            overall: status.progress,
            status: jobStatus,
            currentStep: status.currentStep,
          ),
        );

        // Verificar si terminó
        if (jobStatus == JobStatus.completed) {
          _stopPolling();
          state = ConversionState.success(conversionId);
        } else if (jobStatus == JobStatus.failed) {
          _stopPolling();
          state = ConversionState.error(
            status.errorMessage ?? 'Error en el procesamiento',
          );
        }
      } catch (e) {
        // No parar el polling por errores de red temporales
        // Se para sólo si hay demasiados errores consecutivos
      }
    });
  }

  void _stopPolling() {
    _pollTimer?.cancel();
    _pollTimer = null;
  }

  void reset() {
    _stopPolling();
    state = const ConversionState.idle();
  }

  @override
  void dispose() {
    _stopPolling();
    super.dispose();
  }
}
