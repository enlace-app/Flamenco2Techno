import 'dart:io';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import '../../../../shared/providers/api_client.dart';
import '../../../../core/errors/app_errors.dart';

part 'upload_provider.g.dart';
part 'upload_provider.freezed.dart';

/// Estado de la pantalla de upload
@freezed
class UploadState with _$UploadState {
  const factory UploadState.idle() = _Idle;
  const factory UploadState.uploading(double progress) = _Uploading;
  const factory UploadState.success(String jobId) = _Success;
  const factory UploadState.error(String message) = _Error;
}

/// Notifier que gestiona el estado de carga de archivos
@riverpod
class UploadNotifier extends _$UploadNotifier {
  @override
  UploadState build() => const UploadState.idle();

  /// Sube un archivo de audio al backend y retorna el jobId.
  /// Devuelve null si hubo error.
  Future<String?> uploadFile(File file) async {
    state = const UploadState.uploading(0.0);

    try {
      final client = ref.read(apiClientProvider);
      final response = await client.uploadFile(
        file,
        onProgress: (progress) {
          state = UploadState.uploading(progress);
        },
      );

      state = UploadState.success(response.jobId);
      return response.jobId;
    } on AppFailure catch (e) {
      state = UploadState.error(e.message);
      return null;
    } catch (e) {
      state = UploadState.error('Error inesperado: $e');
      return null;
    }
  }

  /// Resetea el estado al idle inicial
  void reset() {
    state = const UploadState.idle();
  }
}
