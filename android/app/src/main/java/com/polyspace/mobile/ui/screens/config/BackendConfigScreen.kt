package com.polyspace.mobile.ui.screens.config

import android.Manifest
import android.content.Intent
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.polyspace.mobile.R
import com.polyspace.mobile.service.BackendStatus
import com.polyspace.mobile.service.CalendarSyncService
import com.polyspace.mobile.service.MessageBridge
import com.polyspace.mobile.service.MessageListenerService
import com.polyspace.mobile.service.StartupPhase
import com.polyspace.mobile.ui.screens.config.SettingsManager.SettingCategory
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BackendConfigScreen(
    onBack: () -> Unit,
    onNavigateToMessageConfig: () -> Unit = {},
    onNavigateToFullSettings: (String) -> Unit = {},
    viewModel: BackendConfigViewModel = viewModel()
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val backendStatus by viewModel.backendStatus.collectAsState()
    val startupPhase by viewModel.startupPhase.collectAsState()
    val startupProgress by viewModel.startupProgress.collectAsState()
    val autoStart by viewModel.autoStart.collectAsState()
    var syncStatus by remember { mutableStateOf("") }
    var autoForward by remember { mutableStateOf(MessageBridge.isAutoForwardEnabled()) }

    val messageListenerEnabled = MessageBridge.isNotificationListenerEnabled(context)
    val monitoredApps = MessageListenerService.getMonitoredApps(context)
    val host by viewModel.host.collectAsState()
    val port by viewModel.port.collectAsState()

    val calendarPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.all { it.value }
        if (allGranted) {
            syncStatus = context.getString(R.string.permission_grant)
        }
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.settings)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = ImageVector.vectorResource(id = R.drawable.ic_back),
                            contentDescription = stringResource(R.string.back)
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            Spacer(modifier = Modifier.height(8.dp))

            SectionLabel(stringResource(R.string.local_linux))
            Spacer(modifier = Modifier.height(12.dp))

            SwitchRow(
                label = stringResource(R.string.auto_start),
                checked = autoStart,
                onCheckedChange = viewModel::updateAutoStart
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = viewModel::startBackend,
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus != BackendStatus.RUNNING && backendStatus != BackendStatus.STARTING,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    )
                ) { Text(stringResource(R.string.config_start)) }

                OutlinedButton(
                    onClick = viewModel::stopBackend,
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus == BackendStatus.RUNNING || backendStatus == BackendStatus.STARTING
                ) { Text(stringResource(R.string.config_stop)) }
            }

            if (backendStatus == BackendStatus.STARTING) {
                Spacer(modifier = Modifier.height(12.dp))
                LinearProgressIndicator(
                    progress = { startupProgress },
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.primary,
                    trackColor = MaterialTheme.colorScheme.surfaceVariant,
                )
                if (startupPhase != StartupPhase.IDLE) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = startupPhase.label,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Spacer(modifier = Modifier.height(24.dp))

            SectionLabel(stringResource(R.string.calendar_sync))
            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = {
                        if (!CalendarSyncService.hasCalendarPermission(context)) {
                            calendarPermissionLauncher.launch(
                                arrayOf(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR)
                            )
                        } else {
                            scope.launch {
                                val result = CalendarSyncService.syncToSystemCalendar(context, host, port)
                                syncStatus = if (result.isSuccess) context.getString(R.string.sync_success) else context.getString(R.string.sync_failed)
                            }
                        }
                    },
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus == BackendStatus.RUNNING
                ) { Text(stringResource(R.string.sync_to_system)) }

                OutlinedButton(
                    onClick = {
                        if (!CalendarSyncService.hasCalendarPermission(context)) {
                            calendarPermissionLauncher.launch(
                                arrayOf(Manifest.permission.READ_CALENDAR, Manifest.permission.WRITE_CALENDAR)
                            )
                        } else {
                            scope.launch {
                                val result = CalendarSyncService.syncFromSystemCalendar(context, host, port)
                                syncStatus = if (result.isSuccess) context.getString(R.string.sync_success) else context.getString(R.string.sync_failed)
                            }
                        }
                    },
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus == BackendStatus.RUNNING
                ) { Text(stringResource(R.string.sync_from_system)) }
            }

            if (syncStatus.isNotEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Text(syncStatus, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }

            Spacer(modifier = Modifier.height(24.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Spacer(modifier = Modifier.height(24.dp))

            SectionLabel(stringResource(R.string.message_listener))
            Spacer(modifier = Modifier.height(12.dp))

            if (!messageListenerEnabled) {
                Text(
                    text = stringResource(R.string.message_listener_desc),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                Button(
                    onClick = {
                        val intent = Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)
                        context.startActivity(intent)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    )
                ) {
                    Text(stringResource(R.string.enable_message_listener))
                }
            } else {
                Text(
                    text = stringResource(R.string.message_listener_enabled) + " (${monitoredApps.size}${context.getString(R.string.apps_count)})",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))
                SwitchRow(
                    label = stringResource(R.string.auto_forward),
                    checked = autoForward,
                    onCheckedChange = { enabled ->
                        autoForward = enabled
                        MessageBridge.setAutoForward(enabled)
                        MessageBridge.setBackendConfig(host, port)
                    }
                )
                Spacer(modifier = Modifier.height(12.dp))
                OutlinedButton(
                    onClick = onNavigateToMessageConfig,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(stringResource(R.string.configure_monitored_apps))
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
            Spacer(modifier = Modifier.height(24.dp))

            SectionLabel("完整设置 (${SettingsManager.getSettingCount()}项)")
            Spacer(modifier = Modifier.height(12.dp))

            val settingCategories = listOf(
                SettingCategory.GENERAL to "通用设置",
                SettingCategory.UI to "界面设置",
                SettingCategory.SYNC to "同步设置",
                SettingCategory.SECURITY to "安全设置",
                SettingCategory.ADVANCED to "高级设置",
            )
            settingCategories.forEach { (key, label) ->
                OutlinedButton(
                    onClick = { onNavigateToFullSettings(key.name) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(label)
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Text(
        text = text,
        style = MaterialTheme.typography.labelMedium,
        fontWeight = FontWeight.Medium,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

@Composable
private fun SwitchRow(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, style = MaterialTheme.typography.bodyLarge)
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedTrackColor = MaterialTheme.colorScheme.primary,
                checkedThumbColor = MaterialTheme.colorScheme.onPrimary
            )
        )
    }
}
