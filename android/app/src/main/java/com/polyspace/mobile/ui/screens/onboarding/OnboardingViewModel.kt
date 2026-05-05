package com.polyspace.mobile.ui.screens.onboarding

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

data class PersonaPreset(
    val id: String,
    val name: String,
    val description: String,
    val systemPrompt: String,
    val isDefault: Boolean = false
)

class OnboardingViewModel(application: Application) : AndroidViewModel(application) {
    private val prefs = application.getSharedPreferences("polyspace_onboarding", 0)
    private val backendPrefs = application.getSharedPreferences("polyspace_backend", 0)

    val isOnboardingCompleted: Boolean
        get() = prefs.getBoolean("completed", false)

    private val _currentPage = MutableStateFlow(0)
    val currentPage: StateFlow<Int> = _currentPage

    private val _selectedTheme = MutableStateFlow(prefs.getString("theme", "auto") ?: "auto")
    val selectedTheme: StateFlow<String> = _selectedTheme

    private val _selectedLanguage = MutableStateFlow(prefs.getString("language", "zh-CN") ?: "zh-CN")
    val selectedLanguage: StateFlow<String> = _selectedLanguage

    private val _autoStartEnabled = MutableStateFlow(prefs.getBoolean("auto_start", false))
    val autoStartEnabled: StateFlow<Boolean> = _autoStartEnabled

    private val _autoConfigProgress = MutableStateFlow(0f)
    val autoConfigProgress: StateFlow<Float> = _autoConfigProgress

    private val _autoConfigText = MutableStateFlow("")
    val autoConfigText: StateFlow<String> = _autoConfigText

    private val _autoConfigComplete = MutableStateFlow(false)
    val autoConfigComplete: StateFlow<Boolean> = _autoConfigComplete

    private val _tierProviders = MutableStateFlow<Map<String, String>>(emptyMap())
    val tierProviders: StateFlow<Map<String, String>> = _tierProviders

    private val _providerApiKeys = MutableStateFlow<Map<String, String>>(emptyMap())
    val providerApiKeys: StateFlow<Map<String, String>> = _providerApiKeys

    private val _providerModelIds = MutableStateFlow<Map<String, String>>(emptyMap())
    val providerModelIds: StateFlow<Map<String, String>> = _providerModelIds

    private val _providerApiBases = MutableStateFlow<Map<String, String>>(emptyMap())
    val providerApiBases: StateFlow<Map<String, String>> = _providerApiBases

    fun setCurrentPage(page: Int) {
        _currentPage.value = page
    }

    fun updateTierProvider(tier: String, provider: String) {
        _tierProviders.value = _tierProviders.value.toMutableMap().apply { this[tier] = provider }
    }

    fun updateTierModelId(tier: String, modelId: String) {
        _providerModelIds.value = _providerModelIds.value.toMutableMap().apply { this["tier_$tier"] = modelId }
    }

    fun updateTierApiKey(tier: String, apiKey: String) {
        _providerApiKeys.value = _providerApiKeys.value.toMutableMap().apply { this["tier_$tier"] = apiKey }
    }

    fun updateTierApiBase(tier: String, apiBase: String) {
        _providerApiBases.value = _providerApiBases.value.toMutableMap().apply { this["tier_$tier"] = apiBase }
    }

    fun isBaseModelConfigured(): Boolean {
        val provider = _tierProviders.value["base"] ?: ""
        val modelId = _providerModelIds.value["tier_base"] ?: ""
        return provider.isNotBlank() && modelId.isNotBlank()
    }

    fun selectTheme(theme: String) {
        _selectedTheme.value = theme
        prefs.edit().putString("theme", theme).apply()
    }

    fun selectLanguage(language: String) {
        _selectedLanguage.value = language
        prefs.edit().putString("language", language).apply()
    }

    fun setAutoStart(enabled: Boolean) {
        _autoStartEnabled.value = enabled
        prefs.edit().putBoolean("auto_start", enabled).apply()
    }

    fun startAutoConfig() {
        _autoConfigProgress.value = 0f
        _autoConfigComplete.value = false
    }

    fun updateAutoConfig(progress: Float, text: String) {
        _autoConfigProgress.value = progress
        _autoConfigText.value = text
    }

    fun completeAutoConfig() {
        _autoConfigProgress.value = 1f
        _autoConfigComplete.value = true
    }

    fun completeOnboarding() {
        prefs.edit().putString("theme", _selectedTheme.value).apply()
        prefs.edit().putString("language", _selectedLanguage.value).apply()
        prefs.edit().putBoolean("auto_start", _autoStartEnabled.value).apply()
        prefs.edit().putBoolean("completed", true).apply()

        val tiers = listOf("base", "strong", "performance", "cost_effective", "vertical_multimodal")
        val envMap = mapOf(
            "base" to "POLYSPACE_LLM_BASE_MODEL",
            "strong" to "POLYSPACE_LLM_STRONG_MODEL",
            "performance" to "POLYSPACE_LLM_PERFORMANCE_MODEL",
            "cost_effective" to "POLYSPACE_LLM_COST_EFFECTIVE_MODEL",
            "vertical_multimodal" to "POLYSPACE_LLM_MULTIMODAL_MODEL",
        )
        backendPrefs.edit().apply {
            tiers.forEach { tier ->
                val provider = _tierProviders.value[tier] ?: ""
                val modelId = _providerModelIds.value["tier_$tier"] ?: ""
                val apiKey = _providerApiKeys.value["tier_$tier"] ?: ""
                val apiBase = _providerApiBases.value["tier_$tier"] ?: ""
                if (provider.isNotBlank() && modelId.isNotBlank()) {
                    val envKey = envMap[tier] ?: return@forEach
                    val modelStr = if (apiBase.isNotBlank()) "$provider/$modelId|$apiBase" else "$provider/$modelId"
                    putString(envKey, modelStr)
                    putString("${envKey}_KEY", apiKey)
                }
            }
        }.apply()
    }

    companion object {
        const val PREFS_NAME = "polyspace_onboarding"
        const val TOTAL_PAGES = 6

        fun isCompleted(context: android.content.Context): Boolean {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            return prefs.getBoolean("completed", false)
        }

        fun getSelectedTheme(context: android.content.Context): String {
            val prefs = context.getSharedPreferences(PREFS_NAME, 0)
            return prefs.getString("theme", "auto") ?: "auto"
        }
    }
}
