package com.polyspace.mobile.tool

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.util.Log
import com.polyspace.mobile.service.ScreenRecordService
import org.json.JSONObject

class ScreenRecordTool : NativeTool {
    override val name = "screen_record"
    override val displayName = "屏幕录制"
    override val description = "录制屏幕视频并保存为MP4文件"
    override val category = "media"
    override val requiredPermissions = listOf(
        "android.permission.FOREGROUND_SERVICE",
        "android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION",
        "android.permission.RECORD_AUDIO"
    )

    private var pendingResultCode: Int = -1
    private var pendingData: Intent? = null

    companion object {
        private const val TAG = "ScreenRecordTool"
        const val REQUEST_CODE_SCREEN_CAPTURE = 9999
    }

    fun requestScreenCapture(activity: Activity) {
        val projectionManager = activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val intent = projectionManager.createScreenCaptureIntent()
        activity.startActivityForResult(intent, REQUEST_CODE_SCREEN_CAPTURE)
    }

    fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode == REQUEST_CODE_SCREEN_CAPTURE) {
            pendingResultCode = resultCode
            pendingData = data
        }
    }

    fun hasPendingAuthorization(): Boolean = pendingResultCode != -1 && pendingData != null

    fun clearPendingAuthorization() {
        pendingResultCode = -1
        pendingData = null
    }

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "status")
        return when (action) {
            "start" -> startRecording(context, params)
            "stop" -> stopRecording(context)
            "pause" -> pauseRecording(context)
            "resume" -> resumeRecording(context)
            "status" -> getStatus()
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }

    private fun startRecording(context: Context, params: JSONObject): ToolResult {
        if (ScreenRecordService.isRecording) {
            return ToolResult(false, error = "Already recording")
        }

        if (pendingResultCode == -1 || pendingData == null) {
            return ToolResult(false, error = "Screen capture authorization required. Call requestScreenCapture() first.")
        }

        val includeAudio = params.optBoolean("include_audio", true)
        val quality = params.optString("quality", "high")

        try {
            ScreenRecordService.startRecording(
                context,
                pendingResultCode,
                pendingData!!,
                includeAudio,
                quality
            )
            clearPendingAuthorization()
            return ToolResult(true, JSONObject().apply {
                put("recording", true)
                put("message", "Screen recording started")
            })
        } catch (e: Exception) {
            Log.e(TAG, "Failed to start screen recording", e)
            return ToolResult(false, error = e.message ?: "Start failed")
        }
    }

    private fun stopRecording(context: Context): ToolResult {
        if (!ScreenRecordService.isRecording) {
            return ToolResult(false, error = "Not recording")
        }

        try {
            ScreenRecordService.stopRecording(context)
            return ToolResult(true, JSONObject().apply {
                put("recording", false)
                put("file_path", ScreenRecordService.currentFilePath ?: "")
                put("duration", ScreenRecordService.recordingDuration)
            })
        } catch (e: Exception) {
            Log.e(TAG, "Failed to stop screen recording", e)
            return ToolResult(false, error = e.message ?: "Stop failed")
        }
    }

    private fun pauseRecording(context: Context): ToolResult {
        if (!ScreenRecordService.isRecording || ScreenRecordService.isPaused) {
            return ToolResult(false, error = "Cannot pause")
        }
        val intent = Intent(context, ScreenRecordService::class.java).apply {
            action = ScreenRecordService.ACTION_PAUSE
        }
        context.startService(intent)
        return ToolResult(true, JSONObject().apply {
            put("recording", true)
            put("paused", true)
        })
    }

    private fun resumeRecording(context: Context): ToolResult {
        if (!ScreenRecordService.isRecording || !ScreenRecordService.isPaused) {
            return ToolResult(false, error = "Cannot resume")
        }
        val intent = Intent(context, ScreenRecordService::class.java).apply {
            action = ScreenRecordService.ACTION_RESUME
        }
        context.startService(intent)
        return ToolResult(true, JSONObject().apply {
            put("recording", true)
            put("paused", false)
        })
    }

    private fun getStatus(): ToolResult {
        return ToolResult(true, JSONObject().apply {
            put("recording", ScreenRecordService.isRecording)
            put("paused", ScreenRecordService.isPaused)
            put("file_path", ScreenRecordService.currentFilePath ?: "")
            put("duration", ScreenRecordService.recordingDuration)
        })
    }
}
