package com.polyspace.mobile.ui.screens.config

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
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.polyspace.mobile.R
import com.polyspace.mobile.ui.screens.config.SettingsManager.SettingCategory
import com.polyspace.mobile.ui.screens.config.SettingsManager.SettingDefinition
import com.polyspace.mobile.ui.screens.config.SettingsManager.SettingType

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FullSettingsScreen(
    category: SettingCategory,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val settings = SettingsManager.getSettingsByCategory(category)
    val categoryLabel = when (category) {
        SettingCategory.GENERAL -> "通用设置"
        SettingCategory.UI -> "界面设置"
        SettingCategory.SYNC -> "同步设置"
        SettingCategory.SECURITY -> "安全设置"
        SettingCategory.ADVANCED -> "高级设置"
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text(categoryLabel) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = ImageVector.vectorResource(id = R.drawable.ic_back),
                            contentDescription = "返回"
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

            Text(
                text = "$categoryLabel (${settings.size}项)",
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(16.dp))

            settings.forEachIndexed { index, setting ->
                SettingItem(setting = setting)
                if (index < settings.size - 1) {
                    Spacer(modifier = Modifier.height(12.dp))
                }
            }

            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun SettingItem(setting: SettingDefinition) {
    val context = LocalContext.current

    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            text = setting.name,
            style = MaterialTheme.typography.bodyLarge,
            fontWeight = FontWeight.Medium
        )
        Text(
            text = setting.description,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))

        when (setting.type) {
            SettingType.BOOLEAN -> {
                val currentValue = SettingsManager.getSetting(context, setting.key, setting.defaultValue as Boolean)
                var checked by remember { mutableStateOf(currentValue) }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = if (checked) "已开启" else "已关闭",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Switch(
                        checked = checked,
                        onCheckedChange = { newValue ->
                            checked = newValue
                            SettingsManager.setSetting(context, setting.key, newValue)
                        }
                    )
                }
            }
            SettingType.INT -> {
                val currentValue = SettingsManager.getSetting(context, setting.key, setting.defaultValue as Int)
                var value by remember { mutableStateOf(currentValue.toFloat()) }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = value.toInt().toString(),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold
                    )
                }
                Slider(
                    value = value,
                    onValueChange = { newValue ->
                        value = newValue
                        SettingsManager.setSetting(context, setting.key, newValue.toInt())
                    },
                    valueRange = setting.intRange.first.toFloat()..setting.intRange.last.toFloat(),
                    modifier = Modifier.fillMaxWidth()
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(setting.intRange.first.toString(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(setting.intRange.last.toString(), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            SettingType.FLOAT -> {
                val currentValue = SettingsManager.getSetting(context, setting.key, setting.defaultValue as Float)
                var value by remember { mutableStateOf(currentValue) }
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        text = String.format("%.2f", value),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold
                    )
                }
                Slider(
                    value = value,
                    onValueChange = { newValue ->
                        value = newValue
                        SettingsManager.setSetting(context, setting.key, newValue)
                    },
                    valueRange = setting.floatRange,
                    modifier = Modifier.fillMaxWidth()
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(String.format("%.1f", setting.floatRange.start), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(String.format("%.1f", setting.floatRange.endInclusive), style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            SettingType.STRING -> {
                val currentValue = SettingsManager.getSetting(context, setting.key, setting.defaultValue as String)
                var value by remember { mutableStateOf(currentValue) }
                OutlinedTextField(
                    value = value,
                    onValueChange = { newValue ->
                        value = newValue
                        SettingsManager.setSetting(context, setting.key, newValue)
                    },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }
            SettingType.ENUM -> {
                val currentValue = SettingsManager.getSetting(context, setting.key, setting.defaultValue as String)
                var selectedIndex by remember { mutableStateOf(setting.enumValues.indexOf(currentValue).coerceAtLeast(0)) }
                Column {
                    setting.enumValues.forEachIndexed { index, option ->
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = option,
                                style = MaterialTheme.typography.bodyMedium,
                                color = if (index == selectedIndex) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                            )
                            Switch(
                                checked = index == selectedIndex,
                                onCheckedChange = { checked ->
                                    if (checked) {
                                        selectedIndex = index
                                        SettingsManager.setSetting(context, setting.key, option)
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(4.dp))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
    }
}
