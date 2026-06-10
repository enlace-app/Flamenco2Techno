package com.flamenco2techno.app

import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * MainActivity - Punto de entrada Android para la app Flutter.
 * Expone un MethodChannel para comunicación nativa si se necesita
 * acceso a APIs Android no disponibles en Flutter.
 */
class MainActivity : FlutterActivity() {

    companion object {
        private const val CHANNEL = "com.flamenco2techno/native"
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        // Canal para funcionalidades nativas opcionales
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        ).setMethodCallHandler { call, result ->
            when (call.method) {
                "getDeviceInfo" -> {
                    result.success(mapOf(
                        "model" to android.os.Build.MODEL,
                        "sdk" to android.os.Build.VERSION.SDK_INT,
                        "manufacturer" to android.os.Build.MANUFACTURER
                    ))
                }
                "getAvailableStorage" -> {
                    val stat = android.os.StatFs(
                        android.os.Environment.getExternalStorageDirectory().path
                    )
                    val bytesAvailable = stat.blockSizeLong * stat.availableBlocksLong
                    result.success(bytesAvailable)
                }
                else -> result.notImplemented()
            }
        }
    }
}
