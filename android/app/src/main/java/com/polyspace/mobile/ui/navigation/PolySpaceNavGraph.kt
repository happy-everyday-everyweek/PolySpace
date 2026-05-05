package com.polyspace.mobile.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.polyspace.mobile.ui.screens.config.BackendConfigScreen
import com.polyspace.mobile.ui.screens.config.FullSettingsScreen
import com.polyspace.mobile.ui.screens.config.MessageListenerConfigScreen
import com.polyspace.mobile.ui.screens.config.SettingsManager
import com.polyspace.mobile.ui.screens.home.HomeScreen
import com.polyspace.mobile.ui.screens.onboarding.OnboardingScreen
import com.polyspace.mobile.ui.screens.webview.WebViewScreen

object Routes {
    const val ONBOARDING = "onboarding"
    const val HOME = "home"
    const val CONFIG = "config"
    const val MESSAGE_LISTENER_CONFIG = "message_listener_config"
    const val FULL_SETTINGS = "settings/{category}"
    const val WEBVIEW = "webview/{host}/{port}"

    fun webViewRoute(host: String, port: Int): String {
        return "webview/$host/$port"
    }

    fun settingsRoute(category: String): String {
        return "settings/$category"
    }
}

@Composable
fun PolySpaceNavGraph(
    startDestination: String = Routes.HOME
) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Routes.ONBOARDING) {
            OnboardingScreen(
                onComplete = {
                    navController.navigate(Routes.HOME) {
                        popUpTo(Routes.ONBOARDING) { inclusive = true }
                    }
                }
            )
        }
        composable(Routes.HOME) {
            HomeScreen(
                onNavigateToConfig = { navController.navigate(Routes.CONFIG) },
                onNavigateToWebView = { host, port ->
                    navController.navigate(Routes.webViewRoute(host, port))
                }
            )
        }
        composable(Routes.CONFIG) {
            BackendConfigScreen(
                onBack = { navController.popBackStack() },
                onNavigateToMessageConfig = { navController.navigate(Routes.MESSAGE_LISTENER_CONFIG) },
                onNavigateToFullSettings = { category ->
                    navController.navigate(Routes.settingsRoute(category))
                }
            )
        }
        composable(Routes.MESSAGE_LISTENER_CONFIG) {
            MessageListenerConfigScreen(
                onBack = { navController.popBackStack() }
            )
        }
        composable(
            route = Routes.FULL_SETTINGS,
            arguments = listOf(
                navArgument("category") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val categoryName = backStackEntry.arguments?.getString("category") ?: "GENERAL"
            val category = try {
                SettingsManager.SettingCategory.valueOf(categoryName)
            } catch (e: Exception) {
                SettingsManager.SettingCategory.GENERAL
            }
            FullSettingsScreen(
                category = category,
                onBack = { navController.popBackStack() }
            )
        }
        composable(
            route = Routes.WEBVIEW,
            arguments = listOf(
                navArgument("host") { type = NavType.StringType },
                navArgument("port") { type = NavType.IntType }
            )
        ) { backStackEntry ->
            val host = backStackEntry.arguments?.getString("host") ?: "localhost"
            val port = backStackEntry.arguments?.getInt("port") ?: 8000
            WebViewScreen(
                host = host,
                port = port,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
