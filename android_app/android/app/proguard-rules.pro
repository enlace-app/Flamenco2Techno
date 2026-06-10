# ── Flutter ───────────────────────────────────────────────────────────────
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-dontwarn io.flutter.embedding.**

# ── Kotlin ────────────────────────────────────────────────────────────────
-keep class kotlin.** { *; }
-keep class kotlinx.** { *; }
-dontwarn kotlin.**

# ── OkHttp / Dio (HTTP) ───────────────────────────────────────────────────
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# ── Just Audio ────────────────────────────────────────────────────────────
-keep class com.ryanheise.just_audio.** { *; }

# ── File Picker ───────────────────────────────────────────────────────────
-keep class com.mr.flutter.plugin.filepicker.** { *; }

# ── Share Plus ────────────────────────────────────────────────────────────
-keep class dev.fluttercommunity.plus.share.** { *; }

# ── Permission Handler ────────────────────────────────────────────────────
-keep class com.baseflow.permissionhandler.** { *; }

# ── General: mantener clases con anotaciones ──────────────────────────────
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes Exceptions

# ── Evitar warnings innecesarios ──────────────────────────────────────────
-dontwarn com.google.android.gms.**
-dontwarn javax.annotation.**
