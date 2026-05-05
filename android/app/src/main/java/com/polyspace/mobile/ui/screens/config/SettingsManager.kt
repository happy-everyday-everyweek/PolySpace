package com.polyspace.mobile.ui.screens.config

import android.content.Context
import android.content.SharedPreferences

object SettingsManager {

    private const val PREFS_GENERAL = "polyspace_settings_general"
    private const val PREFS_UI = "polyspace_settings_ui"
    private const val PREFS_SYNC = "polyspace_settings_sync"
    private const val PREFS_SECURITY = "polyspace_settings_security"
    private const val PREFS_ADVANCED = "polyspace_settings_advanced"

    enum class SettingType { BOOLEAN, INT, STRING, FLOAT, ENUM }
    enum class SettingCategory { GENERAL, UI, SYNC, SECURITY, ADVANCED }

    data class SettingDefinition(
        val key: String,
        val name: String,
        val description: String,
        val type: SettingType,
        val category: SettingCategory,
        val defaultValue: Any,
        val enumValues: List<String> = emptyList(),
        val intRange: IntRange = 0..100,
        val floatRange: ClosedFloatingPointRange<Float> = 0f..1f,
    )

    val ALL_SETTINGS: List<SettingDefinition> = listOf(

        SettingDefinition("auto_start", "自动启动", "应用启动时自动启动后端服务", SettingType.BOOLEAN, SettingCategory.GENERAL, true),
        SettingDefinition("auto_start_delay_ms", "启动延迟", "自动启动的延迟时间(毫秒)", SettingType.INT, SettingCategory.GENERAL, 1000, intRange = 0..30000),
        SettingDefinition("language", "语言", "应用界面语言", SettingType.ENUM, SettingCategory.GENERAL, "auto", enumValues = listOf("auto", "zh-CN", "en-US")),
        SettingDefinition("theme_mode", "主题模式", "浅色/深色/跟随系统", SettingType.ENUM, SettingCategory.GENERAL, "auto", enumValues = listOf("auto", "light", "dark")),
        SettingDefinition("show_onboarding", "显示引导页", "下次启动时显示引导页", SettingType.BOOLEAN, SettingCategory.GENERAL, false),

        SettingDefinition("font_scale", "字体缩放", "界面字体缩放比例", SettingType.FLOAT, SettingCategory.UI, 1.0f, floatRange = 0.5f..2.0f),
        SettingDefinition("animation_enabled", "动画效果", "启用界面动画效果", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("status_bar_transparent", "透明状态栏", "沉浸式状态栏", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("navigation_bar_transparent", "透明导航栏", "沉浸式导航栏", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("show_feature_labels", "功能标签", "显示功能图标下方的文字标签", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("ring_icon_size", "图标大小", "环形图标大小(dp)", SettingType.INT, SettingCategory.UI, 32, intRange = 16..64),
        SettingDefinition("ring_stroke_width", "图标线宽", "环形图标线宽(dp)", SettingType.INT, SettingCategory.UI, 4, intRange = 1..8),
        SettingDefinition("divider_visible", "分隔线", "显示区域分隔线", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("webview_zoom_enabled", "WebView缩放", "允许WebView页面缩放", SettingType.BOOLEAN, SettingCategory.UI, false),
        SettingDefinition("webview_js_enabled", "JavaScript", "启用WebView JavaScript", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("webview_dom_storage", "DOM存储", "启用WebView DOM存储", SettingType.BOOLEAN, SettingCategory.UI, true),
        SettingDefinition("webview_cache_mode", "缓存模式", "WebView缓存策略", SettingType.ENUM, SettingCategory.UI, "default", enumValues = listOf("default", "no_cache", "cache_only", "cache_first")),

        SettingDefinition("distributed_sync_enabled", "分布式同步", "启用多设备自动同步", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_auto_sync", "自动同步", "定时自动推送和拉取变更", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_auto_sync_interval", "同步间隔", "自动同步间隔(秒)", SettingType.INT, SettingCategory.SYNC, 300, intRange = 30..3600),
        SettingDefinition("distributed_sync_on_startup", "启动时同步", "应用启动时自动拉取远程变更", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_sync_on_handoff", "设备切换同步", "检测到设备切换时自动同步", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_local_first", "本地优先", "敏感数据优先在本地处理", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_encrypt_transit", "传输加密", "同步数据传输时加密", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_conflict_strategy", "冲突策略", "多设备同步冲突解决策略", SettingType.ENUM, SettingCategory.SYNC, "latest", enumValues = listOf("latest", "local", "remote", "merge")),
        SettingDefinition("distributed_sync_settings", "同步设置", "同步设置数据到其他设备", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_sync_persona", "同步人格", "同步人格配置到其他设备", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_sync_workspace", "同步工作区", "同步工作区状态到其他设备", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("distributed_sync_memory", "同步记忆", "同步记忆数据到其他设备", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("calendar_sync_enabled", "日历同步", "启用日历同步", SettingType.BOOLEAN, SettingCategory.SYNC, true),
        SettingDefinition("calendar_sync_interval_min", "日历同步间隔", "日历同步间隔(分钟)", SettingType.INT, SettingCategory.SYNC, 30, intRange = 5..1440),
        SettingDefinition("calendar_sync_direction", "日历同步方向", "日历同步方向", SettingType.ENUM, SettingCategory.SYNC, "both", enumValues = listOf("to_system", "from_system", "both")),
        SettingDefinition("calendar_sync_range_days", "日历同步范围", "日历同步天数范围", SettingType.INT, SettingCategory.SYNC, 90, intRange = 7..365),
        SettingDefinition("message_auto_forward", "消息转发", "自动转发消息到后端", SettingType.BOOLEAN, SettingCategory.SYNC, false),
        SettingDefinition("message_forward_interval_ms", "转发间隔", "消息转发间隔(毫秒)", SettingType.INT, SettingCategory.SYNC, 1000, intRange = 100..10000),
        SettingDefinition("notification_cache_size", "通知缓存", "通知缓存最大条目数", SettingType.INT, SettingCategory.SYNC, 200, intRange = 10..1000),

        SettingDefinition("accessibility_service", "无障碍服务", "启用无障碍服务", SettingType.BOOLEAN, SettingCategory.SECURITY, false),
        SettingDefinition("screen_operation_tool", "屏幕操作", "启用屏幕操作工具", SettingType.BOOLEAN, SettingCategory.SECURITY, false),
        SettingDefinition("screenshot_quality", "截图质量", "屏幕截图JPEG质量(0-100)", SettingType.INT, SettingCategory.SECURITY, 80, intRange = 10..100),
        SettingDefinition("screenshot_max_size", "截图最大尺寸", "截图最大边长(像素)", SettingType.INT, SettingCategory.SECURITY, 1920, intRange = 480..3840),
        SettingDefinition("action_delay_ms", "操作延迟", "屏幕操作之间的延迟(毫秒)", SettingType.INT, SettingCategory.SECURITY, 500, intRange = 100..5000),
        SettingDefinition("confirm_destructive", "确认破坏性操作", "执行破坏性操作前需确认", SettingType.BOOLEAN, SettingCategory.SECURITY, true),
        SettingDefinition("auto_execute_suggestions", "自动执行建议", "自动执行AI建议的操作", SettingType.BOOLEAN, SettingCategory.SECURITY, false),
        SettingDefinition("allow_remote_commands", "远程命令", "允许接收远程命令执行", SettingType.BOOLEAN, SettingCategory.SECURITY, false),

        SettingDefinition("log_level", "日志级别", "应用日志级别", SettingType.ENUM, SettingCategory.ADVANCED, "info", enumValues = listOf("verbose", "debug", "info", "warn", "error")),
        SettingDefinition("log_to_file", "日志写入文件", "将日志写入本地文件", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("log_file_max_size_mb", "日志文件大小", "单个日志文件最大大小(MB)", SettingType.INT, SettingCategory.ADVANCED, 10, intRange = 1..100),
        SettingDefinition("log_retention_days", "日志保留天数", "日志文件保留天数", SettingType.INT, SettingCategory.ADVANCED, 7, intRange = 1..90),
        SettingDefinition("debug_mode", "调试模式", "启用调试模式", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("show_dev_options", "开发者选项", "显示开发者选项", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("backend_verbose_logging", "后端详细日志", "后端服务详细日志输出", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("proot_debug", "proot调试", "启用proot调试输出", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("max_crash_count", "最大崩溃次数", "服务崩溃后停止重启的次数", SettingType.INT, SettingCategory.ADVANCED, 3, intRange = 1..10),
        SettingDefinition("crash_window_s", "崩溃窗口", "崩溃计数重置窗口(秒)", SettingType.INT, SettingCategory.ADVANCED, 60, intRange = 10..300),
        SettingDefinition("service_restart_on_task_removed", "任务移除重启", "从最近任务移除后重启服务", SettingType.BOOLEAN, SettingCategory.ADVANCED, true),
        SettingDefinition("webview_console_log", "WebView控制台", "输出WebView控制台日志", SettingType.BOOLEAN, SettingCategory.ADVANCED, false),
        SettingDefinition("webview_mixed_content", "混合内容", "WebView允许混合内容", SettingType.ENUM, SettingCategory.ADVANCED, "compatibility", enumValues = listOf("never", "compatibility", "always")),
        SettingDefinition("tool_execution_timeout_s", "工具超时", "原生工具执行超时(秒)", SettingType.INT, SettingCategory.ADVANCED, 30, intRange = 5..300),
        SettingDefinition("tts_engine", "TTS引擎", "语音合成引擎", SettingType.STRING, SettingCategory.ADVANCED, ""),
        SettingDefinition("tts_speed", "语速", "语音合成语速", SettingType.FLOAT, SettingCategory.ADVANCED, 1.0f, floatRange = 0.5f..2.0f),
        SettingDefinition("tts_pitch", "音调", "语音合成音调", SettingType.FLOAT, SettingCategory.ADVANCED, 1.0f, floatRange = 0.5f..2.0f),
        SettingDefinition("audio_sample_rate", "录音采样率", "音频录制采样率", SettingType.INT, SettingCategory.ADVANCED, 44100, intRange = 8000..48000),
        SettingDefinition("audio_bit_rate", "录音比特率", "音频录制比特率", SettingType.INT, SettingCategory.ADVANCED, 128000, intRange = 32000..320000),
    )

    private fun getPrefs(context: Context, category: SettingCategory): SharedPreferences {
        val name = when (category) {
            SettingCategory.GENERAL -> PREFS_GENERAL
            SettingCategory.UI -> PREFS_UI
            SettingCategory.SYNC -> PREFS_SYNC
            SettingCategory.SECURITY -> PREFS_SECURITY
            SettingCategory.ADVANCED -> PREFS_ADVANCED
        }
        return context.getSharedPreferences(name, 0)
    }

    fun <T> getSetting(context: Context, key: String, defaultValue: T): T {
        val def = ALL_SETTINGS.find { it.key == key } ?: return defaultValue
        val prefs = getPrefs(context, def.category)
        return when (def.type) {
            SettingType.BOOLEAN -> prefs.getBoolean(key, defaultValue as Boolean) as T
            SettingType.INT -> prefs.getInt(key, defaultValue as Int) as T
            SettingType.STRING -> prefs.getString(key, defaultValue as String) as T
            SettingType.FLOAT -> prefs.getFloat(key, defaultValue as Float) as T
            SettingType.ENUM -> prefs.getString(key, defaultValue as String) as T
        }
    }

    fun <T> setSetting(context: Context, key: String, value: T) {
        val def = ALL_SETTINGS.find { it.key == key } ?: return
        val prefs = getPrefs(context, def.category)
        prefs.edit().apply {
            when (value) {
                is Boolean -> putBoolean(key, value)
                is Int -> putInt(key, value)
                is String -> putString(key, value)
                is Float -> putFloat(key, value)
            }
            apply()
        }
    }

    fun getSettingsByCategory(category: SettingCategory): List<SettingDefinition> {
        return ALL_SETTINGS.filter { it.category == category }
    }

    fun getSettingCount(): Int = ALL_SETTINGS.size

    fun isDistributedSyncEnabled(context: Context): Boolean {
        return getSetting(context, "distributed_sync_enabled", true)
    }

    fun getDistributedSyncScopes(context: Context): List<String> {
        val scopes = mutableListOf<String>()
        if (getSetting(context, "distributed_sync_settings", true)) scopes.add("settings")
        if (getSetting(context, "distributed_sync_persona", true)) scopes.add("persona")
        scopes.add("mode")
        if (getSetting(context, "distributed_sync_workspace", true)) scopes.add("workspace")
        if (getSetting(context, "distributed_sync_memory", true)) scopes.add("memory")
        return scopes
    }
}
