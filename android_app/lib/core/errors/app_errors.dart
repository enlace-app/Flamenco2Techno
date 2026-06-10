import 'package:dio/dio.dart';

/// Clase base para errores de la aplicación
abstract class AppFailure implements Exception {
  const AppFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

/// Error de red o API
class NetworkFailure extends AppFailure {
  const NetworkFailure(super.message);
}

/// Error de validación de archivo
class FileValidationFailure extends AppFailure {
  const FileValidationFailure(super.message);
}

/// Error del servidor (5xx)
class ServerFailure extends AppFailure {
  const ServerFailure(super.message);
}

/// Job no encontrado o expirado
class JobNotFoundFailure extends AppFailure {
  const JobNotFoundFailure(super.message);
}

/// Error de procesamiento de audio
class AudioProcessingFailure extends AppFailure {
  const AudioProcessingFailure(super.message);
}

/// Timeout del job
class JobTimeoutFailure extends AppFailure {
  const JobTimeoutFailure(super.message);
}

/// Convierte errores Dio a AppFailure legibles
AppFailure mapDioError(DioException e) {
  switch (e.type) {
    case DioExceptionType.connectionTimeout:
    case DioExceptionType.sendTimeout:
    case DioExceptionType.receiveTimeout:
      return const NetworkFailure(
        'Tiempo de espera agotado. Comprueba tu conexión.',
      );
    case DioExceptionType.connectionError:
      return const NetworkFailure(
        'No se puede conectar al servidor. ¿Está activo el backend?',
      );
    case DioExceptionType.badResponse:
      final statusCode = e.response?.statusCode ?? 0;
      final detail = e.response?.data?['detail'] ?? 'Error desconocido';
      if (statusCode == 404) {
        return JobNotFoundFailure('Recurso no encontrado: $detail');
      } else if (statusCode == 413) {
        return const FileValidationFailure(
          'Archivo demasiado grande. Máximo 100 MB.',
        );
      } else if (statusCode == 422) {
        return FileValidationFailure('Formato inválido: $detail');
      } else if (statusCode >= 500) {
        return ServerFailure('Error del servidor ($statusCode): $detail');
      }
      return NetworkFailure('Error HTTP $statusCode: $detail');
    default:
      return NetworkFailure('Error de red: ${e.message}');
  }
}
