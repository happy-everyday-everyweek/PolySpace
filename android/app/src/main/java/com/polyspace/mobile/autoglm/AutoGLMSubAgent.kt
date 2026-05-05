package com.polyspace.mobile.autoglm

import android.graphics.Rect
import com.polyspace.mobile.accessibility.AccessibilityBridge
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody

object AutoGLMSubAgent {

    private const val MODEL_ENDPOINT = "http://localhost:8000/api/v1/models/autoglm"

    private val okHttpClient: okhttp3.OkHttpClient by lazy {
        okhttp3.OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .build()
    }

    data class ScreenAction(
        val type: String,
        val params: Map<String, Any>
    )

    data class ActionResult(
        val success: Boolean,
        val message: String,
        val screenshot: String? = null
    )

    suspend fun analyzeScreen(instruction: String): List<ScreenAction> {
        return withContext(Dispatchers.IO) {
            try {
                val uiHierarchy = AccessibilityBridge.getUIHierarchy() ?: return@withContext emptyList()
                val currentActivity = AccessibilityBridge.getCurrentActivityName() ?: "unknown"

                val requestPayload = JSONObject().apply {
                    put("instruction", instruction)
                    put("ui_hierarchy", uiHierarchy)
                    put("current_activity", currentActivity)
                    put("screen_size", getScreenSize())
                }

                val actions = callAutoGLMModel(requestPayload)
                parseActions(actions)
            } catch (e: Exception) {
                emptyList()
            }
        }
    }

    suspend fun executeAction(action: ScreenAction): ActionResult {
        return withContext(Dispatchers.IO) {
            try {
                val success = when (action.type) {
                    "click" -> {
                        val x = action.params["x"] as? Int ?: return@withContext ActionResult(false, "Missing x coordinate")
                        val y = action.params["y"] as? Int ?: return@withContext ActionResult(false, "Missing y coordinate")
                        AccessibilityBridge.performClick(x, y)
                    }
                    "long_press" -> {
                        val x = action.params["x"] as? Int ?: return@withContext ActionResult(false, "Missing x coordinate")
                        val y = action.params["y"] as? Int ?: return@withContext ActionResult(false, "Missing y coordinate")
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
                    else -> return@withContext ActionResult(false, "Unknown action type: ${action.type}")
                }

                ActionResult(success = success, message = if (success) "Action executed" else "Action failed")
            } catch (e: Exception) {
                ActionResult(success = false, message = e.message ?: "Execution error")
            }
        }
    }

    suspend fun executeActions(actions: List<ScreenAction>): List<ActionResult> {
        val results = mutableListOf<ActionResult>()
        for (action in actions) {
            val result = executeAction(action)
            results.add(result)
            if (!result.success) break
            kotlinx.coroutines.delay(500)
        }
        return results
    }

    private fun getScreenSize(): JSONObject {
        return try {
            val context = com.polyspace.mobile.accessibility.AccessibilityBridge.appContext
            val metrics = context?.resources?.displayMetrics
            JSONObject().apply {
                put("width", metrics?.widthPixels ?: 1080)
                put("height", metrics?.heightPixels ?: 2400)
            }
        } catch (e: Exception) {
            JSONObject().apply {
                put("width", 1080)
                put("height", 2400)
            }
        }
    }

    private fun callAutoGLMModel(payload: JSONObject): JSONArray {
        val body = payload.toString()
            .toRequestBody("application/json".toMediaType())
        val request = okhttp3.Request.Builder()
            .url(MODEL_ENDPOINT)
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
}
