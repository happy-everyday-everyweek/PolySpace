-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable

-keep class com.polyspace.mobile.service.BackendService { *; }
-keep class com.polyspace.mobile.service.BackendStatus { *; }
-keep class com.polyspace.mobile.tool.ToolResult { *; }
-keep class com.polyspace.mobile.tool.NativeTool { *; }
-keep class * implements com.polyspace.mobile.tool.NativeTool { *; }

-keepclassmembers class * {
    *** getContext();
    *** getApplicationContext();
}

-keepclassmembers class kotlinx.coroutines.** {
    volatile <fields>;
}

-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int d(...);
}

-keepclassmembers class org.json.** { *; }
