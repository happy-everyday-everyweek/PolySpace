package com.polyspace.mobile.service

import android.content.ComponentName
import android.content.Context
import android.provider.Settings
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.ConcurrentLinkedQueue

object MessageBridge {

    private const val TAG = "MessageBridge"
    private const val MAX_PENDING_MESSAGES = 50

    private val bridgeScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _messages = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val messages: SharedFlow<JSONObject> = _messages.asSharedFlow()

    private val pendingMessages = ConcurrentLinkedQueue<JSONObject>()
    private var service: MessageListenerService? = null

    @Volatile
    private var host: String = "localhost"

    @Volatile
    private var port: Int = 8000

    @Volatile
    private var autoForward: Boolean = false

    fun onServiceConnected(service: MessageListenerService) {
        this.service = service
        Log.i(TAG, "Message bridge connected")
    }

    fun onServiceDisconnected() {
        this.service = null
        Log.i(TAG, "Message bridge disconnected")
    }

    fun onMessageReceived(message: JSONObject) {
        _messages.tryEmit(message)

        while (pendingMessages.size >= MAX_PENDING_MESSAGES) {
            pendingMessages.poll()
        }
        pendingMessages.add(message)

        if (autoForward) {
            forwardToBackend(message)
        }
    }

    fun isNotificationListenerEnabled(context: Context): Boolean {
        val cn = ComponentName(context, MessageListenerService::class.java)
        val flat = Settings.Secure.getString(
            context.contentResolver,
            "enabled_notification_listeners"
        ) ?: return false
        return flat.contains(cn.flattenToString())
    }

    fun setAutoForward(enabled: Boolean) {
        autoForward = enabled
    }

    fun isAutoForwardEnabled(): Boolean = autoForward

    fun setBackendConfig(host: String, port: Int) {
        this.host = host
        this.port = port
    }

    fun getPendingMessages(): List<JSONObject> {
        return pendingMessages.toList()
    }

    fun clearPendingMessages() {
        pendingMessages.clear()
    }

    private fun forwardToBackend(message: JSONObject) {
        bridgeScope.launch {
            try {
                val url = URL("http://$host:$port/api/v1/ai/coordination/messages/incoming")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.connectTimeout = 5000
                conn.readTimeout = 5000

                conn.outputStream.use { os ->
                    os.write(message.toString().toByteArray())
                }

                val code = conn.responseCode
                conn.disconnect()
                Log.d(TAG, "Forwarded message to backend, response: $code")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to forward message to backend", e)
            }
        }
    }

    fun requestAiSuggestion(
        host: String,
        port: Int,
        message: JSONObject,
        callback: (JSONObject?) -> Unit
    ) {
        bridgeScope.launch {
            try {
                val url = URL("http://$host:$port/api/v1/ai/coordination/messages/suggest")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.doOutput = true
                conn.setRequestProperty("Content-Type", "application/json")
                conn.connectTimeout = 10000
                conn.readTimeout = 30000

                conn.outputStream.use { os ->
                    os.write(message.toString().toByteArray())
                }

                if (conn.responseCode == 200) {
                    val response = conn.inputStream.bufferedReader().readText()
                    withContext(Dispatchers.Main) {
                        callback(JSONObject(response))
                    }
                } else {
                    withContext(Dispatchers.Main) {
                        callback(null)
                    }
                }
                conn.disconnect()
            } catch (e: Exception) {
                Log.e(TAG, "Failed to get AI suggestion", e)
                withContext(Dispatchers.Main) {
                    callback(null)
                }
            }
        }
    }
}
