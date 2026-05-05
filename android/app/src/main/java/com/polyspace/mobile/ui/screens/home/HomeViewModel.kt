package com.polyspace.mobile.ui.screens.home

import android.content.Context
import android.provider.Settings
import android.text.TextUtils
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.polyspace.mobile.accessibility.AccessibilityBridge
import com.polyspace.mobile.service.BackendStatus
import com.polyspace.mobile.service.BackendService
import com.polyspace.mobile.service.StartupPhase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class HomeViewModel : ViewModel() {
    private val _backendStatus = MutableStateFlow(BackendStatus.STOPPED)
    val backendStatus: StateFlow<BackendStatus> = _backendStatus

    private val _startupPhase = MutableStateFlow(StartupPhase.IDLE)
    val startupPhase: StateFlow<StartupPhase> = _startupPhase

    private val _startupProgress = MutableStateFlow(0f)
    val startupProgress: StateFlow<Float> = _startupProgress

    private val _backendHost = MutableStateFlow("localhost")
    val backendHost: StateFlow<String> = _backendHost

    private val _backendPort = MutableStateFlow(8000)
    val backendPort: StateFlow<Int> = _backendPort

    private val _accessibilityEnabled = MutableStateFlow(false)
    val accessibilityEnabled: StateFlow<Boolean> = _accessibilityEnabled

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

    fun refreshStatus(context: Context) {
        _backendStatus.value = BackendService.getStatus()
        _startupPhase.value = BackendService.getStartupPhase()
        _startupProgress.value = BackendService.getStartupProgress()
        _backendHost.value = BackendService.getHost(context)
        _backendPort.value = BackendService.getPort(context)
        _accessibilityEnabled.value = isAccessibilityEnabled(context)
    }

    private fun isAccessibilityEnabled(context: Context): Boolean {
        val expected = "com.polyspace.mobile/com.polyspace.mobile.service.PolySpaceAccessibilityService"
        val enabledServices = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false
        val colonSplitter = TextUtils.SimpleStringSplitter(':')
        colonSplitter.setString(enabledServices)
        while (colonSplitter.hasNext()) {
            if (colonSplitter.next().equals(expected, ignoreCase = true)) {
                return true
            }
        }
        return AccessibilityBridge.isServiceRunning()
    }
}
