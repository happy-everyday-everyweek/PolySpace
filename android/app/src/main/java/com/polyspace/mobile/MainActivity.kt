package com.polyspace.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.polyspace.mobile.ui.navigation.PolySpaceNavGraph
import com.polyspace.mobile.ui.navigation.Routes
import com.polyspace.mobile.ui.screens.onboarding.OnboardingViewModel
import com.polyspace.mobile.ui.theme.PolySpaceTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val onboardingCompleted = OnboardingViewModel.isCompleted(this)
        val selectedTheme = OnboardingViewModel.getSelectedTheme(this)
        val startDestination = if (onboardingCompleted) Routes.HOME else Routes.ONBOARDING

        setContent {
            PolySpaceTheme(themeMode = selectedTheme) {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    PolySpaceNavGraph(startDestination = startDestination)
                }
            }
        }
    }
}
