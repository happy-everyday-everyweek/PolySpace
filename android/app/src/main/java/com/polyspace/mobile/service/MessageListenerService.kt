package com.polyspace.mobile.service

import android.content.Context
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import org.json.JSONObject

class MessageListenerService : NotificationListenerService() {

    override fun onListenerConnected() {
        super.onListenerConnected()
        Log.i(TAG, "Message listener connected")
        MessageBridge.onServiceConnected(this)

        activeNotifications?.forEach { sbn ->
            val appName = getAppName(sbn.packageName)
            if (appName != null) {
                NotificationStore.upsert(sbn, appName)
            }
        }
    }

    override fun onListenerDisconnected() {
        super.onListenerDisconnected()
        Log.i(TAG, "Message listener disconnected")
        MessageBridge.onServiceDisconnected()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val packageName = sbn.packageName
        val appName = getAppName(packageName)
        if (appName == null) return

        NotificationStore.upsert(sbn, appName)

        try {
            val notification = sbn.notification
            val extras = notification.extras

            val title = extras.getCharSequence("android.title")?.toString() ?: ""
            val text = extras.getCharSequence("android.text")?.toString() ?: ""
            val bigText = extras.getCharSequence("android.bigText")?.toString() ?: text

            if (title.isEmpty() && text.isEmpty()) return

            val message = JSONObject().apply {
                put("source", packageName)
                put("source_name", appName)
                put("title", title)
                put("text", if (bigText.isNotEmpty()) bigText else text)
                put("sub_text", extras.getCharSequence("android.subText")?.toString() ?: "")
                put("category", extras.getString("android.category") ?: "")
                put("timestamp", sbn.postTime)
                put("is_group", title.contains("群") || text.contains("群"))
            }

            Log.d(TAG, "Message from $appName: $title - ${message.optString("text").take(50)}")
            MessageBridge.onMessageReceived(message)
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing notification from $packageName", e)
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        super.onNotificationRemoved(sbn)
        if (sbn != null) {
            NotificationStore.remove(sbn)
        }
    }

    private fun getAppName(packageName: String): String? {
        val monitoredApps = getMonitoredApps(this)
        if (!monitoredApps.containsKey(packageName)) return null
        return monitoredApps[packageName]
    }

    companion object {
        const val TAG = "MessageListener"
        const val PREFS_NAME = "polyspace_message_listener"
        const val KEY_MONITORED_APPS = "monitored_apps"
        const val KEY_CUSTOM_APPS = "custom_apps"

        val DEFAULT_MONITORED_APPS = mapOf(
            "com.tencent.mm" to "微信",
            "com.tencent.mobileqq" to "QQ",
            "com.alibaba.android.rimet" to "钉钉",
            "com.ss.android.lark" to "飞书",
            "com.android.mms" to "短信",
            "com.google.android.apps.messaging" to "短信",
        )

        val AVAILABLE_APPS = mapOf(
            "com.tencent.mm" to "微信",
            "com.tencent.mobileqq" to "QQ",
            "com.alibaba.android.rimet" to "钉钉",
            "com.ss.android.lark" to "飞书",
            "com.android.mms" to "短信",
            "com.google.android.apps.messaging" to "短信",
            "com.tencent.tim" to "TIM",
            "com.eg.android.AlipayGphone" to "支付宝",
            "com.sina.weibo" to "微博",
            "com.ss.android.ugc.aweme" to "抖音",
            "com.smile.gifmaker" to "快手",
            "com.xunmeng.pinduoduo" to "拼多多",
            "com.jingdong.app.mall" to "京东",
            "com.taobao.taobao" to "淘宝",
            "com.tencent.wework" to "企业微信",
            "com.microsoft.teams" to "Teams",
            "com.slack" to "Slack",
            "org.telegram.messenger" to "Telegram",
            "com.whatsapp" to "WhatsApp",
            "com.discord" to "Discord",
            "com.twitter.android" to "X (Twitter)",
        )

        fun getMonitoredApps(context: Context): Map<String, String> {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            val enabledDefaults = prefs.getStringSet(KEY_MONITORED_APPS, null)
            val result = mutableMapOf<String, String>()

            if (enabledDefaults == null) {
                result.putAll(DEFAULT_MONITORED_APPS)
            } else {
                for (pkg in enabledDefaults) {
                    AVAILABLE_APPS[pkg]?.let { result[pkg] = it }
                }
            }

            val customApps = prefs.getString(KEY_CUSTOM_APPS, "") ?: ""
            if (customApps.isNotEmpty()) {
                try {
                    val json = org.json.JSONObject(customApps)
                    val keys = json.keys()
                    while (keys.hasNext()) {
                        val pkg = keys.next()
                        result[pkg] = json.getString(pkg)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Failed to parse custom apps", e)
                }
            }

            return result
        }

        fun setMonitoredApps(context: Context, packages: Set<String>) {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            prefs.edit().putStringSet(KEY_MONITORED_APPS, packages).apply()
        }

        fun addCustomApp(context: Context, packageName: String, appName: String) {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            val customApps = prefs.getString(KEY_CUSTOM_APPS, "{}") ?: "{}"
            try {
                val json = org.json.JSONObject(customApps)
                json.put(packageName, appName)
                prefs.edit().putString(KEY_CUSTOM_APPS, json.toString()).apply()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to add custom app", e)
            }
        }

        fun removeCustomApp(context: Context, packageName: String) {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            val customApps = prefs.getString(KEY_CUSTOM_APPS, "{}") ?: "{}"
            try {
                val json = org.json.JSONObject(customApps)
                json.remove(packageName)
                prefs.edit().putString(KEY_CUSTOM_APPS, json.toString()).apply()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to remove custom app", e)
            }
        }

        fun getCustomApps(context: Context): Map<String, String> {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            val customApps = prefs.getString(KEY_CUSTOM_APPS, "{}") ?: "{}"
            val result = mutableMapOf<String, String>()
            try {
                val json = org.json.JSONObject(customApps)
                val keys = json.keys()
                while (keys.hasNext()) {
                    val pkg = keys.next()
                    result[pkg] = json.getString(pkg)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Failed to parse custom apps", e)
            }
            return result
        }
    }
}
