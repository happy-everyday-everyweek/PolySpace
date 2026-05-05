package com.polyspace.mobile.tool

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.AlarmClock
import android.provider.Settings
import org.json.JSONObject

class AlarmTool : NativeTool {
    override val name = "alarm"
    override val displayName = "闹钟"
    override val description = "设置闹钟和定时器"
    override val category = "system"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "set_alarm")
        return when (action) {
            "set_alarm" -> {
                val hour = params.optInt("hour", 8)
                val minute = params.optInt("minute", 0)
                val message = params.optString("message", "PolySpace闹钟")
                try {
                    val intent = Intent(AlarmClock.ACTION_SET_ALARM).apply {
                        putExtra(AlarmClock.EXTRA_HOUR, hour)
                        putExtra(AlarmClock.EXTRA_MINUTES, minute)
                        putExtra(AlarmClock.EXTRA_MESSAGE, message)
                    }
                    context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    ToolResult(true, JSONObject().apply {
                        put("hour", hour)
                        put("minute", minute)
                        put("message", message)
                    })
                } catch (e: Exception) {
                    ToolResult(false, error = e.message ?: "Failed to set alarm")
                }
            }
            "set_timer" -> {
                val seconds = params.optInt("seconds", 60)
                val message = params.optString("message", "PolySpace定时器")
                try {
                    val intent = Intent(AlarmClock.ACTION_SET_TIMER).apply {
                        putExtra(AlarmClock.EXTRA_LENGTH, seconds)
                        putExtra(AlarmClock.EXTRA_MESSAGE, message)
                    }
                    context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                    ToolResult(true, JSONObject().apply {
                        put("seconds", seconds)
                        put("message", message)
                    })
                } catch (e: Exception) {
                    ToolResult(false, error = e.message ?: "Failed to set timer")
                }
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class AppLauncherTool : NativeTool {
    override val name = "app_launcher"
    override val displayName = "应用启动"
    override val description = "启动指定应用"
    override val category = "system"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val packageName = params.optString("package_name", "")
        if (packageName.isEmpty()) return ToolResult(false, error = "Missing package_name")
        try {
            val intent = context.packageManager.getLaunchIntentForPackage(packageName)
                ?: return ToolResult(false, error = "App not found: $packageName")
            context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return ToolResult(true, JSONObject().apply { put("launched", packageName) })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Failed to launch app")
        }
    }
}

class ClipboardTool : NativeTool {
    override val name = "clipboard"
    override val displayName = "剪贴板"
    override val description = "读取和写入剪贴板"
    override val category = "system"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "read")
        val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as android.content.ClipboardManager
        return when (action) {
            "read" -> {
                val clip = clipboard.primaryClip
                val text = if (clip != null && clip.itemCount > 0) {
                    clip.getItemAt(0)?.text?.toString() ?: ""
                } else ""
                ToolResult(true, JSONObject().apply { put("text", text) })
            }
            "write" -> {
                val text = params.optString("text", "")
                val clip = android.content.ClipData.newPlainText("PolySpace", text)
                clipboard.setPrimaryClip(clip)
                ToolResult(true, JSONObject().apply { put("written", text.length) })
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class ContactTool : NativeTool {
    override val name = "contact"
    override val displayName = "联系人"
    override val description = "查询手机联系人"
    override val category = "communication"
    override val requiredPermissions = listOf("android.permission.READ_CONTACTS")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "search")
        val query = params.optString("query", "")
        try {
            val results = mutableListOf<JSONObject>()
            val uri = android.provider.ContactsContract.CommonDataKinds.Phone.CONTENT_URI
            val projection = arrayOf(
                android.provider.ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                android.provider.ContactsContract.CommonDataKinds.Phone.NUMBER,
                android.provider.ContactsContract.CommonDataKinds.Phone.TYPE
            )
            val selection = if (query.isNotEmpty()) {
                "${android.provider.ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME} LIKE ?"
            } else null
            val selectionArgs = if (query.isNotEmpty()) arrayOf("%$query%") else null

            context.contentResolver.query(uri, projection, selection, selectionArgs, null)?.use { cursor ->
                while (cursor.moveToNext() && results.size < 20) {
                    results.add(JSONObject().apply {
                        put("name", cursor.getString(0) ?: "")
                        put("phone", cursor.getString(1) ?: "")
                        put("type", cursor.getInt(2))
                    })
                }
            }
            return ToolResult(true, JSONObject().apply {
                put("contacts", org.json.JSONArray(results))
                put("count", results.size)
            })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Failed to query contacts")
        }
    }
}

class PhoneCallTool : NativeTool {
    override val name = "phone_call"
    override val displayName = "电话"
    override val description = "拨打电话"
    override val category = "communication"
    override val requiredPermissions = listOf("android.permission.CALL_PHONE")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val number = params.optString("number", "")
        if (number.isEmpty()) return ToolResult(false, error = "Missing number")
        try {
            val intent = Intent(Intent.ACTION_CALL, Uri.parse("tel:$number"))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            return ToolResult(true, JSONObject().apply { put("calling", number) })
        } catch (e: Exception) {
            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$number"))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            return ToolResult(true, JSONObject().apply { put("dialing", number) })
        }
    }
}

class SmsTool : NativeTool {
    override val name = "sms"
    override val displayName = "短信"
    override val description = "发送短信"
    override val category = "communication"
    override val requiredPermissions = listOf("android.permission.SEND_SMS")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val number = params.optString("number", "")
        val message = params.optString("message", "")
        if (number.isEmpty() || message.isEmpty()) return ToolResult(false, error = "Missing number or message")
        try {
            android.telephony.SmsManager.getDefault().sendTextMessage(number, null, message, null, null)
            return ToolResult(true, JSONObject().apply {
                put("sent_to", number)
                put("message_length", message.length)
            })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Failed to send SMS")
        }
    }
}

class WifiTool : NativeTool {
    override val name = "wifi"
    override val displayName = "WiFi"
    override val description = "查询WiFi网络信息"
    override val category = "network"
    override val requiredPermissions = listOf("android.permission.ACCESS_WIFI_STATE")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "info")
        val wifiManager = context.applicationContext.getSystemService(Context.WIFI_SERVICE) as android.net.wifi.WifiManager
        return when (action) {
            "info" -> {
                val info = wifiManager.connectionInfo
                ToolResult(true, JSONObject().apply {
                    put("enabled", wifiManager.isWifiEnabled)
                    put("ssid", info?.ssid?.removeSurrounding("\"") ?: "")
                    put("ip", info?.let { android.text.format.Formatter.formatIpAddress(it.ipAddress) } ?: "")
                    put("signal_strength", info?.rssi ?: 0)
                    put("link_speed", info?.linkSpeed ?: 0)
                })
            }
            "enable" -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    val panelIntent = Intent(android.provider.Settings.Panel.ACTION_WIFI)
                    panelIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(panelIntent)
                    ToolResult(true, JSONObject().apply { put("opened_settings", true) })
                } else {
                    @Suppress("DEPRECATION")
                    wifiManager.isWifiEnabled = true
                    ToolResult(true, JSONObject().apply { put("enabled", true) })
                }
            }
            "disable" -> {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    val panelIntent = Intent(android.provider.Settings.Panel.ACTION_WIFI)
                    panelIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(panelIntent)
                    ToolResult(true, JSONObject().apply { put("opened_settings", true) })
                } else {
                    @Suppress("DEPRECATION")
                    wifiManager.isWifiEnabled = false
                    ToolResult(true, JSONObject().apply { put("enabled", false) })
                }
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class BatteryTool : NativeTool {
    override val name = "battery"
    override val displayName = "电池"
    override val description = "查询电池状态"
    override val category = "system"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val intent = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            ?: return ToolResult(false, error = "Cannot read battery info")
        val level = intent.getIntExtra(android.os.BatteryManager.EXTRA_LEVEL, -1)
        val scale = intent.getIntExtra(android.os.BatteryManager.EXTRA_SCALE, -1)
        val status = intent.getIntExtra(android.os.BatteryManager.EXTRA_STATUS, -1)
        val plugged = intent.getIntExtra(android.os.BatteryManager.EXTRA_PLUGGED, -1)
        val temperature = intent.getIntExtra(android.os.BatteryManager.EXTRA_TEMPERATURE, -1) / 10f
        val voltage = intent.getIntExtra(android.os.BatteryManager.EXTRA_VOLTAGE, -1) / 1000f
        val isCharging = status == android.os.BatteryManager.BATTERY_STATUS_CHARGING ||
                status == android.os.BatteryManager.BATTERY_STATUS_FULL
        return ToolResult(true, JSONObject().apply {
            put("level", (level * 100 / scale.toFloat()).toInt())
            put("charging", isCharging)
            put("plugged", plugged != 0)
            put("temperature", temperature)
            put("voltage", voltage)
        })
    }

    private class IntentFilter(action: String) : android.content.IntentFilter(action)
}

class LocationTool : NativeTool {
    override val name = "location"
    override val displayName = "位置"
    override val description = "获取当前位置信息"
    override val category = "system"
    override val requiredPermissions = listOf(
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION"
    )

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as android.location.LocationManager
        val providers = locationManager.getProviders(true)
        var bestLocation: android.location.Location? = null
        for (provider in providers) {
            val location = locationManager.getLastKnownLocation(provider) ?: continue
            if (bestLocation == null || location.accuracy < bestLocation.accuracy) {
                bestLocation = location
            }
        }
        return if (bestLocation != null) {
            ToolResult(true, JSONObject().apply {
                put("latitude", bestLocation.latitude)
                put("longitude", bestLocation.longitude)
                put("accuracy", bestLocation.accuracy)
                put("altitude", bestLocation.altitude)
                put("speed", bestLocation.speed)
                put("provider", bestLocation.provider ?: "")
            })
        } else {
            ToolResult(false, error = "Location not available")
        }
    }
}

class StorageTool : NativeTool {
    override val name = "storage"
    override val displayName = "存储"
    override val description = "查询存储空间信息"
    override val category = "system"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val stat = android.os.StatFs(context.filesDir.absolutePath)
        val totalBytes = stat.totalBytes
        val availableBytes = stat.availableBytes
        val usedBytes = totalBytes - availableBytes
        return ToolResult(true, JSONObject().apply {
            put("total_mb", totalBytes / (1024 * 1024))
            put("used_mb", usedBytes / (1024 * 1024))
            put("available_mb", availableBytes / (1024 * 1024))
            put("usage_percent", ((usedBytes * 100) / totalBytes).toInt())
        })
    }
}

class ScreenTool : NativeTool {
    override val name = "screen"
    override val displayName = "屏幕"
    override val description = "控制屏幕亮度、旋转等设置"
    override val category = "system"
    override val requiredPermissions = listOf("android.permission.WRITE_SETTINGS")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "info")
        return when (action) {
            "info" -> {
                val displayMetrics = context.resources.displayMetrics
                ToolResult(true, JSONObject().apply {
                    put("width", displayMetrics.widthPixels)
                    put("height", displayMetrics.heightPixels)
                    put("density", displayMetrics.density)
                    put("density_dpi", displayMetrics.densityDpi)
                    put("scaled_density", displayMetrics.scaledDensity)
                })
            }
            "brightness" -> {
                val brightness = params.optInt("brightness", -1)
                if (brightness in 0..255) {
                    Settings.System.putInt(context.contentResolver, Settings.System.SCREEN_BRIGHTNESS, brightness)
                    ToolResult(true, JSONObject().apply { put("brightness", brightness) })
                } else {
                    val current = Settings.System.getInt(context.contentResolver, Settings.System.SCREEN_BRIGHTNESS, 128)
                    ToolResult(true, JSONObject().apply { put("brightness", current) })
                }
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class FlashlightTool : NativeTool {
    override val name = "flashlight"
    override val displayName = "手电筒"
    override val description = "控制手机闪光灯"
    override val category = "hardware"
    override val requiredPermissions = emptyList<String>()

    private var isOn = false

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "toggle")
        val targetState = when (action) {
            "on" -> true
            "off" -> false
            else -> !isOn
        }
        try {
            val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as android.hardware.camera2.CameraManager
            val cameraId = cameraManager.cameraIdList.firstOrNull { id ->
                cameraManager.getCameraCharacteristics(id)
                    .get(android.hardware.camera2.CameraCharacteristics.FLASH_INFO_AVAILABLE) == true
            } ?: return ToolResult(false, error = "No flashlight available")
            cameraManager.setTorchMode(cameraId, targetState)
            isOn = targetState
            return ToolResult(true, JSONObject().apply { put("on", isOn) })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Flashlight control failed")
        }
    }
}

class NotificationTool : NativeTool {
    override val name = "notification"
    override val displayName = "通知"
    override val description = "发送本地通知"
    override val category = "system"
    override val requiredPermissions = listOf("android.permission.POST_NOTIFICATIONS")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val title = params.optString("title", "PolySpace")
        val text = params.optString("text", "")
        if (text.isEmpty()) return ToolResult(false, error = "Missing text")
        try {
            val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as android.app.NotificationManager
            val channelId = "polyspace_tool"
            if (manager.getNotificationChannel(channelId) == null) {
                manager.createNotificationChannel(
                    android.app.NotificationChannel(channelId, "工具通知", android.app.NotificationManager.IMPORTANCE_DEFAULT)
                )
            }
            val notification = android.app.Notification.Builder(context, channelId)
                .setContentTitle(title)
                .setContentText(text)
                .setSmallIcon(com.polyspace.mobile.R.drawable.ic_status_running)
                .setAutoCancel(true)
                .build()
            manager.notify((System.currentTimeMillis() % 10000).toInt(), notification)
            return ToolResult(true, JSONObject().apply {
                put("title", title)
                put("text", text)
            })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Notification failed")
        }
    }
}

class ShareTool : NativeTool {
    override val name = "share"
    override val displayName = "分享"
    override val description = "通过系统分享功能分享内容"
    override val category = "communication"
    override val requiredPermissions = emptyList<String>()

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val text = params.optString("text", "")
        val title = params.optString("title", "分享")
        if (text.isEmpty()) return ToolResult(false, error = "Missing text")
        try {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_TEXT, text)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            context.startActivity(Intent.createChooser(intent, title).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            return ToolResult(true, JSONObject().apply { put("shared", true) })
        } catch (e: Exception) {
            return ToolResult(false, error = e.message ?: "Share failed")
        }
    }
}

class VibrationTool : NativeTool {
    override val name = "vibration"
    override val displayName = "振动"
    override val description = "控制手机振动"
    override val category = "hardware"
    override val requiredPermissions = listOf("android.permission.VIBRATE")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "vibrate")
        val vibrator = context.getSystemService(Context.VIBRATOR_SERVICE) as android.os.Vibrator
        return when (action) {
            "vibrate" -> {
                val duration = params.optLong("duration", 200L)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(android.os.VibrationEffect.createOneShot(duration, android.os.VibrationEffect.DEFAULT_AMPLITUDE))
                } else {
                    @Suppress("DEPRECATION")
                    vibrator.vibrate(duration)
                }
                ToolResult(true, JSONObject().apply { put("vibrated", duration) })
            }
            "pattern" -> {
                val pattern = params.optString("pattern", "0,200,100,200")
                val timings = pattern.split(",").mapNotNull { it.trim().toLongOrNull() }.toLongArray()
                if (timings.isNotEmpty()) {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                        vibrator.vibrate(android.os.VibrationEffect.createWaveform(timings, -1))
                    } else {
                        @Suppress("DEPRECATION")
                        vibrator.vibrate(timings, -1)
                    }
                }
                ToolResult(true, JSONObject().apply { put("pattern", pattern) })
            }
            "cancel" -> {
                vibrator.cancel()
                ToolResult(true, JSONObject().apply { put("cancelled", true) })
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class TtsTool : NativeTool {
    override val name = "tts"
    override val displayName = "语音合成"
    override val description = "文字转语音播报"
    override val category = "media"
    override val requiredPermissions = emptyList<String>()

    private var tts: android.speech.tts.TextToSpeech? = null

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "speak")
        return when (action) {
            "speak" -> {
                val text = params.optString("text", "")
                if (text.isEmpty()) return ToolResult(false, error = "Missing text")
                if (tts == null) {
                    tts = android.speech.tts.TextToSpeech(context.applicationContext) { status ->
                        if (status == android.speech.tts.TextToSpeech.SUCCESS) {
                            tts?.language = java.util.Locale.getDefault()
                        }
                    }
                }
                val queueMode = if (params.optBoolean("flush", true))
                    android.speech.tts.TextToSpeech.QUEUE_FLUSH
                else
                    android.speech.tts.TextToSpeech.QUEUE_ADD
                tts?.speak(text, queueMode, null, "polyspace_tts_${System.currentTimeMillis()}")
                ToolResult(true, JSONObject().apply { put("speaking", true) })
            }
            "stop" -> {
                tts?.stop()
                ToolResult(true, JSONObject().apply { put("speaking", false) })
            }
            "shutdown" -> {
                tts?.stop()
                tts?.shutdown()
                tts = null
                ToolResult(true, JSONObject().apply { put("shutdown", true) })
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}

class NetworkTool : NativeTool {
    override val name = "network"
    override val displayName = "网络"
    override val description = "查询网络状态信息"
    override val category = "network"
    override val requiredPermissions = listOf("android.permission.ACCESS_NETWORK_STATE")

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val activeNetwork = cm.activeNetworkInfo
        val networkCapabilities = cm.getNetworkCapabilities(cm.activeNetwork)
        return ToolResult(true, JSONObject().apply {
            put("connected", activeNetwork?.isConnected == true)
            put("type", activeNetwork?.typeName ?: "none")
            put("wifi", networkCapabilities?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) == true)
            put("cellular", networkCapabilities?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR) == true)
            put("vpn", networkCapabilities?.hasTransport(android.net.NetworkCapabilities.TRANSPORT_VPN) == true)
            put("link_downstream", networkCapabilities?.linkDownstreamBandwidthKbps ?: 0)
            put("link_upstream", networkCapabilities?.linkUpstreamBandwidthKbps ?: 0)
        })
    }
}

object ToolInitializer {
    fun init(context: Context) {
        val tools: List<NativeTool> = listOf(
            AudioRecordTool(),
            ScreenRecordTool(),
            AlarmTool(),
            AppLauncherTool(),
            ClipboardTool(),
            ContactTool(),
            PhoneCallTool(),
            SmsTool(),
            WifiTool(),
            BatteryTool(),
            LocationTool(),
            StorageTool(),
            ScreenTool(),
            FlashlightTool(),
            NotificationTool(),
            ShareTool(),
            VibrationTool(),
            TtsTool(),
            NetworkTool(),
            ScreenOperationTool,
        )
        tools.forEach { ToolRegistry.register(it) }
    }
}
