package com.polyspace.mobile.tool

import android.content.Context
import android.graphics.Bitmap
import android.util.Base64
import android.util.Log
import com.polyspace.mobile.accessibility.AccessibilityBridge
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.io.File

object ScreenOperationTool : NativeTool {
    override val name = "screen_operation"
    override val displayName = "屏幕操作"
    override val description = "通过多模态AI分析屏幕截图并执行点击、滑动、输入等操作"
    override val category = "accessibility"
    override val requiredPermissions = emptyList<String>()

    private const val TAG = "ScreenOp"
    private const val SCREENSHOT_QUALITY = 80
    private const val MAX_SCREENSHOT_SIZE = 1920

    private val okHttpClient: okhttp3.OkHttpClient by lazy {
        okhttp3.OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
            .build()
    }

    data class ScreenAction(
        val type: String,
        val params: Map<String, Any>
    )

    data class ActionResult(
        val success: Boolean,
        val message: String,
        val screenshotBase64: String? = null,
        val extraData: JSONObject? = null
    )

    suspend fun analyzeWithScreenshot(
        context: Context,
        instruction: String,
        host: String,
        port: Int
    ): List<ScreenAction> {
        return withContext(Dispatchers.IO) {
            try {
                val screenshotBase64 = takeScreenshotBase64(context)
                val uiHierarchy = AccessibilityBridge.getUIHierarchy() ?: ""
                val currentActivity = AccessibilityBridge.getCurrentActivityName() ?: "unknown"
                val displayMetrics = context.resources.displayMetrics
                val screenWidth = displayMetrics.widthPixels
                val screenHeight = displayMetrics.heightPixels

                val requestPayload = JSONObject().apply {
                    put("instruction", instruction)
                    put("ui_hierarchy", uiHierarchy)
                    put("current_activity", currentActivity)
                    put("screen_width", screenWidth)
                    put("screen_height", screenHeight)
                    if (screenshotBase64 != null) {
                        put("screenshot", screenshotBase64)
                        put("screenshot_format", "jpeg")
                        put("has_multimodal_input", true)
                    } else {
                        put("has_multimodal_input", false)
                    }
                }

                val actions = callModel(host, port, requestPayload)
                parseActions(actions)
            } catch (e: Exception) {
                Log.e(TAG, "analyzeWithScreenshot failed", e)
                emptyList()
            }
        }
    }

    suspend fun executeAction(context: Context, action: ScreenAction): ActionResult {
        return withContext(Dispatchers.IO) {
            try {
                val success = when (action.type) {
                    "click" -> {
                        val x = action.params["x"] as? Int ?: return@withContext ActionResult(false, "Missing x")
                        val y = action.params["y"] as? Int ?: return@withContext ActionResult(false, "Missing y")
                        AccessibilityBridge.performClick(x, y)
                    }
                    "long_press" -> {
                        val x = action.params["x"] as? Int ?: return@withContext ActionResult(false, "Missing x")
                        val y = action.params["y"] as? Int ?: return@withContext ActionResult(false, "Missing y")
                        AccessibilityBridge.performLongPress(x, y)
                    }
                    "swipe" -> {
                        val startX = action.params["start_x"] as? Int ?: return@withContext ActionResult(false, "Missing start_x")
                        val startY = action.params["start_y"] as? Int ?: return@withContext ActionResult(false, "Missing start_y")
                        val endX = action.params["end_x"] as? Int ?: return@withContext ActionResult(false, "Missing end_x")
                        val endY = action.params["end_y"] as? Int ?: return@withContext ActionResult(false, "Missing end_y")
                        val duration = action.params["duration"] as? Long ?: 300L
                        AccessibilityBridge.performSwipe(startX, startY, endX, endY, duration)
                    }
                    "input_text" -> {
                        val nodeId = action.params["node_id"] as? String ?: return@withContext ActionResult(false, "Missing node_id")
                        val text = action.params["text"] as? String ?: return@withContext ActionResult(false, "Missing text")
                        AccessibilityBridge.setTextOnNode(nodeId, text)
                    }
                    "global_action" -> {
                        val actionId = action.params["action_id"] as? Int ?: return@withContext ActionResult(false, "Missing action_id")
                        AccessibilityBridge.performGlobalAction(actionId)
                    }
                    "scroll_up" -> {
                        val x = action.params["x"] as? Int ?: (action.params["screen_width"] as? Int ?: 540) / 2
                        val y = action.params["y"] as? Int ?: (action.params["screen_height"] as? Int ?: 2400) * 3 / 4
                        AccessibilityBridge.performSwipe(x, y, x, y / 2, 300L)
                    }
                    "scroll_down" -> {
                        val x = action.params["x"] as? Int ?: (action.params["screen_width"] as? Int ?: 540) / 2
                        val y = action.params["y"] as? Int ?: (action.params["screen_height"] as? Int ?: 2400) / 4
                        AccessibilityBridge.performSwipe(x, y, x, y * 3, 300L)
                    }
                    "back" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_BACK)
                    "home" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_HOME)
                    "recents" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_RECENTS)
                    "notifications" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_NOTIFICATIONS)
                    "quick_settings" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_QUICK_SETTINGS)
                    "power_dialog" -> AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_POWER_DIALOG)
                    "lock_screen" -> {
                        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.P) {
                            AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_LOCK_SCREEN)
                        } else false
                    }
                    "take_screenshot" -> {
                        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.R) {
                            AccessibilityBridge.performGlobalAction(android.accessibilityservice.AccessibilityService.GLOBAL_ACTION_TAKE_SCREENSHOT)
                        } else false
                    }
                    "open_app" -> {
                        val packageName = action.params["package_name"] as? String
                            ?: return@withContext ActionResult(false, "Missing package_name")
                        try {
                            val launchIntent = context.packageManager.getLaunchIntentForPackage(packageName)
                            if (launchIntent != null) {
                                launchIntent.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                                context.startActivity(launchIntent)
                                true
                            } else {
                                false
                            }
                        } catch (e: Exception) {
                            Log.e(TAG, "open_app failed for $packageName", e)
                            false
                        }
                    }
                    "get_app_list" -> {
                        try {
                            val pm = context.packageManager
                            val apps = pm.getInstalledApplications(0)
                            val appList = JSONArray()
                            for (i in apps.indices) {
                                val appInfo = apps[i]
                                val isSystem = (appInfo.flags.toInt() and android.content.pm.ApplicationInfo.FLAG_SYSTEM) != 0
                                val label = try {
                                    appInfo.loadLabel(pm).toString()
                                } catch (e: Exception) {
                                    appInfo.packageName
                                }
                                appList.put(JSONObject().apply {
                                    put("package_name", appInfo.packageName)
                                    put("label", label)
                                    put("is_system", isSystem)
                                })
                            }
                            return@withContext ActionResult(success = true, message = "OK", extraData = JSONObject().apply {
                                put("apps", appList)
                                put("total_count", apps.size)
                            })
                        } catch (e: Exception) {
                            Log.e(TAG, "get_app_list failed", e)
                            return@withContext ActionResult(success = false, message = e.message ?: "Error")
                        }
                    }
                    else -> return@withContext ActionResult(false, "Unknown action: ${action.type}")
                }
                ActionResult(success = success, message = if (success) "OK" else "Failed")
            } catch (e: Exception) {
                ActionResult(success = false, message = e.message ?: "Error")
            }
        }
    }

    suspend fun executeActions(context: Context, actions: List<ScreenAction>): List<ActionResult> {
        val results = mutableListOf<ActionResult>()
        for (action in actions) {
            val result = executeAction(context, action)
            results.add(result)
            if (!result.success) break
            kotlinx.coroutines.delay(500)
        }
        return results
    }

    private fun takeScreenshotBase64(context: Context): String? {
        val file = File(context.cacheDir, "screen_op_${System.currentTimeMillis()}.jpg")
        val success = AccessibilityBridge.takeScreenshot(file.absolutePath, "jpg")
        if (!success || !file.exists()) return null
        var bitmap: android.graphics.Bitmap? = null
        var scaled: Bitmap? = null
        var stream: ByteArrayOutputStream? = null
        return try {
            bitmap = android.graphics.BitmapFactory.decodeFile(file.absolutePath) ?: return null
            scaled = scaleBitmap(bitmap)
            stream = ByteArrayOutputStream()
            scaled.compress(Bitmap.CompressFormat.JPEG, SCREENSHOT_QUALITY, stream)
            val base64 = Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP)
            base64
        } catch (e: Exception) {
            Log.e(TAG, "Screenshot base64 failed", e)
            null
        } finally {
            try { stream?.close() } catch (_: Exception) {}
            if (scaled != null && scaled !== bitmap) scaled.recycle()
            bitmap?.recycle()
            file.delete()
        }
    }

    private fun scaleBitmap(bitmap: Bitmap): Bitmap {
        if (bitmap.width <= MAX_SCREENSHOT_SIZE && bitmap.height <= MAX_SCREENSHOT_SIZE) {
            return bitmap
        }
        val scale = MAX_SCREENSHOT_SIZE.toFloat() / maxOf(bitmap.width, bitmap.height)
        val newWidth = (bitmap.width * scale).toInt()
        val newHeight = (bitmap.height * scale).toInt()
        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }

    private fun callModel(host: String, port: Int, payload: JSONObject): JSONArray {
        val body = payload.toString()
            .toRequestBody("application/json".toMediaType())
        val request = okhttp3.Request.Builder()
            .url("http://$host:$port/api/v1/models/autoglm")
            .post(body)
            .build()
        try {
            okHttpClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return JSONArray()
                val responseBody = response.body?.string() ?: return JSONArray()
                val json = JSONObject(responseBody)
                return json.optJSONArray("actions") ?: JSONArray()
            }
        } catch (e: Exception) {
            Log.e(TAG, "Model call failed", e)
            return JSONArray()
        }
    }

    private fun parseActions(actionsJson: JSONArray): List<ScreenAction> {
        val actions = mutableListOf<ScreenAction>()
        for (i in 0 until actionsJson.length()) {
            val actionObj = actionsJson.getJSONObject(i)
            val type = actionObj.getString("type")
            val paramsObj = actionObj.optJSONObject("params") ?: JSONObject()
            val params = mutableMapOf<String, Any>()
            val keys = paramsObj.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                val value = paramsObj.get(key)
                params[key] = when (value) {
                    is Int -> value
                    is Long -> value.toInt()
                    is Double -> value
                    is String -> value
                    is Boolean -> value
                    else -> value.toString()
                }
            }
            actions.add(ScreenAction(type, params))
        }
        return actions
    }

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "analyze")
        val host = params.optString("host", "localhost")
        val port = params.optInt("port", 8000)
        return when (action) {
            "analyze" -> {
                val instruction = params.optString("instruction", "")
                if (instruction.isEmpty()) return ToolResult(false, error = "Missing instruction")
                val actions = analyzeWithScreenshot(context, instruction, host, port)
                ToolResult(true, JSONObject().apply {
                    put("action_count", actions.size)
                    put("actions", JSONArray(actions.map { a ->
                        JSONObject().apply {
                            put("type", a.type)
                            put("params", JSONObject(a.params))
                        }
                    }))
                })
            }
            "execute" -> {
                val type = params.optString("type", "")
                if (type.isEmpty()) return ToolResult(false, error = "Missing type")
                val actionParams = mutableMapOf<String, Any>()
                val paramsObj = params.optJSONObject("params")
                if (paramsObj != null) {
                    val keys = paramsObj.keys()
                    while (keys.hasNext()) {
                        val key = keys.next()
                        actionParams[key] = paramsObj.get(key)
                    }
                }
                val result = executeAction(context, ScreenAction(type, actionParams))
                ToolResult(result.success, JSONObject().apply {
                    put("message", result.message)
                })
            }
            "screenshot" -> {
                val base64 = takeScreenshotBase64(context)
                if (base64 != null) {
                    ToolResult(true, JSONObject().apply {
                        put("screenshot_length", base64.length)
                        put("format", "jpeg")
                    })
                } else {
                    ToolResult(false, error = "Screenshot failed")
                }
            }
            "open_app" -> {
                val packageName = params.optString("package_name", "")
                if (packageName.isEmpty()) return ToolResult(false, error = "Missing package_name")
                val result = executeAction(context, ScreenAction("open_app", mapOf("package_name" to packageName)))
                ToolResult(result.success, JSONObject().apply {
                    put("message", result.message)
                })
            }
            "get_app_list" -> {
                val result = executeAction(context, ScreenAction("get_app_list", emptyMap()))
                if (result.success && result.extraData != null) {
                    ToolResult(true, result.extraData)
                } else {
                    ToolResult(false, error = result.message)
                }
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}
