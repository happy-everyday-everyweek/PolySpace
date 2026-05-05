package com.polyspace.mobile.ui.screens.config

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.polyspace.mobile.service.BackendService
import com.polyspace.mobile.service.BackendStatus
import com.polyspace.mobile.service.StartupPhase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class BackendConfigViewModel(application: Application) : AndroidViewModel(application) {
    private val prefs = application.getSharedPreferences("polyspace_backend", 0)

    private val _host = MutableStateFlow(prefs.getString("host", "localhost") ?: "localhost")
    val host: StateFlow<String> = _host

    private val _port = MutableStateFlow(prefs.getInt("port", 8000))
    val port: StateFlow<Int> = _port

    private val _backendStatus = MutableStateFlow(BackendService.getStatus())
    val backendStatus: StateFlow<BackendStatus> = _backendStatus

    private val _startupPhase = MutableStateFlow(BackendService.getStartupPhase())
    val startupPhase: StateFlow<StartupPhase> = _startupPhase

    private val _startupProgress = MutableStateFlow(BackendService.getStartupProgress())
    val startupProgress: StateFlow<Float> = _startupProgress

    private val _autoStart = MutableStateFlow(prefs.getBoolean("auto_start", true))
    val autoStart: StateFlow<Boolean> = _autoStart

    init {
        viewModelScope.launch {
            while (true) {
                kotlinx.coroutines.delay(500)
                _backendStatus.value = BackendService.getStatus()
                _startupPhase.value = BackendService.getStartupPhase()
                _startupProgress.value = BackendService.getStartupProgress()
            }
        }
    }

    fun updateAutoStart(value: Boolean) {
        _autoStart.value = value
        prefs.edit().putBoolean("auto_start", value).apply()
    }

    fun startBackend() {
        val app = getApplication<Application>()
        val useLocalLinux = prefs.getBoolean("use_local_linux", true)
        BackendService.start(app, _host.value, _port.value, useLocalLinux)
    }

    fun stopBackend() {
        val app = getApplication<Application>()
        BackendService.stop(app)
    }
}
