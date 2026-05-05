package com.polyspace.mobile.ui.screens.home

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.polyspace.mobile.R
import com.polyspace.mobile.service.BackendService
import com.polyspace.mobile.service.BackendStatus
import com.polyspace.mobile.service.StartupPhase

@Composable
fun HomeScreen(
    onNavigateToConfig: () -> Unit,
    onNavigateToWebView: (String, Int) -> Unit,
    viewModel: HomeViewModel = viewModel()
) {
    val context = LocalContext.current
    val backendStatus by viewModel.backendStatus.collectAsState()
    val startupPhase by viewModel.startupPhase.collectAsState()
    val startupProgress by viewModel.startupProgress.collectAsState()
    val backendHost by viewModel.backendHost.collectAsState()
    val backendPort by viewModel.backendPort.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.refreshStatus(context)
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 24.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            Spacer(modifier = Modifier.height(16.dp))

            StartupRingIcon(
                modifier = Modifier.size(80.dp),
                status = backendStatus,
                startupPhase = startupPhase,
                progress = startupProgress
            )

            Spacer(modifier = Modifier.height(20.dp))

            Text(
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = statusText(backendStatus, startupPhase),
                style = MaterialTheme.typography.bodyLarge,
                color = when (backendStatus) {
                    BackendStatus.STARTING -> MaterialTheme.colorScheme.primary
                    BackendStatus.ERROR -> MaterialTheme.colorScheme.error
                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                }
            )

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
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = {
                        val prefs = context.getSharedPreferences("polyspace_backend", 0)
                        val useLocalLinux = prefs.getBoolean("use_local_linux", true)
                        BackendService.start(context, backendHost, backendPort, useLocalLinux)
                    },
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus != BackendStatus.RUNNING && backendStatus != BackendStatus.STARTING,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    )
                ) {
                    Text(stringResource(R.string.config_start))
                }
                OutlinedButton(
                    onClick = { BackendService.stop(context) },
                    modifier = Modifier.weight(1f),
                    enabled = backendStatus == BackendStatus.RUNNING || backendStatus == BackendStatus.STARTING
                ) {
                    Text(stringResource(R.string.config_stop))
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

            Spacer(modifier = Modifier.height(24.dp))

            FeatureRow(
                label = stringResource(R.string.ai_assist),
                features = listOf(
                    stringResource(R.string.calendar),
                    stringResource(R.string.todo),
                    stringResource(R.string.knowledge),
                    stringResource(R.string.memo),
                ),
                enabled = backendStatus == BackendStatus.RUNNING,
                onClick = {
                    onNavigateToWebView(backendHost, backendPort)
                }
            )

            Spacer(modifier = Modifier.height(20.dp))

            FeatureRow(
                label = stringResource(R.string.email),
                features = listOf(
                    stringResource(R.string.email),
                    stringResource(R.string.kanban),
                    stringResource(R.string.document),
                    stringResource(R.string.presentation),
                ),
                enabled = backendStatus == BackendStatus.RUNNING,
                onClick = {
                    onNavigateToWebView(backendHost, backendPort)
                }
            )

            Spacer(modifier = Modifier.height(20.dp))

            FeatureRow(
                label = stringResource(R.string.spreadsheet),
                features = listOf(
                    stringResource(R.string.spreadsheet),
                    stringResource(R.string.video),
                    stringResource(R.string.calendar_sync),
                    stringResource(R.string.ai_analyze),
                ),
                enabled = backendStatus == BackendStatus.RUNNING,
                onClick = {
                    onNavigateToWebView(backendHost, backendPort)
                }
            )

            Spacer(modifier = Modifier.height(24.dp))

            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

            Spacer(modifier = Modifier.height(16.dp))

            if (backendStatus == BackendStatus.RUNNING) {
                Button(
                    onClick = { onNavigateToWebView(backendHost, backendPort) },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = MaterialTheme.colorScheme.onPrimary
                    )
                ) {
                    Text(stringResource(R.string.open_workspace))
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            TextButton(
                onClick = onNavigateToConfig,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = stringResource(R.string.settings),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Composable
private fun StartupRingIcon(
    modifier: Modifier = Modifier,
    status: BackendStatus,
    startupPhase: StartupPhase,
    progress: Float
) {
    val color = when (status) {
        BackendStatus.RUNNING -> MaterialTheme.colorScheme.primary
        BackendStatus.STARTING -> MaterialTheme.colorScheme.primary
        BackendStatus.ERROR -> MaterialTheme.colorScheme.error
        else -> MaterialTheme.colorScheme.outlineVariant
    }

    if (status == BackendStatus.STARTING) {
        val infiniteTransition = rememberInfiniteTransition(label = "startup_rotation")
        val rotation by infiniteTransition.animateFloat(
            initialValue = 0f,
            targetValue = 360f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 1500, easing = LinearEasing),
                repeatMode = RepeatMode.Restart
            ),
            label = "rotation"
        )

        Canvas(modifier = modifier) {
            val strokeWidth = 4.dp.toPx()
            val diameter = size.minDimension - strokeWidth * 2
            val topLeft = Offset(
                (size.width - diameter) / 2,
                (size.height - diameter) / 2
            )

            drawArc(
                color = color.copy(alpha = 0.15f),
                startAngle = 0f,
                sweepAngle = 360f,
                useCenter = false,
                topLeft = topLeft,
                size = Size(diameter, diameter),
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )

            rotate(rotation) {
                drawArc(
                    color = color,
                    startAngle = -90f,
                    sweepAngle = 360f * progress.coerceIn(0.05f, 1f),
                    useCenter = false,
                    topLeft = topLeft,
                    size = Size(diameter, diameter),
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
            }
        }
    } else {
        RingIcon(
            modifier = modifier,
            progress = when (status) {
                BackendStatus.RUNNING -> 1f
                BackendStatus.ERROR -> 0.25f
                else -> 0f
            },
            color = color
        )
    }
}

@Composable
private fun RingIcon(
    modifier: Modifier = Modifier,
    progress: Float,
    color: Color
) {
    Canvas(modifier = modifier) {
        val strokeWidth = 4.dp.toPx()
        val diameter = size.minDimension - strokeWidth * 2
        val topLeft = Offset(
            (size.width - diameter) / 2,
            (size.height - diameter) / 2
        )

        drawArc(
            color = color.copy(alpha = 0.15f),
            startAngle = 0f,
            sweepAngle = 360f,
            useCenter = false,
            topLeft = topLeft,
            size = Size(diameter, diameter),
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )

        if (progress > 0f) {
            drawArc(
                color = color,
                startAngle = -90f,
                sweepAngle = 360f * progress,
                useCenter = false,
                topLeft = topLeft,
                size = Size(diameter, diameter),
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )
        }
    }
}

@Composable
private fun FeatureRow(
    label: String,
    features: List<String>,
    enabled: Boolean,
    onClick: () -> Unit
) {
    val featureColor = if (enabled) MaterialTheme.colorScheme.onSurface else MaterialTheme.colorScheme.outlineVariant

    Column {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.Medium
        )
        Spacer(modifier = Modifier.height(10.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(0.dp)
        ) {
            features.forEach { feature ->
                Column(
                    modifier = Modifier
                        .weight(1f)
                        .clickable(enabled = enabled) { onClick() },
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    RingIcon(
                        modifier = Modifier.size(32.dp),
                        progress = if (enabled) 0.6f else 0f,
                        color = featureColor
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = feature,
                        style = MaterialTheme.typography.labelSmall,
                        color = featureColor
                    )
                }
            }
        }
    }
}

@Composable
private fun statusText(status: BackendStatus, phase: StartupPhase = StartupPhase.IDLE): String {
    return when (status) {
        BackendStatus.RUNNING -> stringResource(R.string.config_status_running)
        BackendStatus.STARTING -> stringResource(R.string.config_status_starting)
        BackendStatus.ERROR -> if (phase == StartupPhase.FAILED) phase.label else stringResource(R.string.config_status_error)
        BackendStatus.STOPPED -> stringResource(R.string.config_status_stopped)
    }
}
