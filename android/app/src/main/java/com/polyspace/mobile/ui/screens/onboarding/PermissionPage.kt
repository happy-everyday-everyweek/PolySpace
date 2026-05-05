package com.polyspace.mobile.ui.screens.onboarding

import android.Manifest
import android.content.ComponentName
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.polyspace.mobile.R
import com.polyspace.mobile.service.CalendarSyncService
import com.polyspace.mobile.service.MessageBridge

@Composable
fun PermissionPage() {
    val context = LocalContext.current
    var calendarGranted by remember { mutableStateOf(CalendarSyncService.hasCalendarPermission(context)) }
    var notificationGranted by remember {
        mutableStateOf(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED
            } else true
        )
    }
    var messageListenerGranted by remember { mutableStateOf(MessageBridge.isNotificationListenerEnabled(context)) }
    var audioGranted by remember {
        mutableStateOf(
            context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == android.content.pm.PackageManager.PERMISSION_GRANTED
        )
    }
    var accessibilityGranted by remember {
        mutableStateOf(isAccessibilityEnabled(context))
    }

    LaunchedEffect(Unit) {
        calendarGranted = CalendarSyncService.hasCalendarPermission(context)
        messageListenerGranted = MessageBridge.isNotificationListenerEnabled(context)
        audioGranted = context.checkSelfPermission(Manifest.permission.RECORD_AUDIO) == android.content.pm.PackageManager.PERMISSION_GRANTED
        accessibilityGranted = isAccessibilityEnabled(context)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            notificationGranted = context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == android.content.pm.PackageManager.PERMISSION_GRANTED
        }
    }

    val calendarLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        calendarGranted = permissions.all { it.value }
    }

    val notificationLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        notificationGranted = granted
    }

    val audioLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        audioGranted = granted
    }

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = stringResource(R.string.onboarding_permission_title),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(R.string.onboarding_permission_subtitle),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(20.dp))

        PermissionCard(
            iconResId = R.drawable.ic_calendar,
            title = stringResource(R.string.onboarding_perm_calendar),
            desc = stringResource(R.string.onboarding_perm_calendar_desc),
            granted = calendarGranted,
            onRequest = {
                calendarLauncher.launch(
                    arrayOf(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR)
                )
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            PermissionCard(
                iconResId = R.drawable.ic_sync,
                title = stringResource(R.string.onboarding_perm_notification),
                desc = stringResource(R.string.onboarding_perm_notification_desc),
                granted = notificationGranted,
                onRequest = {
                    notificationLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                }
            )
            Spacer(modifier = Modifier.height(10.dp))
        }

        PermissionCard(
            iconResId = R.drawable.ic_email,
            title = stringResource(R.string.onboarding_perm_message),
            desc = stringResource(R.string.onboarding_perm_message_desc),
            granted = messageListenerGranted,
            onRequest = {
                val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                context.startActivity(intent)
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        PermissionCard(
            iconResId = R.drawable.ic_ai,
            title = stringResource(R.string.onboarding_perm_audio),
            desc = stringResource(R.string.onboarding_perm_audio_desc),
            granted = audioGranted,
            onRequest = {
                audioLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        PermissionCard(
            iconResId = R.drawable.ic_ai,
            title = stringResource(R.string.onboarding_perm_accessibility),
            desc = stringResource(R.string.onboarding_perm_accessibility_desc),
            granted = accessibilityGranted,
            onRequest = {
                val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
                context.startActivity(intent)
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        PermissionCard(
            iconResId = R.drawable.ic_sync,
            title = stringResource(R.string.onboarding_perm_battery),
            desc = stringResource(R.string.onboarding_perm_battery_desc),
            granted = false,
            onRequest = {
                try {
                    val intent = Intent()
                    val packageName = context.packageName
                    when {
                        Build.MANUFACTURER.equals("xiaomi", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.miui.powerkeeper",
                                "com.miui.powerkeeper.ui.HiddenAppsConfigActivity"
                            )
                            intent.putExtra("package_name", packageName)
                            intent.putExtra("package_label", "PolySpace")
                        }
                        Build.MANUFACTURER.equals("huawei", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.huawei.systemmanager",
                                "com.huawei.systemmanager.optimize.process.ProtectActivity"
                            )
                        }
                        Build.MANUFACTURER.equals("oppo", ignoreCase = true) ||
                        Build.MANUFACTURER.equals("realme", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.coloros.safecenter",
                                "com.coloros.safecenter.permission.startup.StartupAppListActivity"
                            )
                        }
                        Build.MANUFACTURER.equals("vivo", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.vivo.abe",
                                "com.vivo.applicationbehaviorengine.ui.ExcessivePowerManagerActivity"
                            )
                        }
                        else -> {
                            intent.action = Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS
                        }
                    }
                    context.startActivity(intent)
                } catch (e: Exception) {
                    val intent = Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS)
                    context.startActivity(intent)
                }
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        PermissionCard(
            iconResId = R.drawable.ic_sync,
            title = stringResource(R.string.onboarding_perm_autostart),
            desc = stringResource(R.string.onboarding_perm_autostart_desc),
            granted = false,
            onRequest = {
                try {
                    val intent = Intent()
                    val packageName = context.packageName
                    when {
                        Build.MANUFACTURER.equals("xiaomi", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.miui.securitycenter",
                                "com.miui.permcenter.autostart.AutoStartManagementActivity"
                            )
                        }
                        Build.MANUFACTURER.equals("huawei", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.huawei.systemmanager",
                                "com.huawei.systemmanager.startupmgr.ui.StartupNormalAppListActivity"
                            )
                        }
                        Build.MANUFACTURER.equals("oppo", ignoreCase = true) ||
                        Build.MANUFACTURER.equals("realme", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.coloros.safecenter",
                                "com.coloros.safecenter.permission.startup.StartupAppListActivity"
                            )
                        }
                        Build.MANUFACTURER.equals("vivo", ignoreCase = true) -> {
                            intent.component = ComponentName(
                                "com.vivo.abe",
                                "com.vivo.applicationbehaviorengine.ui.ExcessivePowerManagerActivity"
                            )
                        }
                        else -> {
                            intent.action = Settings.ACTION_APPLICATION_DETAILS_SETTINGS
                            intent.data = Uri.fromParts("package", packageName, null)
                        }
                    }
                    context.startActivity(intent)
                } catch (e: Exception) {
                    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                    intent.data = Uri.fromParts("package", context.packageName, null)
                    context.startActivity(intent)
                }
            }
        )
    }
}

private fun isAccessibilityEnabled(context: android.content.Context): Boolean {
    val service = ComponentName(context, "com.polyspace.mobile.service.PolySpaceAccessibilityService")
    val enabledServices = Settings.Secure.getString(
        context.contentResolver,
        Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
    ) ?: return false
    return enabledServices.contains(service.flattenToString())
}

@Composable
private fun PermissionCard(
    iconResId: Int,
    title: String,
    desc: String,
    granted: Boolean,
    onRequest: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = ImageVector.vectorResource(id = iconResId),
                contentDescription = title,
                modifier = Modifier.size(20.dp),
                tint = if (granted) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline
            )
            Spacer(modifier = Modifier.size(12.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Text(
                    text = desc,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (granted) {
                Text(
                    text = stringResource(R.string.onboarding_perm_granted),
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary
                )
            } else {
                OutlinedButton(
                    onClick = onRequest,
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    Text(stringResource(R.string.onboarding_perm_grant))
                }
            }
        }
    }
}
