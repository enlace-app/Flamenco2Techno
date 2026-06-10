import 'dart:io';
import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:logger/logger.dart';

import '../constants/app_constants.dart';
import '../errors/app_errors.dart';

part 'api_client.g.dart';

final _logger = Logger(
  printer: PrettyPrinter(methodCount: 0, colors: false),
);

/// Provider del cliente HTTP principal
@riverpod
ApiClient apiClient(ApiClientRef ref) {
  return ApiClient();
}

/// Cliente HTTP configurado con Dio para comunicarse con el backend FastAPI.
class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: AppConstants.apiTimeout,
        receiveTimeout: AppConstants.apiTimeout,
        sendTimeout: const Duration(minutes: 5), // Upload puede tardar
        headers: {
          'Accept': 'application/json',
        },
      ),
    );

    // Interceptor de logging
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          _logger.d('→ ${options.method} ${options.path}');
          handler.next(options);
        },
        onResponse: (response, handler) {
          _logger.d('← ${response.statusCode} ${response.realUri.path}');
          handler.next(response);
        },
        onError: (error, handler) {
          _logger.e('✗ ${error.response?.statusCode} ${error.message}');
          handler.next(error);
        },
      ),
    );
  }

  // ── Upload ─────────────────────────────────────────────────────────

  /// Sube un archivo de audio al servidor.
  /// [file] - Archivo a subir
  /// [onProgress] - Callback con progreso 0.0 a 1.0
  Future<UploadResponse> uploadFile(
    File file, {
    void Function(double progress)? onProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
      });

      final response = await _dio.post(
        '/api/v1/upload',
        data: formData,
        onSendProgress: (sent, total) {
          if (total > 0 && onProgress != null) {
            onProgress(sent / total);
          }
        },
      );

      return UploadResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }

  // ── Analyze ────────────────────────────────────────────────────────

  /// Solicita análisis musical del archivo subido.
  Future<AnalysisResult> analyzeFile(String jobId) async {
    try {
      final response = await _dio.post(
        '/api/v1/analyze',
        data: {'job_id': jobId},
      );
      return AnalysisResult.fromJson(response.data);
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }

  // ── Convert ────────────────────────────────────────────────────────

  /// Inicia la conversión a Techno.
  Future<ConversionJobResponse> startConversion({
    required String jobId,
    required String mode,
    required bool keepVocals,
    required int targetBpm,
    required String exportFormat,
  }) async {
    try {
      final response = await _dio.post(
        '/api/v1/convert',
        data: {
          'job_id': jobId,
          'mode': mode,
          'keep_vocals': keepVocals,
          'target_bpm': targetBpm,
          'export_format': exportFormat,
        },
      );
      return ConversionJobResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }

  // ── Status ─────────────────────────────────────────────────────────

  /// Consulta el estado de un job de procesamiento.
  Future<JobStatusResponse> getJobStatus(String jobId) async {
    try {
      final response = await _dio.get('/api/v1/status/$jobId');
      return JobStatusResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }

  // ── Download ───────────────────────────────────────────────────────

  /// Descarga el archivo de audio convertido.
  Future<void> downloadResult({
    required String jobId,
    required String savePath,
    void Function(double progress)? onProgress,
  }) async {
    try {
      await _dio.download(
        '/api/v1/download/$jobId',
        savePath,
        onReceiveProgress: (received, total) {
          if (total > 0 && onProgress != null) {
            onProgress(received / total);
          }
        },
      );
    } on DioException catch (e) {
      throw mapDioError(e);
    }
  }
}

// ── Response models ─────────────────────────────────────────────────

class UploadResponse {
  final String jobId;
  final String filename;
  final int fileSizeBytes;
  final String message;

  const UploadResponse({
    required this.jobId,
    required this.filename,
    required this.fileSizeBytes,
    required this.message,
  });

  factory UploadResponse.fromJson(Map<String, dynamic> json) => UploadResponse(
        jobId: json['job_id'],
        filename: json['filename'],
        fileSizeBytes: json['file_size_bytes'],
        message: json['message'],
      );
}

class AnalysisResult {
  final String jobId;
  final double bpm;
  final String key;
  final String scale;
  final double durationSeconds;
  final bool vocalsDetected;
  final bool drumsDetected;
  final bool bassDetected;
  final List<String> structureSections;

  const AnalysisResult({
    required this.jobId,
    required this.bpm,
    required this.key,
    required this.scale,
    required this.durationSeconds,
    required this.vocalsDetected,
    required this.drumsDetected,
    required this.bassDetected,
    required this.structureSections,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) => AnalysisResult(
        jobId: json['job_id'],
        bpm: (json['bpm'] as num).toDouble(),
        key: json['key'],
        scale: json['scale'],
        durationSeconds: (json['duration_seconds'] as num).toDouble(),
        vocalsDetected: json['vocals_detected'],
        drumsDetected: json['drums_detected'],
        bassDetected: json['bass_detected'],
        structureSections: List<String>.from(json['structure_sections'] ?? []),
      );
}

class ConversionJobResponse {
  final String jobId;
  final String conversionId;
  final String status;
  final String message;

  const ConversionJobResponse({
    required this.jobId,
    required this.conversionId,
    required this.status,
    required this.message,
  });

  factory ConversionJobResponse.fromJson(Map<String, dynamic> json) =>
      ConversionJobResponse(
        jobId: json['job_id'],
        conversionId: json['conversion_id'],
        status: json['status'],
        message: json['message'],
      );
}

class JobStatusResponse {
  final String jobId;
  final String status;
  final double progress;
  final String currentStep;
  final String? errorMessage;
  final String? downloadUrl;

  const JobStatusResponse({
    required this.jobId,
    required this.status,
    required this.progress,
    required this.currentStep,
    this.errorMessage,
    this.downloadUrl,
  });

  factory JobStatusResponse.fromJson(Map<String, dynamic> json) =>
      JobStatusResponse(
        jobId: json['job_id'],
        status: json['status'],
        progress: (json['progress'] as num).toDouble(),
        currentStep: json['current_step'] ?? '',
        errorMessage: json['error_message'],
        downloadUrl: json['download_url'],
      );
}
