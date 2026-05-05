package com.polyspace.mobile.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaFormat
import android.media.MediaMuxer
import android.media.MediaRecorder
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ScreenRecordService : Service() {

    companion object {
        private const val TAG = "ScreenRecordService"
        private const val CHANNEL_ID = "screen_record_channel"
        private const val NOTIFICATION_ID = 2001
        const val ACTION_START = "com.polyspace.mobile.ACTION_START_RECORD"
        const val ACTION_STOP = "com.polyspace.mobile.ACTION_STOP_RECORD"
        const val ACTION_PAUSE = "com.polyspace.mobile.ACTION_PAUSE_RECORD"
        const val ACTION_RESUME = "com.polyspace.mobile.ACTION_RESUME_RECORD"
        const val EXTRA_RESULT_CODE = "result_code"
        const val EXTRA_RESULT_DATA = "result_data"
        const val EXTRA_INCLUDE_AUDIO = "include_audio"
        const val EXTRA_QUALITY = "quality"

        var isRecording = false
            private set
        var isPaused = false
            private set
        var currentFilePath: String? = null
            private set
        var recordingDuration: Long = 0
            private set

        private var listener: RecordingStateListener? = null

        fun setListener(l: RecordingStateListener?) {
            listener = l
        }

        fun startRecording(
            context: Context,
            resultCode: Int,
            data: Intent,
            includeAudio: Boolean = true,
            quality: String = "high"
        ) {
            val intent = Intent(context, ScreenRecordService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_RESULT_CODE, resultCode)
                putExtra(EXTRA_RESULT_DATA, data)
                putExtra(EXTRA_INCLUDE_AUDIO, includeAudio)
                putExtra(EXTRA_QUALITY, quality)
            }
            context.startForegroundService(intent)
        }

        fun stopRecording(context: Context) {
            val intent = Intent(context, ScreenRecordService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }
    }

    interface RecordingStateListener {
        fun onRecordingStarted(filePath: String)
        fun onRecordingStopped(filePath: String, duration: Long)
        fun onRecordingPaused()
        fun onRecordingResumed()
        fun onRecordingError(error: String)
    }

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var mediaRecorder: MediaRecorder? = null
    private var audioRecorder: MediaRecorder? = null
    private var startTime: Long = 0
    private var pauseTime: Long = 0
    private var totalPausedTime: Long = 0
    private var handler: Handler? = null
    private var timerRunnable: Runnable? = null

    override fun onCreate() {
        super.onCreate()
        handler = Handler(Looper.getMainLooper())
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                val resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, -1)
                val data: Intent? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra(EXTRA_RESULT_DATA)
                }
                val includeAudio = intent.getBooleanExtra(EXTRA_INCLUDE_AUDIO, true)
                val quality = intent.getStringExtra(EXTRA_QUALITY) ?: "high"

                if (data != null && resultCode != -1) {
                    try {
                        startForeground(NOTIFICATION_ID, createNotification("Recording screen..."),
                            ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
                    } catch (e: Exception) {
                        Log.w(TAG, "startForeground with mediaProjection type failed, fallback", e)
                        startForeground(NOTIFICATION_ID, createNotification("Recording screen..."))
                    }
                    startScreenRecord(resultCode, data, includeAudio, quality)
                } else {
                    stopSelf()
                }
            }
            ACTION_STOP -> stopScreenRecord()
            ACTION_PAUSE -> pauseScreenRecord()
            ACTION_RESUME -> resumeScreenRecord()
        }
        return START_NOT_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            "Screen Recording",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Screen recording in progress"
            setShowBadge(false)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    private fun createNotification(text: String): Notification {
        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle("PolySpace")
            .setContentText(text)
            .setSmallIcon(android.R.drawable.ic_media_play)
            .build()
    }

    private fun startScreenRecord(resultCode: Int, data: Intent, includeAudio: Boolean, quality: String) {
        try {
            val projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            mediaProjection = projectionManager.getMediaProjection(resultCode, data)

            if (mediaProjection == null) {
                listener?.onRecordingError("Failed to get MediaProjection")
                stopSelf()
                return
            }

            val outputDir = File(getExternalFilesDir(null), "recordings")
            if (!outputDir.exists()) outputDir.mkdirs()

            val dateFormat = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault())
            val fileName = "REC_${dateFormat.format(Date())}.mp4"
            val outputFile = File(outputDir, fileName)
            currentFilePath = outputFile.absolutePath

            val (width, height, fps, bitrate) = getQualityParams(quality)

            mediaRecorder = MediaRecorder(this).apply {
                if (includeAudio) {
                    setAudioSource(MediaRecorder.AudioSource.MIC)
                }
                setVideoSource(MediaRecorder.VideoSource.SURFACE)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setOutputFile(outputFile.absolutePath)
                setVideoEncoder(MediaRecorder.VideoEncoder.H264)
                if (includeAudio) {
                    setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
                    setAudioEncodingBitRate(128000)
                    setAudioSamplingRate(44100)
                }
                setVideoSize(width, height)
                setVideoFrameRate(fps)
                setVideoEncodingBitRate(bitrate)
                prepare()
            }

            virtualDisplay = mediaProjection?.createVirtualDisplay(
                "PolySpaceScreenRecord",
                width, height, resources.displayMetrics.densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                mediaRecorder?.surface,
                null, null
            )

            mediaRecorder?.start()
            isRecording = true
            isPaused = false
            startTime = System.currentTimeMillis()
            totalPausedTime = 0

            startTimer()
            listener?.onRecordingStarted(outputFile.absolutePath)

            updateNotification("Recording screen... ${formatDuration(0)}")

        } catch (e: Exception) {
            Log.e(TAG, "Failed to start screen recording", e)
            listener?.onRecordingError(e.message ?: "Unknown error")
            cleanup()
            stopSelf()
        }
    }

    private fun stopScreenRecord() {
        try {
            mediaRecorder?.apply {
                stop()
                release()
            }
            mediaRecorder = null

            virtualDisplay?.release()
            virtualDisplay = null

            mediaProjection?.stop()
            mediaProjection = null

            stopTimer()

            val duration = if (startTime > 0) {
                (System.currentTimeMillis() - startTime - totalPausedTime) / 1000
            } else 0
            recordingDuration = duration

            isRecording = false
            isPaused = false

            val filePath = currentFilePath
            if (filePath != null) {
                listener?.onRecordingStopped(filePath, duration)
            }

        } catch (e: Exception) {
            Log.e(TAG, "Error stopping recording", e)
            listener?.onRecordingError(e.message ?: "Stop error")
        } finally {
            cleanup()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
    }

    private fun pauseScreenRecord() {
        if (!isRecording || isPaused) return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                mediaRecorder?.pause()
                isPaused = true
                pauseTime = System.currentTimeMillis()
                listener?.onRecordingPaused()
                updateNotification("Recording paused")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to pause recording", e)
        }
    }

    private fun resumeScreenRecord() {
        if (!isRecording || !isPaused) return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                mediaRecorder?.resume()
                isPaused = false
                totalPausedTime += System.currentTimeMillis() - pauseTime
                listener?.onRecordingResumed()
                updateNotification("Recording screen...")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to resume recording", e)
        }
    }

    private fun getQualityParams(quality: String): QualityParams {
        val displayMetrics = resources.displayMetrics
        val screenWidth = displayMetrics.widthPixels and 0xFFFE
        val screenHeight = displayMetrics.heightPixels and 0xFFFE

        return when (quality) {
            "low" -> QualityParams(
                width = minOf(1280, screenWidth) and 0xFFFE,
                height = minOf(720, screenHeight) and 0xFFFE,
                fps = 15,
                bitrate = 1_000_000
            )
            "medium" -> QualityParams(
                width = minOf(1920, screenWidth) and 0xFFFE,
                height = minOf(1080, screenHeight) and 0xFFFE,
                fps = 24,
                bitrate = 2_500_000
            )
            "original" -> QualityParams(
                width = screenWidth,
                height = screenHeight,
                fps = 60,
                bitrate = 8_000_000
            )
            else -> QualityParams(
                width = minOf(1920, screenWidth) and 0xFFFE,
                height = minOf(1080, screenHeight) and 0xFFFE,
                fps = 30,
                bitrate = 5_000_000
            )
        }
    }

    private data class QualityParams(
        val width: Int,
        val height: Int,
        val fps: Int,
        val bitrate: Int
    )

    private fun startTimer() {
        timerRunnable = object : Runnable {
            override fun run() {
                if (isRecording && !isPaused) {
                    val elapsed = (System.currentTimeMillis() - startTime - totalPausedTime) / 1000
                    recordingDuration = elapsed
                    updateNotification("Recording screen... ${formatDuration(elapsed)}")
                }
                handler?.postDelayed(this, 1000)
            }
        }
        handler?.post(timerRunnable!!)
    }

    private fun stopTimer() {
        timerRunnable?.let { handler?.removeCallbacks(it) }
        timerRunnable = null
    }

    private fun updateNotification(text: String) {
        val manager = getSystemService(NotificationManager::class.java)
        manager.notify(NOTIFICATION_ID, createNotification(text))
    }

    private fun formatDuration(seconds: Long): String {
        val h = seconds / 3600
        val m = (seconds % 3600) / 60
        val s = seconds % 60
        return if (h > 0) {
            String.format(Locale.getDefault(), "%d:%02d:%02d", h, m, s)
        } else {
            String.format(Locale.getDefault(), "%02d:%02d", m, s)
        }
    }

    private fun cleanup() {
        try {
            mediaRecorder?.release()
        } catch (_: Exception) {}
        try {
            virtualDisplay?.release()
        } catch (_: Exception) {}
        try {
            mediaProjection?.stop()
        } catch (_: Exception) {}
        mediaRecorder = null
        virtualDisplay = null
        mediaProjection = null
    }

    override fun onDestroy() {
        stopTimer()
        if (isRecording) {
            stopScreenRecord()
        }
        cleanup()
        super.onDestroy()
    }
}
