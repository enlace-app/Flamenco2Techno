/// Constantes globales de la aplicación Flamenco2Techno AI
class AppConstants {
  // ── API ───────────────────────────────────────────────────────────
  /// URL base del backend FastAPI.
  /// En producción, reemplazar con la URL del servidor real.
  static const String apiBaseUrl = 'http://10.0.2.2:8000'; // Emulador Android
  // static const String apiBaseUrl = 'https://api.flamenco2techno.com'; // Producción

  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration pollInterval = Duration(seconds: 2);

  // ── Archivo de audio ──────────────────────────────────────────────
  static const int maxFileSizeMb = 100;
  static const int maxFileSizeBytes = maxFileSizeMb * 1024 * 1024;
  static const List<String> allowedExtensions = ['mp3', 'wav', 'flac'];
  static const List<String> allowedMimeTypes = [
    'audio/mpeg',
    'audio/wav',
    'audio/x-wav',
    'audio/flac',
    'audio/x-flac',
  ];

  // ── Conversión ────────────────────────────────────────────────────
  static const int bpmMin = 125;
  static const int bpmMax = 140;
  static const int maxJobDurationSeconds = 600; // 10 minutos

  // ── UI ────────────────────────────────────────────────────────────
  static const double borderRadius = 16.0;
  static const double borderRadiusSmall = 8.0;
  static const double padding = 20.0;
  static const double paddingSmall = 12.0;

  // ── Almacenamiento local ──────────────────────────────────────────
  static const String settingsBox = 'settings';
  static const String jobsBox = 'jobs_history';
  static const String keyServerUrl = 'server_url';
  static const String keyDefaultMode = 'default_mode';
  static const String keyKeepVocals = 'keep_vocals';
}

/// Rutas de navegación de GoRouter
class AppRoutes {
  static const String upload = '/';
  static const String analysis = '/analysis/:jobId';
  static const String conversion = '/conversion/:jobId';
  static const String result = '/result/:jobId';

  /// Genera la ruta de análisis con el jobId dado
  static String analysisRoute(String jobId) => '/analysis/$jobId';

  /// Genera la ruta de conversión con el jobId dado
  static String conversionRoute(String jobId) => '/conversion/$jobId';

  /// Genera la ruta de resultado con el jobId dado
  static String resultRoute(String jobId) => '/result/$jobId';
}

/// Modos de conversión disponibles
enum TechnoMode {
  soft('soft', 'Soft Techno', '125-128 BPM · Ambient · Progresivo'),
  peak('peak', 'Peak Time', '130-135 BPM · Power · Dancefloor'),
  hard('hard', 'Hard Techno', '138-145 BPM · Industrial · Rave');

  const TechnoMode(this.apiValue, this.displayName, this.description);

  final String apiValue;
  final String displayName;
  final String description;
}

/// Estados posibles de un job de procesamiento
enum JobStatus {
  pending,
  uploading,
  analyzing,
  separating,
  generating,
  mixing,
  exporting,
  completed,
  failed,
}

/// Extensión para convertir string del API a JobStatus
extension JobStatusX on String {
  JobStatus toJobStatus() {
    return JobStatus.values.firstWhere(
      (e) => e.name == this,
      orElse: () => JobStatus.pending,
    );
  }
}
