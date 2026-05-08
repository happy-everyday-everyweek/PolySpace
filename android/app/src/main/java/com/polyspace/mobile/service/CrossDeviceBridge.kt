package com.polyspace.mobile.service

import android.content.Context
import android.util.Log
import com.polyspace.mobile.tool.ScreenOperationTool
import com.polyspace.mobile.tool.ToolRegistry
import com.polyspace.mobile.tool.ToolResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.ByteString
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

object CrossDeviceBridge {

    private const val TAG = "CrossDeviceBridge"
    private val bridgeScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    @Volatile
    private var host: String = "localhost"

    @Volatile
    private var port: Int = 8000

    @Volatile
    private var deviceId: String = ""

    @Volatile
    private var registered: Boolean = false

    private var webSocket: WebSocket? = null
    private var appContext: Context? = null
    private var reconnectAttempts: Int = 0
    private val maxReconnectAttempts: Int = 10
    private val baseReconnectInterval: Long = 3000
    private val heartbeatInterval: Long = 15000
    private var heartbeatJob: kotlinx.coroutines.Job? = null
    private val isConnecting = AtomicBoolean(false)

    private val okHttpClient: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(0, TimeUnit.MINUTES)
            .writeTimeout(10, TimeUnit.SECONDS)
            .pingInterval(heartbeatInterval, TimeUnit.MILLISECONDS)
            .build()
    }

    fun setConfig(host: String, port: Int) {
        this.host = host
        this.port = port
    }

    fun setDeviceId(id: String) {
        this.deviceId = id
    }

    fun connectWebSocket(context: Context) {
        if (!isConnecting.compareAndSet(false, true)) {
            Log.i(TAG, "WebSocket connection already in progress, skipping")
            return
        }
        appContext = context.applicationContext
        bridgeScope.launch {
            val id = deviceId.ifEmpty {
                android.provider.Settings.Secure.getString(
                    context.contentResolver,
                    android.provider.Settings.Secure.ANDROID_ID
                ) ?: "android_unknown"
            }
            deviceId = id

            val wsUrl = "ws://$host:$port/api/v1/devices/ws/$id"
            val request = Request.Builder().url(wsUrl).build()

            val oldSocket = webSocket
            if (oldSocket != null) {
                try {
                    oldSocket.close(1000, "Reconnecting")
                } catch (_: Exception) {}
                webSocket = null
            }

            webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    isConnecting.set(false)
                    Log.i(TAG, "WebSocket connected")
                    reconnectAttempts = 0
                    registered = true

                    val toolManifest = ToolRegistry.getToolManifest()
                    val capabilities = buildCapabilitiesJson(context)
                    val initMessage = JSONObject().apply {
                        put("device_name", android.os.Build.MODEL)
                        put("platform", "android")
                        put("capabilities", capabilities)
                        put("metadata", JSONObject().apply {
                            put("os_version", "Android ${android.os.Build.VERSION.RELEASE} (API ${android.os.Build.VERSION.SDK_INT})")
                            put("tools", org.json.JSONArray(toolManifest))
                        })
                    }
                    webSocket.send(initMessage.toString())
                    startHeartbeat()
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    handleMessage(text)
                }

                override fun onMessage(webSocket: WebSocket, bytes: ByteString) {}

                override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                    webSocket.close(1000, null)
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    isConnecting.set(false)
                    Log.i(TAG, "WebSocket closed: $code $reason")
                    registered = false
                    scheduleReconnect()
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    isConnecting.set(false)
                    Log.e(TAG, "WebSocket failure: ${t.message}")
                    registered = false
                    scheduleReconnect()
                }
            })
        }
    }

    private fun buildCapabilitiesJson(context: Context): org.json.JSONArray {
        val caps = org.json.JSONArray()
        val toolList = listOf(
            "audio_record" to listOf("record", "stop"),
            "alarm" to listOf("set", "cancel"),
            "app_launcher" to listOf("launch", "info"),
            "clipboard" to listOf("read", "write"),
            "contact" to listOf("query", "detail"),
            "phone_call" to listOf("dial", "end"),
            "sms" to listOf("send", "read"),
            "wifi" to listOf("status", "enable", "disable"),
            "battery" to listOf("status"),
            "location" to listOf("current"),
            "storage" to listOf("info"),
            "screen" to listOf("info", "screenshot"),
            "flashlight" to listOf("on", "off"),
            "notification" to listOf("send", "cancel"),
            "share" to listOf("text", "file"),
            "vibration" to listOf("vibrate"),
            "tts" to listOf("speak", "stop"),
            "network" to listOf("status"),
            "screen_operation" to listOf("click", "long_press", "swipe", "input_text", "scroll_up", "scroll_down", "back", "home", "recents", "screenshot")
        )
        for ((name, actions) in toolList) {
            caps.put(JSONObject().apply {
                put("name", name)
                put("description", "$name tool on Android device")
                put("actions", org.json.JSONArray(actions))
            })
        }
        return caps
    }

    private fun handleMessage(text: String) {
        try {
            val json = JSONObject(text)
            val type = json.optString("type", "")

            when (type) {
                "register_ack" -> {
                    val accepted = json.optBoolean("accepted", false)
                    Log.i(TAG, "Registration ${if (accepted) "accepted" else "rejected"}")
                }
                "heartbeat_ack" -> {}
                "tool_call" -> {
                    val ctx = appContext ?: return
                    val requestId = json.optString("request_id", "")
                    val tool = json.optString("tool", "")
                    val action = json.optString("action", "execute")
                    val params = json.optJSONObject("params") ?: JSONObject()

                    bridgeScope.launch {
                        val result = executeToolLocally(ctx, tool, params)
                        sendToolResult(requestId, result)
                    }
                }
                "disconnect" -> {
                    disconnect()
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to handle message: ${e.message}")
        }
    }

    private fun sendToolResult(requestId: String, result: ToolResult) {
        val message = JSONObject().apply {
            put("type", "tool_result")
            put("request_id", requestId)
            put("result", result.toJson())
        }
        webSocket?.send(message.toString())
    }

    private fun startHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = bridgeScope.launch {
            while (true) {
                try {
                    val message = JSONObject().apply {
                        put("type", "heartbeat")
                        put("timestamp", System.currentTimeMillis() / 1000.0)
                    }
                    webSocket?.send(message.toString())
                } catch (e: Exception) {
                    Log.d(TAG, "Heartbeat error: ${e.message}")
                }
                kotlinx.coroutines.delay(heartbeatInterval)
            }
        }
    }

    private fun scheduleReconnect() {
        if (reconnectAttempts >= maxReconnectAttempts) {
            Log.e(TAG, "Max reconnect attempts reached")
            return
        }
        val delay = (baseReconnectInterval * Math.pow(1.5, reconnectAttempts.toDouble())).toLong()
        reconnectAttempts++
        Log.i(TAG, "Reconnecting in ${delay}ms (attempt $reconnectAttempts/$maxReconnectAttempts)")

        bridgeScope.launch {
            kotlinx.coroutines.delay(delay)
            appContext?.let { connectWebSocket(it) }
        }
    }

    fun registerDevice(context: Context) {
        connectWebSocket(context)
    }

    suspend fun executeToolLocally(context: Context, toolName: String, params: JSONObject): ToolResult {
        return withContext(Dispatchers.IO) {
            val tool = ToolRegistry.getTool(toolName)
            if (tool == null) {
                ToolResult(false, error = "Tool not found: $toolName")
            } else {
                try {
                    tool.execute(context, params)
                } catch (e: Exception) {
                    ToolResult(false, error = e.message ?: "Execution error")
                }
            }
        }
    }

    suspend fun executeScreenOperation(
        context: Context,
        instruction: String
    ): List<ScreenOperationTool.ScreenAction> {
        return ScreenOperationTool.analyzeWithScreenshot(context, instruction, host, port)
    }

    fun pollRemoteCommands(context: Context) {
        connectWebSocket(context)
    }

    fun syncState(context: Context) {
        bridgeScope.launch {
            try {
                val prefs = context.getSharedPreferences("polyspace_backend", 0)
                val statusMessage = JSONObject().apply {
                    put("type", "status_update")
                    put("status", "online")
                    put("device_id", deviceId)
                    put("backend_status", BackendService.getStatus().name)
                    put("message_listener", MessageBridge.isNotificationListenerEnabled(context))
                    put("accessibility", com.polyspace.mobile.accessibility.AccessibilityBridge.isServiceRunning())
                    put("auto_start", prefs.getBoolean("auto_start", true))
                    put("tools_count", ToolRegistry.tools.size)
                }
                webSocket?.send(statusMessage.toString())
            } catch (e: Exception) {
                Log.d(TAG, "State sync error: ${e.message}")
            }
        }
    }

    fun sendCapabilityUpdate(context: Context) {
        val capabilities = buildCapabilitiesJson(context)
        val message = JSONObject().apply {
            put("type", "capability_update")
            put("capabilities", capabilities)
        }
        webSocket?.send(message.toString())
    }

    fun disconnect() {
        heartbeatJob?.cancel()
        reconnectAttempts = maxReconnectAttempts
        isConnecting.set(false)
        val message = JSONObject().apply {
            put("type", "disconnect")
            put("reason", "client_shutdown")
        }
        webSocket?.send(message.toString())
        webSocket?.close(1000, "Client shutdown")
        webSocket = null
        registered = false
    }

    fun isRegistered(): Boolean = registered
    fun isConnected(): Boolean = webSocket != null && registered
}
