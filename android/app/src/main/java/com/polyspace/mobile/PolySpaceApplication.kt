package com.polyspace.mobile

import android.app.Application
import android.content.Context
import android.util.Log
import com.polyspace.mobile.accessibility.AccessibilityBridge
import com.polyspace.mobile.service.BackendService
import com.polyspace.mobile.service.BackendStatus
import com.polyspace.mobile.tool.ToolInitializer

class PolySpaceApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        AccessibilityBridge.init(this)
        ToolInitializer.init(this)
        ensureDefaultPreferences(this)
        autoStartBackendIfNeeded(this)
    }

    private fun ensureDefaultPreferences(context: Context) {
        val prefs = context.getSharedPreferences(BackendService.PREFS_NAME, 0)
        if (!prefs.contains("auto_start")) {
            prefs.edit().putBoolean("auto_start", true).apply()
        }
        if (!prefs.contains("use_local_linux")) {
            prefs.edit().putBoolean("use_local_linux", true).apply()
        }
        if (!prefs.contains("host")) {
            prefs.edit().putString("host", "localhost").apply()
        }
        if (!prefs.contains("port")) {
            prefs.edit().putInt("port", 8000).apply()
        }
    }

    private fun autoStartBackendIfNeeded(context: Context) {
        try {
            val prefs = context.getSharedPreferences(BackendService.PREFS_NAME, 0)
            val autoStart = prefs.getBoolean("auto_start", true)
            if (!autoStart) return

            if (BackendService.getStatus() == BackendStatus.RUNNING ||
                BackendService.getStatus() == BackendStatus.STARTING
            ) {
                Log.i(TAG, "Backend already running or starting, skip auto-start")
                return
            }

            val useLocalLinux = prefs.getBoolean("use_local_linux", true)
            val host = prefs.getString("host", "localhost") ?: "localhost"
            val port = prefs.getInt("port", 8000)

            Log.i(TAG, "Auto-starting backend: $host:$port, local=$useLocalLinux")
            BackendService.start(context, host, port, useLocalLinux)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to auto-start backend", e)
        }
    }

    companion object {
        const val TAG = "PolySpaceApp"
    }
}
