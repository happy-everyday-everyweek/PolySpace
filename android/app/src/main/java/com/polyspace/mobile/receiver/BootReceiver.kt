package com.polyspace.mobile.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.polyspace.mobile.service.BackendService
import com.polyspace.mobile.service.BackendStatus

class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Intent.ACTION_BOOT_COMPLETED &&
            intent.action != Intent.ACTION_MY_PACKAGE_REPLACED &&
            intent.action != Intent.ACTION_LOCKED_BOOT_COMPLETED
        ) return

        try {
            val prefs = context.getSharedPreferences(BackendService.PREFS_NAME, 0)
            val autoStart = prefs.getBoolean("auto_start", true)
            if (!autoStart) {
                Log.i(TAG, "Auto-start disabled, skip boot launch")
                return
            }

            if (BackendService.getStatus() == BackendStatus.RUNNING ||
                BackendService.getStatus() == BackendStatus.STARTING
            ) {
                Log.i(TAG, "Backend already running, skip boot launch")
                return
            }

            val useLocalLinux = prefs.getBoolean("use_local_linux", true)
            val host = prefs.getString("host", "localhost") ?: "localhost"
            val port = prefs.getInt("port", 8000)

            Log.i(TAG, "Boot received, starting backend: $host:$port, local=$useLocalLinux")
            BackendService.start(context, host, port, useLocalLinux)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start backend on boot", e)
        }
    }

    companion object {
        const val TAG = "BootReceiver"
    }
}
