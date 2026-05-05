package com.polyspace.mobile.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import com.polyspace.mobile.MainActivity
import com.polyspace.mobile.linux.LinuxManager
import com.polyspace.mobile.R
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.net.HttpURLConnection
import java.net.URL

enum class BackendStatus {
    STOPPED,
    STARTING,
    RUNNING,
    ERROR
}

enum class StartupPhase(val label: String, val progress: Float) {
    IDLE("", 0f),
    EXTRACTING_ROOTFS("正在解压系统环境...", 0.1f),
    EXTRACTING_ROOTFS_PROGRESS("正在解压系统环境...", 0.5f),
    STARTING_PROOT("正在启动Linux环境...", 0.7f),
    INSTALLING_PACKAGES("正在安装依赖包...", 0.8f),
    WAITING_BACKEND("正在等待后端就绪...", 0.9f),
    READY("", 1.0f),
    FAILED("启动失败", 0f)
}

class BackendService : Service() {

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var healthCheckJob: Job? = null
    private var currentHost: String = "localhost"
    private var currentPort: Int = 8000
    private var consecutiveErrors: Int = 0

    companion object {
        private const val CHANNEL_ID = "polyspace_backend"
        private const val NOTIFICATION_ID = 1001
        private const val HEALTH_CHECK_INTERVAL_MS = 5000L
        private const val STARTUP_HEALTH_CHECK_INTERVAL_MS = 1000L
        private const val MAX_CONSECUTIVE_ERRORS = 6
        private const val MAX_RESTART_ATTEMPTS = 3
        private const val RESTART_WINDOW_MS = 60_000L
        const val PREFS_NAME = "polyspace_backend"
        private const val KEY_CRASH_COUNT = "service_crash_count"
        private const val KEY_LAST_CRASH_TIME = "service_last_crash_time"

        @Volatile
        private var _status = BackendStatus.STOPPED
        fun getStatus(): BackendStatus = _status

        @Volatile
        private var _startupPhase = StartupPhase.IDLE
        fun getStartupPhase(): StartupPhase = _startupPhase

        @Volatile
        private var _startupProgress = 0f
        fun getStartupProgress(): Float = _startupProgress

        fun getHost(context: Context): String {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            return prefs.getString("host", "localhost") ?: "localhost"
        }

        fun getPort(context: Context): Int {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            return prefs.getInt("port", 8000)
        }

        fun start(
            context: Context,
            host: String,
            port: Int,
            useLocalLinux: Boolean
        ) {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            val crashCount = prefs.getInt(KEY_CRASH_COUNT, 0)
            val lastCrashTime = prefs.getLong(KEY_LAST_CRASH_TIME, 0)
            val now = System.currentTimeMillis()
            if (crashCount >= MAX_RESTART_ATTEMPTS && (now - lastCrashTime) < RESTART_WINDOW_MS) {
                android.util.Log.w("BackendService", "Too many crashes ($crashCount in 60s), skip start")
                _status = BackendStatus.ERROR
                _startupPhase = StartupPhase.FAILED
                return
            }

            _status = BackendStatus.STARTING
            _startupPhase = StartupPhase.IDLE
            _startupProgress = 0f
            val intent = Intent(context, BackendService::class.java).apply {
                putExtra("host", host)
                putExtra("port", port)
                putExtra("use_local_linux", useLocalLinux)
            }
            try {
                context.startForegroundService(intent)
            } catch (e: Exception) {
                android.util.Log.e("BackendService", "Failed to start foreground service", e)
                _status = BackendStatus.ERROR
                _startupPhase = StartupPhase.FAILED
            }
        }

        fun stop(context: Context) {
            val intent = Intent(context, BackendService::class.java)
            context.stopService(intent)
            _status = BackendStatus.STOPPED
            _startupPhase = StartupPhase.IDLE
            _startupProgress = 0f
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            prefs.edit()
                .remove(KEY_CRASH_COUNT)
                .remove(KEY_LAST_CRASH_TIME)
                .apply()
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val prefs = getSharedPreferences(PREFS_NAME, 0)

        if (intent == null) {
            currentHost = prefs.getString("host", "localhost") ?: "localhost"
            currentPort = prefs.getInt("port", 8000)
        } else {
            currentHost = intent.getStringExtra("host") ?: prefs.getString("host", "localhost") ?: "localhost"
            currentPort = intent.getIntExtra("port", prefs.getInt("port", 8000))
        }
        val useLocalLinux = intent?.getBooleanExtra("use_local_linux", prefs.getBoolean("use_local_linux", true))
            ?: prefs.getBoolean("use_local_linux", true)

        val notification = createNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
        try {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } catch (e: Exception) {
            android.util.Log.w("BackendService", "startForeground with type failed, fallback", e)
            startForeground(NOTIFICATION_ID, notification)
        }

        _status = BackendStatus.STARTING
        consecutiveErrors = 0

        serviceScope.launch {
            try {
                if (useLocalLinux) {
                    startLocalLinuxBackend(currentPort)
                } else {
                    _startupPhase = StartupPhase.WAITING_BACKEND
                    _startupProgress = StartupPhase.WAITING_BACKEND.progress
                    updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
                    checkRemoteBackend(currentHost, currentPort)
                }
            } catch (e: Exception) {
                android.util.Log.e("BackendService", "Backend start failed", e)
                _status = BackendStatus.ERROR
                _startupPhase = StartupPhase.FAILED
                _startupProgress = 0f
                updateNotification(currentHost, currentPort, BackendStatus.ERROR, _startupPhase)
            }
        }

        startHealthCheck(currentHost, currentPort)
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onTaskRemoved(rootIntent: Intent?) {
        val prefs = getSharedPreferences(PREFS_NAME, 0)
        val autoStart = prefs.getBoolean("auto_start", true)
        if (autoStart && _status == BackendStatus.RUNNING) {
            try {
                val restartIntent = Intent(this, BackendService::class.java).apply {
                    putExtra("host", prefs.getString("host", "localhost") ?: "localhost")
                    putExtra("port", prefs.getInt("port", 8000))
                    putExtra("use_local_linux", prefs.getBoolean("use_local_linux", true))
                }
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    val pendingIntent = android.app.PendingIntent.getService(
                        this,
                        0,
                        restartIntent,
                        android.app.PendingIntent.FLAG_IMMUTABLE or android.app.PendingIntent.FLAG_UPDATE_CURRENT
                    )
                    val alarmManager = getSystemService(android.content.Context.ALARM_SERVICE) as android.app.AlarmManager
                    alarmManager.set(
                        android.app.AlarmManager.ELAPSED_REALTIME_WAKEUP,
                        android.os.SystemClock.elapsedRealtime() + 1000,
                        pendingIntent
                    )
                } else {
                    startForegroundService(restartIntent)
                }
            } catch (e: Exception) {
                android.util.Log.e("BackendService", "Failed to restart on task removed", e)
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        healthCheckJob?.cancel()
        serviceScope.cancel()
        LinuxManager.stopLinuxBackend()
        _status = BackendStatus.STOPPED
        _startupPhase = StartupPhase.IDLE
        _startupProgress = 0f
    }

    private fun startLocalLinuxBackend(port: Int) {
        LinuxManager.setProgressCallback(object : LinuxManager.ExtractionProgressCallback {
            override fun onProgress(phase: String, progress: Float) {
                when (phase) {
                    "extracting_proot" -> {
                        _startupPhase = StartupPhase.EXTRACTING_ROOTFS
                        _startupProgress = progress
                    }
                    "extracting_rootfs" -> {
                        _startupPhase = StartupPhase.EXTRACTING_ROOTFS_PROGRESS
                        _startupProgress = progress
                    }
                    "extraction_complete" -> {
                        _startupPhase = StartupPhase.STARTING_PROOT
                        _startupProgress = StartupPhase.STARTING_PROOT.progress
                    }
                }
                updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
            }
        })

        if (!LinuxManager.isLinuxAvailable(this)) {
            _startupPhase = StartupPhase.EXTRACTING_ROOTFS
            _startupProgress = StartupPhase.EXTRACTING_ROOTFS.progress
            updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
            val extracted = LinuxManager.extractLinuxDist(this)
            if (!extracted) {
                _status = BackendStatus.ERROR
                _startupPhase = StartupPhase.FAILED
                _startupProgress = 0f
                updateNotification(currentHost, currentPort, BackendStatus.ERROR, _startupPhase)
                LinuxManager.setProgressCallback(null)
                return
            }
        }

        LinuxManager.setProgressCallback(null)

        _startupPhase = StartupPhase.STARTING_PROOT
        _startupProgress = StartupPhase.STARTING_PROOT.progress
        updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)

        val started = LinuxManager.startLinuxBackend(
            context = this,
            port = port,
            onOutput = { line ->
                android.util.Log.d("BackendService", line)
                when {
                    line.contains("POLYSPACE_INSTALL_START") -> {
                        _startupPhase = StartupPhase.INSTALLING_PACKAGES
                        _startupProgress = StartupPhase.INSTALLING_PACKAGES.progress
                        updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
                    }
                    line.contains("POLYSPACE_INSTALL_DONE") -> {
                        _startupPhase = StartupPhase.WAITING_BACKEND
                        _startupProgress = StartupPhase.WAITING_BACKEND.progress
                        updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
                    }
                    line.contains("Uvicorn running on") -> {
                        _status = BackendStatus.RUNNING
                        _startupPhase = StartupPhase.READY
                        _startupProgress = 1.0f
                        updateNotification(currentHost, currentPort, BackendStatus.RUNNING, _startupPhase)
                    }
                }
            },
            onError = { error ->
                android.util.Log.e("BackendService", error)
                if (_status != BackendStatus.STOPPED) {
                    _status = BackendStatus.ERROR
                    _startupPhase = StartupPhase.FAILED
                    _startupProgress = 0f
                    updateNotification(currentHost, currentPort, BackendStatus.ERROR, _startupPhase)
                }
            }
        )
        if (!started) {
            _status = BackendStatus.ERROR
            _startupPhase = StartupPhase.FAILED
            _startupProgress = 0f
            updateNotification(currentHost, currentPort, BackendStatus.ERROR, _startupPhase)
            return
        }

        _startupPhase = StartupPhase.WAITING_BACKEND
        _startupProgress = StartupPhase.WAITING_BACKEND.progress
        updateNotification(currentHost, currentPort, BackendStatus.STARTING, _startupPhase)
    }

    private suspend fun checkRemoteBackend(host: String, port: Int) {
        delay(2000)
        var conn: HttpURLConnection? = null
        try {
            val url = URL("http://$host:$port/health")
            conn = url.openConnection() as HttpURLConnection
            conn.requestMethod = "GET"
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            val responseCode = conn.responseCode
            if (responseCode == 200) {
                _status = BackendStatus.RUNNING
                _startupPhase = StartupPhase.READY
                _startupProgress = 1.0f
                updateNotification(host, port, BackendStatus.RUNNING, _startupPhase)
            } else {
                _status = BackendStatus.ERROR
                _startupPhase = StartupPhase.FAILED
                _startupProgress = 0f
                updateNotification(host, port, BackendStatus.ERROR, _startupPhase)
            }
        } catch (e: Exception) {
            _status = BackendStatus.ERROR
            _startupPhase = StartupPhase.FAILED
            _startupProgress = 0f
            updateNotification(host, port, BackendStatus.ERROR, _startupPhase)
        } finally {
            conn?.disconnect()
        }
    }

    private fun startHealthCheck(host: String, port: Int) {
        healthCheckJob?.cancel()
        healthCheckJob = serviceScope.launch {
            while (true) {
                val interval = if (_status == BackendStatus.STARTING)
                    STARTUP_HEALTH_CHECK_INTERVAL_MS else HEALTH_CHECK_INTERVAL_MS
                delay(interval)
                try {
                    val url = URL("http://$host:$port/health")
                    val conn = url.openConnection() as HttpURLConnection
                    conn.requestMethod = "GET"
                    conn.connectTimeout = 3000
                    conn.readTimeout = 3000
                    val responseCode = conn.responseCode
                    conn.disconnect()

                    if (responseCode == 200) {
                        consecutiveErrors = 0
                        if (_status != BackendStatus.RUNNING) {
                            _status = BackendStatus.RUNNING
                            _startupPhase = StartupPhase.READY
                            _startupProgress = 1.0f
                            updateNotification(host, port, BackendStatus.RUNNING, _startupPhase)
                            val prefs = getSharedPreferences(PREFS_NAME, 0)
                            prefs.edit().remove(KEY_CRASH_COUNT).remove(KEY_LAST_CRASH_TIME).apply()
                        }
                    } else {
                        consecutiveErrors++
                        if (_status == BackendStatus.RUNNING && consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
                            _status = BackendStatus.ERROR
                            _startupPhase = StartupPhase.FAILED
                            _startupProgress = 0f
                            updateNotification(host, port, BackendStatus.ERROR, _startupPhase)
                        }
                    }
                } catch (e: Exception) {
                    if (_status == BackendStatus.STARTING) continue
                    consecutiveErrors++
                    if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
                        _status = BackendStatus.ERROR
                        _startupPhase = StartupPhase.FAILED
                        _startupProgress = 0f
                        updateNotification(host, port, BackendStatus.ERROR, _startupPhase)
                    }
                }
            }
        }
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.notification_channel_backend),
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = getString(R.string.notification_channel_backend_desc)
            setShowBadge(false)
        }
        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }

    private fun createNotification(host: String, port: Int, status: BackendStatus, phase: StartupPhase = StartupPhase.IDLE): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val statusText = when (status) {
            BackendStatus.RUNNING -> getString(R.string.config_status_running)
            BackendStatus.STARTING -> phase.label.ifEmpty { getString(R.string.config_status_starting) }
            BackendStatus.ERROR -> getString(R.string.config_status_error)
            BackendStatus.STOPPED -> getString(R.string.config_status_stopped)
        }

        val icon = when (status) {
            BackendStatus.RUNNING -> R.drawable.ic_status_running
            BackendStatus.STARTING -> R.drawable.ic_status_starting
            BackendStatus.ERROR -> R.drawable.ic_status_error
            BackendStatus.STOPPED -> R.drawable.ic_status_stopped
        }

        return Notification.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText("$statusText $host:$port")
            .setSmallIcon(icon)
            .setContentIntent(pendingIntent)
            .setOngoing(status == BackendStatus.RUNNING || status == BackendStatus.STARTING)
            .build()
    }

    private fun updateNotification(host: String, port: Int, status: BackendStatus, phase: StartupPhase = StartupPhase.IDLE) {
        try {
            val notification = createNotification(host, port, status, phase)
            val manager = getSystemService(NotificationManager::class.java)
            manager.notify(NOTIFICATION_ID, notification)
        } catch (e: Exception) {
            android.util.Log.e("BackendService", "Failed to update notification", e)
        }
    }
}
