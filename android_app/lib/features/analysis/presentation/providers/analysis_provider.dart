import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../../../../shared/providers/api_client.dart';

part 'analysis_provider.g.dart';

/// Provider que dispara el análisis de un job y devuelve el resultado.
/// Se cachea automáticamente por jobId.
@riverpod
Future<AnalysisResult> analysis(AnalysisRef ref, String jobId) async {
  final client = ref.watch(apiClientProvider);
  return client.analyzeFile(jobId);
}
