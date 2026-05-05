package com.polyspace.mobile.ui.screens.onboarding

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.polyspace.mobile.R

data class TierDefinition(
    val key: String,
    val labelResId: Int,
    val hintResId: Int,
    val isRequired: Boolean = false
)

val MODEL_TIERS = listOf(
    TierDefinition("base", R.string.onboarding_tier_base, R.string.onboarding_tier_base_hint, true),
    TierDefinition("strong", R.string.onboarding_tier_strong, R.string.onboarding_tier_strong_hint),
    TierDefinition("performance", R.string.onboarding_tier_performance, R.string.onboarding_tier_performance_hint),
    TierDefinition("cost_effective", R.string.onboarding_tier_cost_effective, R.string.onboarding_tier_cost_effective_hint),
    TierDefinition("vertical_multimodal", R.string.onboarding_tier_multimodal, R.string.onboarding_tier_multimodal_hint),
)

@Composable
@OptIn(ExperimentalMaterial3Api::class)
fun ModelConfigPage(viewModel: OnboardingViewModel) {
    val providerApiKeys by viewModel.providerApiKeys.collectAsState()
    val providerModelIds by viewModel.providerModelIds.collectAsState()
    val providerApiBases by viewModel.providerApiBases.collectAsState()
    val tierProviders by viewModel.tierProviders.collectAsState()
    val context = LocalContext.current

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
        modifier = Modifier.verticalScroll(rememberScrollState())
    ) {
        Text(
            text = stringResource(R.string.onboarding_model_title),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(R.string.onboarding_model_subtitle_tier),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(16.dp))

        MODEL_TIERS.forEachIndexed { index, tier ->
            if (index > 0) {
                HorizontalDivider(
                    color = MaterialTheme.colorScheme.outlineVariant,
                    modifier = Modifier.padding(vertical = 8.dp)
                )
            }

            val tierKey = "tier_${tier.key}"
            val currentProvider = tierProviders[tier.key] ?: ""

            Column(modifier = Modifier.fillMaxWidth()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = stringResource(tier.labelResId),
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onBackground,
                        modifier = Modifier.weight(1f)
                    )
                    if (tier.isRequired) {
                        Text(
                            text = stringResource(R.string.onboarding_tier_required),
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.error,
                        )
                    }
                }

                Text(
                    text = stringResource(tier.hintResId),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    ExposedDropdownMenuBox(
                        expanded = false,
                        onExpandedChange = {}
                    ) {
                        OutlinedTextField(
                            value = currentProvider,
                            onValueChange = { viewModel.updateTierProvider(tier.key, it) },
                            label = { Text(stringResource(R.string.onboarding_model_provider)) },
                            modifier = Modifier.weight(1f),
                            singleLine = true,
                            readOnly = false,
                            placeholder = { Text("e.g. deepseek, openai") }
                        )
                    }

                    OutlinedTextField(
                        value = providerModelIds[tierKey] ?: "",
                        onValueChange = { viewModel.updateTierModelId(tier.key, it) },
                        label = { Text(stringResource(R.string.onboarding_model_id)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = providerApiKeys[tierKey] ?: "",
                        onValueChange = { viewModel.updateTierApiKey(tier.key, it) },
                        label = { Text(stringResource(R.string.onboarding_model_api_key)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        visualTransformation = PasswordVisualTransformation()
                    )

                    val keyUrl = PROVIDER_KEY_URLS[currentProvider]
                    if (keyUrl != null) {
                        TextButton(
                            onClick = {
                                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(keyUrl)))
                            }
                        ) {
                            Text(
                                text = stringResource(R.string.onboarding_model_get_key_short),
                                style = MaterialTheme.typography.labelSmall
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                OutlinedTextField(
                    value = providerApiBases[tierKey] ?: "",
                    onValueChange = { viewModel.updateTierApiBase(tier.key, it) },
                    label = { Text(stringResource(R.string.onboarding_model_api_base)) },
                    placeholder = { Text(stringResource(R.string.onboarding_model_api_base_hint)) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            }
        }

        val baseProvider = tierProviders["base"] ?: ""
        val baseModelId = providerModelIds["tier_base"] ?: ""
        if (baseProvider.isBlank() || baseModelId.isBlank()) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = stringResource(R.string.onboarding_tier_base_required_msg),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
                textAlign = TextAlign.Center,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

private val PROVIDER_KEY_URLS = mapOf(
    "openai" to "https://platform.openai.com/api-keys",
    "anthropic" to "https://console.anthropic.com/",
    "deepseek" to "https://platform.deepseek.com/api_keys",
    "zhipu" to "https://open.bigmodel.cn/",
    "moonshot" to "https://platform.moonshot.cn/",
    "qwen" to "https://dashscope.console.aliyun.com/",
)
