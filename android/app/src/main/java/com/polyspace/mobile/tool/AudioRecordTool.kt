package com.polyspace.mobile.tool

import android.content.Context
import android.media.MediaRecorder
import android.os.Build
import android.util.Log
import org.json.JSONObject
import java.io.File

class AudioRecordTool : NativeTool {
    override val name = "audio_record"
    override val displayName = "录音"
    override val description = "录制音频并保存为文件"
    override val category = "media"
    override val requiredPermissions = listOf("android.permission.RECORD_AUDIO")

    private var recorder: MediaRecorder? = null
    private var isRecording = false
    private var currentFilePath: String = ""

    fun startRecording(context: Context, outputPath: String? = null): Boolean {
        if (isRecording) return false
        try {
            val path = outputPath ?: File(context.cacheDir, "recording_${System.currentTimeMillis()}.m4a").absolutePath
            currentFilePath = path
            recorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                MediaRecorder(context)
            } else {
                @Suppress("DEPRECATION")
                MediaRecorder()
            }.apply {
                setAudioSource(MediaRecorder.AudioSource.MIC)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                setAudioSamplingRate(44100)
                setAudioEncodingBitRate(128000)
                setOutputFile(path)
                prepare()
                start()
            }
            isRecording = true
            return true
        } catch (e: Exception) {
            Log.e("AudioRecordTool", "Start recording failed", e)
            return false
        }
    }

    fun stopRecording(): String {
        if (!isRecording) return ""
        try {
            recorder?.apply {
                stop()
                release()
            }
        } catch (e: Exception) {
            Log.e("AudioRecordTool", "Stop recording failed", e)
        }
        recorder = null
        isRecording = false
        return currentFilePath
    }

    fun isCurrentlyRecording(): Boolean = isRecording

    override suspend fun execute(context: Context, params: JSONObject): ToolResult {
        val action = params.optString("action", "start")
        return when (action) {
            "start" -> {
                val path = params.optString("output_path", "")
                val success = startRecording(context, path.ifEmpty { null })
                ToolResult(success, JSONObject().apply {
                    put("recording", true)
                    put("file_path", currentFilePath)
                })
            }
            "stop" -> {
                val path = stopRecording()
                ToolResult(true, JSONObject().apply {
                    put("recording", false)
                    put("file_path", path)
                })
            }
            "status" -> {
                ToolResult(true, JSONObject().apply {
                    put("recording", isRecording)
                    put("file_path", currentFilePath)
                })
            }
            else -> ToolResult(false, error = "Unknown action: $action")
        }
    }
}
