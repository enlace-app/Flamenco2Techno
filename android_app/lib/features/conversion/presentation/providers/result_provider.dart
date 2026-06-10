import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'result_provider.g.dart';

/// Progreso de descarga del archivo resultado (0.0 - 1.0)
@riverpod
class ResultDownloadProgress extends _$ResultDownloadProgress {
  @override
  double build() => 0.0;
}
