package com.polyspace.mobile.service

import android.service.notification.StatusBarNotification
import android.util.Log
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import org.json.JSONObject
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.LinkedBlockingQueue

object NotificationStore {

    private const val TAG = "NotificationStore"
    private const val MAX_CACHE_SIZE = 50

    private val _messages = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val messages: SharedFlow<JSONObject> = _messages.asSharedFlow()

    private val cache = LinkedBlockingQueue<JSONObject>(MAX_CACHE_SIZE)
    private val activeNotifications = ConcurrentHashMap<String, JSONObject>()

    fun upsert(sbn: StatusBarNotification, appName: String) {
        try {
            val notification = sbn.notification
            val extras = notification.extras

            val title = extras.getCharSequence("android.title")?.toString() ?: ""
            val text = extras.getCharSequence("android.text")?.toString() ?: ""
            val subText = extras.getCharSequence("android.subText")?.toString() ?: ""
            val bigText = extras.getCharSequence("android.bigText")?.toString() ?: text
            val textLines = extras.getCharSequenceArray("android.textLines")

            if (title.isEmpty() && text.isEmpty()) return

            val key = sbn.key
            val message = JSONObject().apply {
                put("id", key)
                put("source", sbn.packageName)
                put("source_name", appName)
                put("title", title)
                put("text", if (bigText.isNotEmpty()) bigText else text)
                put("sub_text", subText)
                put("category", extras.getString("android.category") ?: "")
                put("timestamp", sbn.postTime)
                put("is_group", title.contains("群") || text.contains("群"))
                put("is_ongoing", sbn.isOngoing)
                if (textLines != null && textLines.isNotEmpty()) {
                    put("text_lines", textLines.map { it.toString() })
                }
            }

            val existing = activeNotifications[key]
            if (existing != null && existing.optString("text") == message.optString("text")) {
                return
            }

            activeNotifications[key] = message
            while (cache.size >= MAX_CACHE_SIZE) {
                cache.poll()
            }
            cache.offer(message)
            _messages.tryEmit(message)
        } catch (e: Exception) {
            Log.e(TAG, "Error upserting notification", e)
        }
    }

    fun remove(sbn: StatusBarNotification) {
        activeNotifications.remove(sbn.key)
    }

    fun snapshot(limit: Int = 50, includeOngoing: Boolean = false): List<JSONObject> {
        return cache.toList()
            .filter { includeOngoing || !it.optBoolean("is_ongoing", false) }
            .takeLast(limit)
    }

    fun getActiveNotifications(): List<JSONObject> {
        return activeNotifications.values.toList()
    }

    fun clear() {
        cache.clear()
        activeNotifications.clear()
    }
}
