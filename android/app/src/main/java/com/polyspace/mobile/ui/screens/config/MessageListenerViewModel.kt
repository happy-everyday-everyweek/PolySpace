package com.polyspace.mobile.ui.screens.config

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import com.polyspace.mobile.service.MessageListenerService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class MessageListenerViewModel(application: Application) : AndroidViewModel(application) {

    private val _enabledApps = MutableStateFlow<Set<String>>(emptySet())
    val enabledApps: StateFlow<Set<String>> = _enabledApps

    private val _customApps = MutableStateFlow<Map<String, String>>(emptyMap())
    val customApps: StateFlow<Map<String, String>> = _customApps

    private val _newPackageName = MutableStateFlow("")
    val newPackageName: StateFlow<String> = _newPackageName

    private val _newAppName = MutableStateFlow("")
    val newAppName: StateFlow<String> = _newAppName

    init {
        loadConfig()
    }

    private fun loadConfig() {
        val context = getApplication<Application>()
        val monitored = MessageListenerService.getMonitoredApps(context)
        _enabledApps.value = monitored.keys

        val custom = MessageListenerService.getCustomApps(context)
        _customApps.value = custom
    }

    fun toggleApp(packageName: String, enabled: Boolean) {
        val current = _enabledApps.value.toMutableSet()
        if (enabled) {
            current.add(packageName)
        } else {
            current.remove(packageName)
        }
        _enabledApps.value = current
        MessageListenerService.setMonitoredApps(getApplication(), current)
    }

    fun updateNewPackageName(value: String) {
        _newPackageName.value = value
    }

    fun updateNewAppName(value: String) {
        _newAppName.value = value
    }

    fun addCustomApp(): Boolean {
        val pkg = _newPackageName.value.trim()
        val name = _newAppName.value.trim()
        if (pkg.isEmpty() || name.isEmpty()) return false

        MessageListenerService.addCustomApp(getApplication(), pkg, name)

        val current = _enabledApps.value.toMutableSet()
        current.add(pkg)
        _enabledApps.value = current
        MessageListenerService.setMonitoredApps(getApplication(), current)

        _customApps.value = MessageListenerService.getCustomApps(getApplication())
        _newPackageName.value = ""
        _newAppName.value = ""
        return true
    }

    fun removeCustomApp(packageName: String) {
        MessageListenerService.removeCustomApp(getApplication(), packageName)

        val current = _enabledApps.value.toMutableSet()
        current.remove(packageName)
        _enabledApps.value = current
        MessageListenerService.setMonitoredApps(getApplication(), current)

        _customApps.value = MessageListenerService.getCustomApps(getApplication())
    }
}
