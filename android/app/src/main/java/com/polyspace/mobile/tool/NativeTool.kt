package com.polyspace.mobile.tool

import android.content.Context
import android.util.Log
import org.json.JSONObject

interface NativeTool {
    val name: String
    val displayName: String
    val description: String
    val category: String
    val requiredPermissions: List<String>

    suspend fun execute(context: Context, params: JSONObject): ToolResult
}

data class ToolResult(
    val success: Boolean,
    val data: JSONObject = JSONObject(),
    val error: String = ""
) {
    fun toJson(): JSONObject {
        return JSONObject().apply {
            put("success", success)
            put("data", data)
            if (error.isNotEmpty()) put("error", error)
        }
    }
}

object ToolRegistry {
    private const val TAG = "ToolRegistry"
    private val _tools = mutableMapOf<String, NativeTool>()
    val tools: Map<String, NativeTool> get() = _tools.toMap()

    fun register(tool: NativeTool) {
        _tools[tool.name] = tool
        Log.d(TAG, "Registered tool: ${tool.name}")
    }

    fun unregister(name: String) {
        _tools.remove(name)
    }

    fun getTool(name: String): NativeTool? = _tools[name]

    fun getToolsByCategory(category: String): List<NativeTool> {
        return _tools.values.filter { it.category == category }
    }

    fun getAllCategories(): List<String> {
        return _tools.values.map { it.category }.distinct()
    }

    fun getToolManifest(): List<JSONObject> {
        return _tools.values.map { tool ->
            JSONObject().apply {
                put("name", tool.name)
                put("display_name", tool.displayName)
                put("description", tool.description)
                put("category", tool.category)
                put("required_permissions", tool.requiredPermissions)
            }
        }
    }
}
