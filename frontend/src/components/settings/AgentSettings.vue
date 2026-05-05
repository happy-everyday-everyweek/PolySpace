<template>
  <div class="settings-section">
    <h2 class="global-section-title">AI Agent 设置</h2>
    <div class="global-form-group">
      <label>执行模式</label>
      <div class="mode-options">
        <label class="mode-option" :class="{ active: executionMode === 'auto' }">
          <input type="radio" v-model="executionMode" value="auto" />
          <span class="mode-label">自动</span>
          <span class="mode-desc">由系统根据任务复杂度自动选择</span>
        </label>
        <label class="mode-option" :class="{ active: executionMode === 'single' }">
          <input type="radio" v-model="executionMode" value="single" />
          <span class="mode-label">单智能体优先</span>
          <span class="mode-desc">优先使用单个智能体处理任务</span>
        </label>
        <label class="mode-option" :class="{ active: executionMode === 'multi' }">
          <input type="radio" v-model="executionMode" value="multi" />
          <span class="mode-label">多智能体协作优先</span>
          <span class="mode-desc">优先使用多智能体协作处理任务</span>
        </label>
      </div>
    </div>

    <h3 class="subsection-title">AI 原子能力</h3>
    <p class="section-hint">管理AI可调用的原子能力来源。点击展开可查看和配置各来源下的具体工具。</p>

    <div class="capability-config-block">
      <div class="capability-summary-bar">
        <div class="summary-stat">
          <span class="stat-value">{{ capabilitySummary.total }}</span>
          <span class="stat-label">总能力数</span>
        </div>
        <div class="summary-stat" v-for="(count, cat) in topCategories" :key="String(cat)">
          <span class="stat-value">{{ count }}</span>
          <span class="stat-label">{{ categoryLabel(String(cat)) }}</span>
        </div>
      </div>

      <div class="capability-provider-list">
        <div v-for="p in providerList" :key="p.key" class="capability-provider-item" :class="{ expanded: expandedProvider === p.key }">
          <div class="provider-row" @click="toggleProvider(p.key)">
            <div class="provider-info">
              <div class="provider-header">
                <svg class="expand-icon" :class="{ rotated: expandedProvider === p.key }" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9,18 15,12 9,6"/></svg>
                <span class="provider-name">{{ p.label }}</span>
                <span class="provider-count" v-if="capabilitySummary.by_source[p.key]">{{ capabilitySummary.by_source[p.key] }}</span>
              </div>
              <span class="provider-desc">{{ p.desc }}</span>
            </div>
            <label class="global-switch" @click.stop>
              <input type="checkbox" v-model="capabilityProviders[p.key + '_enabled' as keyof typeof capabilityProviders]" />
              <span class="slider"></span>
            </label>
          </div>

          <div v-if="expandedProvider === p.key" class="provider-detail">
            <div v-if="p.key === 'internal'" class="cap-tool-list">
              <div class="cap-toolbar">
                <input type="text" v-model="internalFilter" class="global-input cap-filter" placeholder="搜索工具..." />
                <button class="inference-btn sm" @click="loadInternalCaps" :disabled="capsLoading">刷新</button>
              </div>
              <div v-if="capsLoading" class="cap-empty">加载中...</div>
              <div v-else-if="internalCaps.length === 0" class="cap-empty">暂无内置工具</div>
              <div v-for="cap in filteredInternalCaps" :key="cap.name" class="cap-item">
                <div class="cap-item-info">
                  <span class="cap-item-name">{{ cap.display_name }}</span>
                  <span class="cap-item-cat">{{ categoryLabel(cap.category) }}</span>
                </div>
                <span class="cap-item-desc">{{ cap.description }}</span>
                <div class="cap-item-actions">
                  <span class="cap-state" :class="'state-' + cap.state">{{ stateLabel(cap.state) }}</span>
                  <button v-if="cap.state === 'inactive'" class="inference-btn sm" @click="activateCap(cap.name)">激活</button>
                  <button v-if="cap.state === 'active'" class="inference-btn sm unload" @click="deactivateCap(cap.name)">停用</button>
                </div>
              </div>
            </div>

            <div v-if="p.key === 'mcp'" class="cap-tool-list">
              <div class="cap-toolbar">
                <button class="inference-btn sm" @click="showMcpForm = !showMcpForm">{{ showMcpForm ? '取消' : '添加服务器' }}</button>
                <button class="inference-btn sm" @click="showMcpAiForm = !showMcpAiForm; showMcpForm = false">{{ showMcpAiForm ? '取消' : 'AI 辅助配置' }}</button>
                <button class="inference-btn sm" @click="loadMcpServers" :disabled="capsLoading">刷新</button>
              </div>
              <div v-if="showMcpAiForm" class="mcp-form">
                <div class="field-group">
                  <label>描述你需要的MCP工具</label>
                  <textarea v-model="mcpAiPrompt" class="global-input text-area" rows="3" placeholder="例如：我需要一个能搜索GitHub仓库的MCP工具，或者一个能操作本地文件系统的工具..."></textarea>
                </div>
                <button class="inference-btn sm" @click="aiGenerateMcpConfig" :disabled="!mcpAiPrompt.trim() || mcpAiLoading">
                  {{ mcpAiLoading ? '生成中...' : 'AI 生成配置' }}
                </button>
                <div v-if="mcpAiResult" class="mcp-ai-result">
                  <div class="field-row">
                    <div class="field-group flex-1">
                      <label>名称</label>
                      <input type="text" v-model="mcpAiResult.name" class="global-input" />
                    </div>
                    <div class="field-group flex-1">
                      <label>命令</label>
                      <input type="text" v-model="mcpAiResult.command" class="global-input" />
                    </div>
                  </div>
                  <div class="field-row">
                    <div class="field-group flex-1">
                      <label>参数 (逗号分隔)</label>
                      <input type="text" v-model="mcpAiResult.args" class="global-input" />
                    </div>
                  </div>
                  <button class="inference-btn sm" @click="applyMcpAiResult" :disabled="!mcpAiResult.name || !mcpAiResult.command">确认并注册</button>
                </div>
              </div>
              <div v-if="showMcpForm" class="mcp-form">
                <div class="field-row">
                  <div class="field-group flex-1">
                    <label>名称</label>
                    <input type="text" v-model="mcpForm.name" class="global-input" placeholder="my-server" />
                  </div>
                  <div class="field-group flex-1">
                    <label>命令</label>
                    <input type="text" v-model="mcpForm.command" class="global-input" placeholder="npx @modelcontextprotocol/server-xxx" />
                  </div>
                </div>
                <div class="field-row">
                  <div class="field-group flex-1">
                    <label>参数 (逗号分隔)</label>
                    <input type="text" v-model="mcpForm.args" class="global-input" placeholder="--port,8080" />
                  </div>
                </div>
                <button class="inference-btn sm" @click="registerMcpServer" :disabled="!mcpForm.name || !mcpForm.command">注册</button>
              </div>
              <div v-if="mcpServers.length === 0" class="cap-empty">暂无已注册的MCP服务器</div>
              <div v-for="srv in mcpServers" :key="srv.name" class="cap-item mcp-server-item">
                <div class="cap-item-info">
                  <span class="cap-item-name">{{ srv.name }}</span>
                  <span class="cap-state" :class="srv.connected ? 'state-active' : 'state-inactive'">{{ srv.connected ? '已连接' : '未连接' }}</span>
                </div>
                <div class="cap-item-actions">
                  <button v-if="!srv.connected" class="inference-btn sm" @click="connectMcp(srv.name)">连接</button>
                  <button v-if="srv.connected" class="inference-btn sm unload" @click="disconnectMcp(srv.name)">断开</button>
                  <button class="inference-btn sm danger" @click="removeMcp(srv.name)">移除</button>
                </div>
              </div>
            </div>

            <div v-if="p.key === 'skill'" class="cap-tool-list">
              <div class="cap-toolbar">
                <button class="inference-btn sm" @click="discoverSkills" :disabled="capsLoading">发现技能</button>
                <button class="inference-btn sm" @click="loadSkills" :disabled="capsLoading">刷新</button>
              </div>
              <div v-if="skills.length === 0" class="cap-empty">暂无已加载的技能</div>
              <div v-for="sk in skills" :key="sk.name" class="cap-item">
                <div class="cap-item-info">
                  <span class="cap-item-name">{{ sk.name }}</span>
                  <span class="cap-item-cat">{{ sk.category || '通用' }}</span>
                  <span v-if="sk.version" class="cap-item-ver">v{{ sk.version }}</span>
                </div>
                <span class="cap-item-desc">{{ sk.description }}</span>
              </div>
            </div>

            <div v-if="p.key === 'cli'" class="cap-tool-list">
              <div class="cap-toolbar">
                <button class="inference-btn sm" @click="scanCliTools" :disabled="capsLoading">扫描系统工具</button>
                <button class="inference-btn sm" @click="showCliAiForm = !showCliAiForm">{{ showCliAiForm ? '取消' : 'AI 辅助配置' }}</button>
                <button class="inference-btn sm" @click="loadCliCaps" :disabled="capsLoading">刷新</button>
              </div>
              <div v-if="showCliAiForm" class="mcp-form">
                <div class="field-group">
                  <label>描述你需要的命令行工具</label>
                  <textarea v-model="cliAiPrompt" class="global-input text-area" rows="3" placeholder="例如：我需要一个能自动部署到服务器的工具，或者一个能批量处理图片的工具..."></textarea>
                </div>
                <button class="inference-btn sm" @click="aiGenerateCliConfig" :disabled="!cliAiPrompt.trim() || cliAiLoading">
                  {{ cliAiLoading ? '生成中...' : 'AI 生成配置' }}
                </button>
                <div v-if="cliAiResult" class="mcp-ai-result">
                  <div class="field-group">
                    <label>AI 建议的工具及安装方式</label>
                    <div class="cli-ai-suggestion" v-html="cliAiResult"></div>
                  </div>
                  <button class="inference-btn sm" @click="applyCliAiResult">一键安装并扫描</button>
                </div>
              </div>
              <div v-if="capsLoading && cliCaps.length === 0" class="cap-empty">扫描中...</div>
              <div v-else-if="cliCaps.length === 0" class="cap-empty">点击"扫描系统工具"检测可用命令行工具</div>
              <div v-for="cap in cliCaps" :key="cap.name" class="cap-item">
                <div class="cap-item-info">
                  <span class="cap-item-name">{{ cap.display_name }}</span>
                  <span class="cap-item-cat">{{ categoryLabel(cap.category) }}</span>
                  <span v-if="cap.version" class="cap-item-ver">v{{ cap.version }}</span>
                </div>
                <span class="cap-item-desc">{{ cap.description }}</span>
              </div>
            </div>

            <div v-if="p.key === 'device'" class="cap-tool-list">
              <div class="cap-toolbar">
                <button class="inference-btn sm" @click="loadDevices" :disabled="capsLoading">刷新</button>
              </div>
              <div v-if="devices.length === 0" class="cap-empty">暂无已连接的远程设备</div>
              <div v-for="dev in devices" :key="dev.device_id" class="cap-item device-item">
                <div class="cap-item-info">
                  <span class="cap-item-name">{{ dev.device_name }}</span>
                  <span class="cap-state" :class="dev.status === 'online' ? 'state-active' : 'state-inactive'">{{ dev.status }}</span>
                  <span class="cap-item-cat">{{ dev.platform }}</span>
                </div>
                <span class="cap-item-desc">{{ dev.capabilities?.length || 0 }} 个能力</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="capability-actions">
        <button class="inference-btn" @click="refreshCapabilities" :disabled="capabilityRefreshing">
          {{ capabilityRefreshing ? '刷新中...' : '刷新能力注册表' }}
        </button>
      </div>
    </div>

    <h3 class="subsection-title">本地推理框架</h3>
    <p class="section-hint">配置本地推理引擎，支持 Ollama 和 llama.cpp 后端。启用后可在无网络环境下使用 AI 功能。</p>

    <div class="inference-config-block">
      <div class="global-form-group lab-row">
        <label>启用本地推理</label>
        <label class="global-switch">
          <input type="checkbox" v-model="inferenceEnabled" @change="toggleInference" />
          <span class="slider"></span>
        </label>
      </div>

      <template v-if="inferenceEnabled">
        <div class="global-form-group">
          <label>推理后端</label>
          <select v-model="inferenceConfig.backend" class="global-input">
            <option value="ollama">Ollama</option>
            <option value="llama_cpp">llama.cpp</option>
          </select>
        </div>

        <div v-if="inferenceConfig.backend === 'ollama'" class="global-form-group">
          <label>Ollama 地址</label>
          <input type="text" v-model="inferenceConfig.ollamaHost" class="global-input" placeholder="http://localhost:11434" />
        </div>

        <div v-if="inferenceConfig.backend === 'ollama'" class="global-form-group">
          <label>模型名称</label>
          <input type="text" v-model="inferenceConfig.modelName" class="global-input" placeholder="如: llama3, qwen2.5" />
        </div>

        <div v-if="inferenceConfig.backend === 'llama_cpp'" class="global-form-group">
          <label>模型文件路径</label>
          <input type="text" v-model="inferenceConfig.modelPath" class="global-input" placeholder="如: D:/models/qwen2.5-7b-q4_k_m.gguf" />
        </div>

        <div class="inference-actions">
          <button class="inference-btn" :class="{ loading: inferenceLoading }" @click="loadInferenceModel" :disabled="inferenceLoading">
            {{ inferenceLoaded ? '已加载 - 点击重新加载' : '加载模型' }}
          </button>
          <button v-if="inferenceLoaded" class="inference-btn unload" @click="unloadInferenceModel">卸载模型</button>
        </div>

        <div v-if="inferenceStatus" class="inference-status" :class="inferenceLoaded ? 'status-ok' : 'status-idle'">
          <svg v-if="inferenceLoaded" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <span>{{ inferenceStatus }}</span>
        </div>

        <div v-if="inferenceLoaded" class="inference-test">
          <label>推理测试</label>
          <div class="test-row">
            <input type="text" v-model="testPrompt" class="global-input" placeholder="输入测试提示词..." @keyup.enter="runTest" />
            <button class="inference-btn" @click="runTest" :disabled="testRunning">{{ testRunning ? '生成中...' : '测试' }}</button>
          </div>
          <div v-if="testResult" class="test-result">
            <p>{{ testResult }}</p>
          </div>
        </div>
      </template>
    </div>

    <h3 class="subsection-title">模型配置</h3>
    <p class="section-hint">配置各层级模型及其API密钥。选择Provider后API地址将自动填充，也可手动修改。</p>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge required">基础模型</span>
        <span class="model-tier-desc">默认模型，未配置分级模型时所有调用使用此模型</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.base_provider" @change="onProviderChange('base')" class="global-input">
              <option value="">请选择</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.base_model" class="global-input" :placeholder="providerDefaults[modelConfig.base_provider]?.defaultModel || '如: glm-4'" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.base ? 'text' : 'password'" v-model="modelConfig.base_api_key" class="global-input" :placeholder="providerDefaults[modelConfig.base_provider]?.requiresApiKey === false ? '可选' : 'sk-...'" />
              <button class="toggle-visibility" @click="showKeys.base = !showKeys.base" :title="showKeys.base ? '隐藏' : '显示'">
                <svg v-if="!showKeys.base" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.base_api_base" class="global-input" :placeholder="providerDefaults[modelConfig.base_provider]?.apiBase || 'https://...'" />
          </div>
        </div>
      </div>
    </div>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge">强能力模型</span>
        <span class="model-tier-desc">复杂规划任务</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.strong_provider" @change="onProviderChange('strong')" class="global-input">
              <option value="">同基础模型</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.strong_model" class="global-input" :placeholder="providerDefaults[modelConfig.strong_provider || modelConfig.base_provider]?.defaultModel || '如: glm-5.1'" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.strong ? 'text' : 'password'" v-model="modelConfig.strong_api_key" class="global-input" placeholder="留空则使用基础模型Key" />
              <button class="toggle-visibility" @click="showKeys.strong = !showKeys.strong">
                <svg v-if="!showKeys.strong" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.strong_api_base" class="global-input" placeholder="留空则使用基础模型URL" />
          </div>
        </div>
      </div>
    </div>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge">高性能模型</span>
        <span class="model-tier-desc">日常任务</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.performance_provider" @change="onProviderChange('performance')" class="global-input">
              <option value="">同基础模型</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.performance_model" class="global-input" placeholder="如: qwen3.5-35b-a3b" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.performance ? 'text' : 'password'" v-model="modelConfig.performance_api_key" class="global-input" placeholder="留空则使用基础模型Key" />
              <button class="toggle-visibility" @click="showKeys.performance = !showKeys.performance">
                <svg v-if="!showKeys.performance" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.performance_api_base" class="global-input" placeholder="留空则使用基础模型URL" />
          </div>
        </div>
      </div>
    </div>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge">性价比模型</span>
        <span class="model-tier-desc">高Token任务</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.cost_effective_provider" @change="onProviderChange('cost_effective')" class="global-input">
              <option value="">同基础模型</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.cost_effective_model" class="global-input" placeholder="如: qwen3.5-4b" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.costEffective ? 'text' : 'password'" v-model="modelConfig.cost_effective_api_key" class="global-input" placeholder="留空则使用基础模型Key" />
              <button class="toggle-visibility" @click="showKeys.costEffective = !showKeys.costEffective">
                <svg v-if="!showKeys.costEffective" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.cost_effective_api_base" class="global-input" placeholder="留空则使用基础模型URL" />
          </div>
        </div>
      </div>
    </div>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge">多模态模型</span>
        <span class="model-tier-desc">处理图片/视频/音频输入</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.multimodal_provider" @change="onProviderChange('multimodal')" class="global-input">
              <option value="">同基础模型</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.multimodal_model" class="global-input" placeholder="如: glm-4v" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.multimodal ? 'text' : 'password'" v-model="modelConfig.multimodal_api_key" class="global-input" placeholder="留空则使用基础模型Key" />
              <button class="toggle-visibility" @click="showKeys.multimodal = !showKeys.multimodal">
                <svg v-if="!showKeys.multimodal" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.multimodal_api_base" class="global-input" placeholder="留空则使用基础模型URL" />
          </div>
        </div>
        <div class="field-row">
          <div class="global-form-group">
            <label>模型能力</label>
            <div class="capability-checkboxes">
              <label class="cap-checkbox"><input type="checkbox" v-model="modelCapabilities.multimodal_image" /> 图片理解</label>
              <label class="cap-checkbox"><input type="checkbox" v-model="modelCapabilities.multimodal_audio" /> 音频理解</label>
              <label class="cap-checkbox"><input type="checkbox" v-model="modelCapabilities.multimodal_video" /> 视频理解</label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="model-config-block">
      <div class="model-block-header">
        <span class="model-tier-badge">屏幕操作模型</span>
        <span class="model-tier-desc">屏幕操作和自动化任务</span>
      </div>
      <div class="model-fields">
        <div class="field-row">
          <div class="field-group flex-1">
            <label>Provider</label>
            <select v-model="modelConfig.screen_provider" @change="onProviderChange('screen')" class="global-input">
              <option value="">同基础模型</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="zhipu">智谱AI</option>
              <option value="qwen">通义千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="moonshot">月之暗面</option>
              <option value="baichuan">百川</option>
              <option value="doubao">豆包</option>
              <option value="siliconflow">硅基流动</option>
              <option value="openrouter">OpenRouter</option>
              <option value="ollama">Ollama</option>
              <option value="lmstudio">LM Studio</option>
              <option value="custom">自定义</option>
            </select>
          </div>
          <div class="field-group flex-1">
            <label>模型名称</label>
            <input type="text" v-model="modelConfig.screen_model" class="global-input" placeholder="如: autoglm-phone-9b" />
          </div>
        </div>
        <div class="field-row">
          <div class="field-group flex-1">
            <label>API Key</label>
            <div class="input-with-toggle">
              <input :type="showKeys.screen ? 'text' : 'password'" v-model="modelConfig.screen_api_key" class="global-input" placeholder="留空则使用基础模型Key" />
              <button class="toggle-visibility" @click="showKeys.screen = !showKeys.screen">
                <svg v-if="!showKeys.screen" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
          </div>
          <div class="field-group flex-1">
            <label>API Base URL</label>
            <input type="text" v-model="modelConfig.screen_api_base" class="global-input" placeholder="留空则使用基础模型URL" />
          </div>
        </div>
      </div>
    </div>

    <h3 class="subsection-title">LLM 高级配置</h3>
    <div class="llm-advanced-block">
      <div class="field-row">
        <div class="global-form-group flex-1">
          <label>请求超时 (秒)</label>
          <input type="number" v-model.number="llmAdvanced.LLM_REQUEST_TIMEOUT" class="global-input" min="5" max="600" step="1" />
        </div>
        <div class="global-form-group flex-1">
          <label>最大重试次数</label>
          <input type="number" v-model.number="llmAdvanced.LLM_MAX_RETRIES" class="global-input" min="0" max="10" />
        </div>
        <div class="global-form-group flex-1">
          <label>重试延迟 (秒)</label>
          <input type="number" v-model.number="llmAdvanced.LLM_RETRY_DELAY" class="global-input" min="0" max="60" step="0.5" />
        </div>
      </div>
    </div>

    <h3 class="subsection-title">人格设置</h3>
    <div class="global-form-group">
      <label>AI 名称</label>
      <input type="text" v-model="personaForm.name" class="global-input" />
    </div>

    <div class="global-form-group">
      <label>温暖度</label>
      <div class="slider-row">
        <span class="slider-label">冷静</span>
        <input type="range" min="0" max="100" v-model.number="warmthVal" class="range-input" />
        <span class="slider-label">温暖</span>
      </div>
    </div>

    <div class="global-form-group">
      <label>幽默度</label>
      <div class="slider-row">
        <span class="slider-label">严肃</span>
        <input type="range" min="0" max="100" v-model.number="humorVal" class="range-input" />
        <span class="slider-label">幽默</span>
      </div>
    </div>

    <div class="global-form-group">
      <label>正式度</label>
      <div class="slider-row">
        <span class="slider-label">随意</span>
        <input type="range" min="0" max="100" v-model.number="formalityVal" class="range-input" />
        <span class="slider-label">正式</span>
      </div>
    </div>

    <div class="global-form-group">
      <label>简洁度</label>
      <div class="slider-row">
        <span class="slider-label">详尽</span>
        <input type="range" min="0" max="100" v-model.number="concisenessVal" class="range-input" />
        <span class="slider-label">简洁</span>
      </div>
    </div>

    <div class="global-form-group">
      <label>开放性</label>
      <div class="slider-row">
        <span class="slider-label">保守</span>
        <input type="range" min="0" max="100" v-model.number="opennessVal" class="range-input" />
        <span class="slider-label">好奇</span>
      </div>
    </div>

    <div class="global-form-group">
      <label>外向性</label>
      <div class="slider-row">
        <span class="slider-label">内敛</span>
        <input type="range" min="0" max="100" v-model.number="extraversionVal" class="range-input" />
        <span class="slider-label">外向</span>
      </div>
    </div>

    <div v-if="personaPreview" class="persona-preview">
      <label>人格预览</label>
      <p class="preview-text">{{ personaPreview }}</p>
    </div>

    <div class="global-form-group">
      <label>自定义指令</label>
      <textarea v-model="personaForm.custom_instructions" class="global-input text-area" rows="3" placeholder="给AI的额外行为指令..."></textarea>
    </div>

    <MemorySettings />

    <div class="save-bar">
      <button class="save-btn" :class="{ saved: saved, 'save-error': messageType === 'error' && message }" @click="saveAll" :disabled="saving">
        <svg v-if="saved" class="check-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="saving">保存中...</span>
        <span v-else-if="saved">已保存</span>
        <span v-else>保存设置</span>
      </button>
      <button class="cancel-btn" @click="resetAll">重置</button>
      <span v-if="message && messageType === 'error'" class="save-error-text">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useSettings } from '@/composables/useSettings'
import { useSettingsStore } from '@/stores/settings'
import api from '@/utils/api'
import MemorySettings from './MemorySettings.vue'

const { settings, updateAgent } = useSettings()
const settingsStore = useSettingsStore()

const saving = ref(false)
const saved = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const capabilityProviders = reactive({
  internal_enabled: true,
  mcp_enabled: true,
  skill_enabled: true,
  cli_enabled: true,
  device_bridge_enabled: true,
})

const capabilitySummary = reactive({
  by_source: {} as Record<string, number>,
  by_category: {} as Record<string, number>,
  total: 0,
})

const capabilityRefreshing = ref(false)
const expandedProvider = ref<string | null>(null)
const capsLoading = ref(false)

const providerList = [
  { key: 'internal', label: '内置工具', desc: '系统内置的70+工具，包括邮件、日历、待办、知识库、PDF等' },
  { key: 'mcp', label: 'MCP 工具', desc: '通过MCP协议连接的外部工具服务器' },
  { key: 'skill', label: '技能系统', desc: '已加载的技能包提供的专业能力' },
  { key: 'cli', label: '命令行工具', desc: '系统PATH中检测到的命令行工具，如git、docker、npm等' },
  { key: 'device', label: '设备桥接', desc: '已连接的远程设备(Android/Windows/Web)提供的能力' },
]

const internalCaps = ref<any[]>([])
const internalFilter = ref('')
const filteredInternalCaps = computed(() => {
  if (!internalFilter.value) return internalCaps.value
  const kw = internalFilter.value.toLowerCase()
  return internalCaps.value.filter(c => c.name.toLowerCase().includes(kw) || c.display_name.toLowerCase().includes(kw) || (c.description || '').toLowerCase().includes(kw))
})

const mcpServers = ref<any[]>([])
const showMcpForm = ref(false)
const showMcpAiForm = ref(false)
const mcpForm = reactive({ name: '', command: '', args: '' })
const mcpAiPrompt = ref('')
const mcpAiLoading = ref(false)
const mcpAiResult = ref<{ name: string; command: string; args: string } | null>(null)

const skills = ref<any[]>([])
const cliCaps = ref<any[]>([])
const showCliAiForm = ref(false)
const cliAiPrompt = ref('')
const cliAiLoading = ref(false)
const cliAiResult = ref<string>('')
const devices = ref<any[]>([])

function toggleProvider(key: string) {
  const wasExpanded = expandedProvider.value === key
  expandedProvider.value = wasExpanded ? null : key
  if (!wasExpanded) {
    if (key === 'internal' && internalCaps.value.length === 0) loadInternalCaps()
    else if (key === 'mcp' && mcpServers.value.length === 0) loadMcpServers()
    else if (key === 'skill' && skills.value.length === 0) loadSkills()
    else if (key === 'cli' && cliCaps.value.length === 0) loadCliCaps()
    else if (key === 'device' && devices.value.length === 0) loadDevices()
  }
}

function stateLabel(state: string): string {
  const map: Record<string, string> = { inactive: '未激活', activating: '激活中', active: '已激活', calling: '调用中', hibernating: '休眠', error: '错误' }
  return map[state] || state
}

async function loadInternalCaps() {
  capsLoading.value = true
  try {
    const res = await api.get('/tools/capabilities', { params: { source_type: 'internal' } })
    const caps = res.data.capabilities || []
    internalCaps.value = caps.map((c: any) => ({ ...c, state: 'active' }))
  } catch { /* ignore */ } finally { capsLoading.value = false }
}

async function activateCap(name: string) {
  try { await api.post(`/tools/capabilities/${name}/activate`) } catch { /* ignore */ }
  await loadInternalCaps()
}

async function deactivateCap(name: string) {
  try { await api.post(`/tools/capabilities/${name}/deactivate`) } catch { /* ignore */ }
  await loadInternalCaps()
}

async function loadMcpServers() {
  capsLoading.value = true
  try {
    const res = await api.get('/tools/mcp/servers')
    const registered = res.data.registered || []
    const connected = res.data.connected || []
    const connectedSet = new Set(connected)
    mcpServers.value = registered.map((name: string) => ({ name, connected: connectedSet.has(name) }))
  } catch { /* ignore */ } finally { capsLoading.value = false }
}

async function registerMcpServer() {
  try {
    const args = mcpForm.args ? mcpForm.args.split(',').map(s => s.trim()).filter(Boolean) : []
    await api.post('/tools/mcp/register', { name: mcpForm.name, command: mcpForm.command, args })
    showMcpForm.value = false
    mcpForm.name = ''
    mcpForm.command = ''
    mcpForm.args = ''
    await loadMcpServers()
  } catch { /* ignore */ }
}

async function aiGenerateMcpConfig() {
  if (!mcpAiPrompt.value.trim()) return
  mcpAiLoading.value = true
  mcpAiResult.value = null
  try {
    const res = await api.post('/chat', {
      message: `根据以下需求，生成MCP服务器配置。只返回JSON格式，包含name(服务器名称，英文小写短横线)、command(启动命令)、args(参数数组)字段，不要其他内容。\n\n需求：${mcpAiPrompt.value}`,
      stream: false,
    })
    let content = res.data?.response || res.data?.content || res.data?.message || ''
    const jsonMatch = content.match(/\{[\s\S]*\}/)
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0])
      mcpAiResult.value = {
        name: parsed.name || '',
        command: parsed.command || '',
        args: Array.isArray(parsed.args) ? parsed.args.join(',') : (parsed.args || ''),
      }
    }
  } catch {
    mcpAiResult.value = null
  } finally {
    mcpAiLoading.value = false
  }
}

async function applyMcpAiResult() {
  if (!mcpAiResult.value) return
  mcpForm.name = mcpAiResult.value.name
  mcpForm.command = mcpAiResult.value.command
  mcpForm.args = mcpAiResult.value.args
  mcpAiResult.value = null
  showMcpAiForm.value = false
  showMcpForm.value = true
  await registerMcpServer()
}

async function connectMcp(name: string) {
  try { await api.post(`/tools/mcp/connect/${name}`) } catch { /* ignore */ }
  await loadMcpServers()
}

async function disconnectMcp(name: string) {
  try { await api.post(`/tools/mcp/disconnect/${name}`) } catch { /* ignore */ }
  await loadMcpServers()
}

async function removeMcp(name: string) {
  try { await api.delete(`/tools/mcp/servers/${name}`) } catch { /* ignore */ }
  await loadMcpServers()
}

async function loadSkills() {
  capsLoading.value = true
  try {
    const res = await api.get('/tools/skills')
    skills.value = res.data.skills || []
  } catch { /* ignore */ } finally { capsLoading.value = false }
}

async function discoverSkills() {
  capsLoading.value = true
  try { await api.post('/tools/skills/discover') } catch { /* ignore */ }
  await loadSkills()
}

async function loadCliCaps() {
  capsLoading.value = true
  try {
    const res = await api.get('/tools/capabilities', { params: { source_type: 'cli' } })
    cliCaps.value = res.data.capabilities || []
  } catch { /* ignore */ } finally { capsLoading.value = false }
}

async function scanCliTools() {
  capsLoading.value = true
  try { await api.post('/tools/cli/scan') } catch { /* ignore */ }
  await loadCliCaps()
}

async function aiGenerateCliConfig() {
  if (!cliAiPrompt.value.trim()) return
  cliAiLoading.value = true
  cliAiResult.value = ''
  try {
    const res = await api.post('/chat', {
      message: `用户需要命令行工具，请根据需求推荐合适的工具和安装命令。返回HTML格式，使用简单的标签(p, code, strong)，不要使用script标签。包含：1)推荐工具名 2)安装命令(用code标签包裹) 3)简要说明。\n\n需求：${cliAiPrompt.value}`,
      stream: false,
    })
    cliAiResult.value = res.data?.response || res.data?.content || res.data?.message || '无法生成建议'
  } catch {
    cliAiResult.value = ''
  } finally {
    cliAiLoading.value = false
  }
}

async function applyCliAiResult() {
  const codeMatches = cliAiResult.value.match(/<code[^>]*>([\s\S]*?)<\/code>/g)
  if (codeMatches) {
    for (const match of codeMatches) {
      const cmd = match.replace(/<\/?code[^>]*>/g, '').trim()
      if (cmd) {
        try { await api.post('/tools/cli/install', { command: cmd }) } catch { /* ignore */ }
      }
    }
  }
  cliAiResult.value = ''
  showCliAiForm.value = false
  await scanCliTools()
}

async function loadDevices() {
  capsLoading.value = true
  try {
    const res = await api.get('/devices')
    devices.value = res.data.devices || []
  } catch { /* ignore */ } finally { capsLoading.value = false }
}

const _CATEGORY_LABELS: Record<string, string> = {
  system: '系统',
  file: '文件',
  communication: '通讯',
  network: '网络',
  media: '媒体',
  hardware: '硬件',
  accessibility: '无障碍',
  automation: '自动化',
  browser: '浏览器',
  storage: '存储',
  process: '进程',
  clipboard: '剪贴板',
  window: '窗口',
  notification: '通知',
  search: '搜索',
  scheduler: '日程',
  document: '文档',
  knowledge: '知识库',
  memory: '记忆',
  coordination: '协调',
  productivity: '效率',
  creative: '创意',
  lifestyle: '生活',
  workflow: '工作流',
  integration: '集成',
  content: '内容',
  analytics: '分析',
  finance: '财务',
  security: '安全',
  database: '数据库',
  development: '开发',
}

function categoryLabel(cat: string): string {
  return _CATEGORY_LABELS[cat] || cat
}

const topCategories = computed(() => {
  const entries = Object.entries(capabilitySummary.by_category)
  entries.sort((a, b) => b[1] - a[1])
  return Object.fromEntries(entries.slice(0, 5))
})

async function loadCapabilitySettings() {
  try {
    const res = await api.get('/settings/capabilities')
    const data = res.data
    if (data.providers) {
      capabilityProviders.internal_enabled = data.providers.internal_enabled ?? true
      capabilityProviders.mcp_enabled = data.providers.mcp_enabled ?? true
      capabilityProviders.skill_enabled = data.providers.skill_enabled ?? true
      capabilityProviders.cli_enabled = data.providers.cli_enabled ?? true
      capabilityProviders.device_bridge_enabled = data.providers.device_bridge_enabled ?? true
    }
    if (data.summary) {
      capabilitySummary.by_source = data.summary.by_source || {}
      capabilitySummary.by_category = data.summary.by_category || {}
      capabilitySummary.total = data.summary.total || 0
    }
  } catch {
    // use defaults
  }
}

async function refreshCapabilities() {
  capabilityRefreshing.value = true
  try {
    await api.post('/tools/capabilities/initialize')
    await loadCapabilitySettings()
  } catch {
    // ignore
  } finally {
    capabilityRefreshing.value = false
  }
}

const inferenceEnabled = ref(false)
const inferenceLoaded = ref(false)
const inferenceLoading = ref(false)
const inferenceStatus = ref('')
const testPrompt = ref('')
const testResult = ref('')
const testRunning = ref(false)

const inferenceConfig = reactive({
  backend: 'ollama',
  modelPath: '',
  modelName: '',
  ollamaHost: 'http://localhost:11434',
})

async function loadInferenceStatus() {
  try {
    const res = await api.get('/inference/status')
    inferenceLoaded.value = res.data.loaded
    if (res.data.loaded) {
      inferenceStatus.value = `已加载 (${res.data.backend})`
    }
    if (res.data.config) {
      inferenceConfig.backend = res.data.config.backend || 'ollama'
      inferenceConfig.modelPath = res.data.config.model_path || ''
      inferenceConfig.modelName = res.data.config.model_name || ''
      inferenceConfig.ollamaHost = res.data.config.ollama_host || 'http://localhost:11434'
    }
  } catch {
    inferenceStatus.value = '无法连接推理服务'
  }
}

async function toggleInference() {
  if (inferenceEnabled.value) {
    await loadInferenceStatus()
  } else {
    inferenceStatus.value = ''
  }
}

async function loadInferenceModel() {
  inferenceLoading.value = true
  inferenceStatus.value = '正在加载模型...'
  try {
    const res = await api.post('/inference/load', {
      backend: inferenceConfig.backend,
      model_path: inferenceConfig.modelPath,
      model_name: inferenceConfig.modelName,
      ollama_host: inferenceConfig.ollamaHost,
    })
    inferenceLoaded.value = res.data.loaded
    if (res.data.loaded) {
      inferenceStatus.value = `已加载 (${res.data.backend})`
    } else {
      inferenceStatus.value = '加载失败，请检查配置'
    }
  } catch (e: any) {
    inferenceStatus.value = `加载失败: ${e.response?.data?.detail || e.message}`
  } finally {
    inferenceLoading.value = false
  }
}

async function unloadInferenceModel() {
  try {
    await api.post('/inference/unload')
    inferenceLoaded.value = false
    inferenceStatus.value = '模型已卸载'
  } catch (e) {
    inferenceStatus.value = '卸载失败'
  }
}

async function runTest() {
  if (!testPrompt.value.trim()) return
  testRunning.value = true
  testResult.value = ''
  try {
    const res = await api.post('/inference/generate', {
      prompt: testPrompt.value,
      model: inferenceConfig.modelName || undefined,
    })
    if (res.data.success) {
      testResult.value = res.data.text
    } else {
      testResult.value = `错误: ${res.data.error}`
    }
  } catch (e: any) {
    testResult.value = `请求失败: ${e.response?.data?.detail || e.message}`
  } finally {
    testRunning.value = false
  }
}

const executionMode = ref<'auto' | 'single' | 'multi'>(settings.value.agent.executionMode)

const modelConfig = ref({
  base_model: '',
  base_provider: '',
  base_api_key: '',
  base_api_base: '',
  strong_model: '',
  strong_provider: '',
  strong_api_key: '',
  strong_api_base: '',
  performance_model: '',
  performance_provider: '',
  performance_api_key: '',
  performance_api_base: '',
  cost_effective_model: '',
  cost_effective_provider: '',
  cost_effective_api_key: '',
  cost_effective_api_base: '',
  multimodal_model: '',
  multimodal_provider: '',
  multimodal_api_key: '',
  multimodal_api_base: '',
  screen_model: '',
  screen_provider: '',
  screen_api_key: '',
  screen_api_base: '',
})

const showKeys = reactive({
  base: false,
  strong: false,
  performance: false,
  costEffective: false,
  multimodal: false,
  screen: false,
})

const providerDefaults: Record<string, { apiBase: string; defaultModel: string; requiresApiKey: boolean }> = {
  openai: { apiBase: 'https://api.openai.com/v1', defaultModel: 'gpt-4o', requiresApiKey: true },
  anthropic: { apiBase: 'https://api.anthropic.com/v1', defaultModel: 'claude-3-opus-20240229', requiresApiKey: true },
  zhipu: { apiBase: 'https://open.bigmodel.cn/api/paas/v4', defaultModel: 'glm-4', requiresApiKey: true },
  qwen: { apiBase: 'https://dashscope.aliyuncs.com/compatible-mode/v1', defaultModel: 'qwen-max', requiresApiKey: true },
  deepseek: { apiBase: 'https://api.deepseek.com/v1', defaultModel: 'deepseek-chat', requiresApiKey: true },
  moonshot: { apiBase: 'https://api.moonshot.cn/v1', defaultModel: 'moonshot-v1-128k', requiresApiKey: true },
  baichuan: { apiBase: 'https://api.baichuan-ai.com/v1', defaultModel: 'baichuan4', requiresApiKey: true },
  doubao: { apiBase: 'https://ark.cn-beijing.volces.com/api/v3', defaultModel: 'doubao-pro-4k', requiresApiKey: true },
  siliconflow: { apiBase: 'https://api.siliconflow.cn/v1', defaultModel: 'Qwen/Qwen2.5-7B-Instruct', requiresApiKey: true },
  openrouter: { apiBase: 'https://openrouter.ai/api/v1', defaultModel: 'google/gemini-pro', requiresApiKey: true },
  ollama: { apiBase: 'http://localhost:11434/v1', defaultModel: '', requiresApiKey: false },
  lmstudio: { apiBase: 'http://localhost:1234/v1', defaultModel: '', requiresApiKey: false },
  custom: { apiBase: '', defaultModel: '', requiresApiKey: true },
}

const _providerApiBases = Object.fromEntries(
  Object.entries(providerDefaults).map(([k, v]) => [k, v.apiBase])
)

function onProviderChange(tier: string) {
  const providerKey = `${tier}_provider` as keyof typeof modelConfig.value
  const apiBaseKey = `${tier}_api_base` as keyof typeof modelConfig.value
  const provider = modelConfig.value[providerKey] as string
  if (!provider) return

  const defaults = providerDefaults[provider]
  if (!defaults) return

  const currentBase = (modelConfig.value[apiBaseKey] as string) || ''
  const isDefaultOrEmpty = !currentBase || Object.values(_providerApiBases).includes(currentBase)
  if (isDefaultOrEmpty && defaults.apiBase) {
    (modelConfig.value as any)[apiBaseKey] = defaults.apiBase
  }
}

const modelCapabilities = reactive({
  multimodal_image: false,
  multimodal_audio: false,
  multimodal_video: false,
})

const llmAdvanced = reactive({
  LLM_REQUEST_TIMEOUT: 120,
  LLM_MAX_RETRIES: 3,
  LLM_RETRY_DELAY: 1.0,
})

const personaForm = ref({
  name: 'Poly',
  custom_instructions: '',
})

const warmthVal = ref(75)
const humorVal = ref(50)
const formalityVal = ref(35)
const concisenessVal = ref(55)
const opennessVal = ref(75)
const extraversionVal = ref(55)

const personaPreview = computed(() => {
  const parts: string[] = []
  if (opennessVal.value >= 70) parts.push('对新事物充满好奇')
  else if (opennessVal.value >= 40) parts.push('对新鲜事物保持适度兴趣')
  else parts.push('偏好熟悉和稳定的事物')

  if (warmthVal.value >= 70) parts.push('温暖亲切')
  else if (warmthVal.value >= 40) parts.push('友好平和')
  else parts.push('冷静客观')

  if (humorVal.value >= 70) parts.push('幽默风趣')
  else if (humorVal.value >= 40) parts.push('偶尔俏皮')
  else parts.push('严肃认真')

  if (extraversionVal.value >= 70) parts.push('性格外向')
  else if (extraversionVal.value >= 40) parts.push('性格温和')
  else parts.push('性格内敛')

  return `${personaForm.value.name}：${parts.join('，')}。`
})

async function loadModels() {
  try {
    const res = await api.get('/settings/models')
    const data = res.data
    for (const [key, value] of Object.entries(data)) {
      if (key.endsWith('_api_key') && value === '***') {
        (modelConfig.value as any)[key] = '***'
      } else if (key === 'multimodal_capabilities') {
        const caps = value as string[] || []
        modelCapabilities.multimodal_image = caps.includes('image')
        modelCapabilities.multimodal_audio = caps.includes('audio')
        modelCapabilities.multimodal_video = caps.includes('video')
      } else if (key in modelConfig.value) {
        (modelConfig.value as any)[key] = value ?? ''
      }
    }
  } catch (e) {
    console.error('Failed to load model config:', e)
  }
}

async function loadLlmAdvanced() {
  try {
    const res = await api.get('/settings/env')
    const vars = res.data?.variables || {}
    for (const groupVars of Object.values(vars) as any[][]) {
      for (const env of groupVars) {
        if (env.key in llmAdvanced) {
          (llmAdvanced as any)[env.key] = env.value ?? (llmAdvanced as any)[env.key]
        }
      }
    }
  } catch {
    // use defaults
  }
}

async function saveAll() {
  saving.value = true
  message.value = ''
  saved.value = false
  try {
    await updateAgent({ executionMode: executionMode.value })

    const modelPayload: Record<string, any> = {}
    for (const [key, value] of Object.entries(modelConfig.value)) {
      if (typeof value === 'string' && value === '***') continue
      modelPayload[key] = value
    }
    const multimodalCaps: string[] = []
    if (modelCapabilities.multimodal_image) multimodalCaps.push('image')
    if (modelCapabilities.multimodal_audio) multimodalCaps.push('audio')
    if (modelCapabilities.multimodal_video) multimodalCaps.push('video')
    modelPayload.multimodal_capabilities = multimodalCaps
    await api.put('/settings/models', modelPayload)

    if (inferenceEnabled.value) {
      await api.put('/inference/config', {
        backend: inferenceConfig.backend,
        model_path: inferenceConfig.modelPath,
        model_name: inferenceConfig.modelName,
        ollama_host: inferenceConfig.ollamaHost,
      })
    }

    await api.put('/settings/env', { updates: { ...llmAdvanced } })

    await api.put('/settings/capabilities', { ...capabilityProviders })

    await settingsStore.updatePersona({
      name: personaForm.value.name,
      communication: {
        formality: formalityVal.value / 100,
        warmth: warmthVal.value / 100,
        humor: humorVal.value / 100,
        conciseness: concisenessVal.value / 100,
      },
      big_five: {
        openness: opennessVal.value / 100,
        conscientiousness: 0.65,
        extraversion: extraversionVal.value / 100,
        agreeableness: 0.80,
        neuroticism: 0.30,
      },
      custom_instructions: personaForm.value.custom_instructions,
    })

    saved.value = true
    messageType.value = 'success'
    setTimeout(() => { saved.value = false }, 1500)
  } catch (e: any) {
    message.value = e.message || '保存失败'
    messageType.value = 'error'
    setTimeout(() => { message.value = '' }, 3000)
  } finally {
    saving.value = false
  }
}

function resetAll() {
  executionMode.value = settings.value.agent.executionMode
  loadModels()
  loadLlmAdvanced()
  loadCapabilitySettings()
  const p = settingsStore.persona
  if (p) {
    personaForm.value.name = p.name || 'Poly'
    personaForm.value.custom_instructions = p.custom_instructions || ''
    warmthVal.value = Math.round((p.communication?.warmth ?? 0.75) * 100)
    humorVal.value = Math.round((p.communication?.humor ?? 0.5) * 100)
    formalityVal.value = Math.round((p.communication?.formality ?? 0.35) * 100)
    concisenessVal.value = Math.round((p.communication?.conciseness ?? 0.55) * 100)
    opennessVal.value = Math.round((p.big_five?.openness ?? 0.75) * 100)
    extraversionVal.value = Math.round((p.big_five?.extraversion ?? 0.55) * 100)
  }
}

onMounted(async () => {
  await Promise.all([
    settingsStore.fetchPersona(),
    loadModels(),
    loadInferenceStatus(),
    loadLlmAdvanced(),
    loadCapabilitySettings(),
  ])
  const p = settingsStore.persona
  if (p) {
    personaForm.value.name = p.name || 'Poly'
    personaForm.value.custom_instructions = p.custom_instructions || ''
    warmthVal.value = Math.round((p.communication?.warmth ?? 0.75) * 100)
    humorVal.value = Math.round((p.communication?.humor ?? 0.5) * 100)
    formalityVal.value = Math.round((p.communication?.formality ?? 0.35) * 100)
    concisenessVal.value = Math.round((p.communication?.conciseness ?? 0.55) * 100)
    opennessVal.value = Math.round((p.big_five?.openness ?? 0.75) * 100)
    extraversionVal.value = Math.round((p.big_five?.extraversion ?? 0.55) * 100)
  }
  inferenceEnabled.value = inferenceLoaded.value
})
</script>

<style scoped>
.settings-section {
  max-width: 640px;
}

.subsection-title {
  font-size: 15px;
  font-weight: 600;
  margin: 24px 0 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color);
  color: var(--text-secondary);
}

.section-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.mode-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.mode-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg, 8px);
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.mode-option:hover {
  border-color: var(--primary-color);
}

.mode-option.active {
  border-color: var(--primary-color);
  background-color: var(--bg-secondary);
}

.mode-option input[type="radio"] {
  margin-top: 2px;
  accent-color: var(--primary-color);
}

.mode-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
}

.mode-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  display: block;
  margin-top: 2px;
}

.model-config-block {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
}

.model-block-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.model-tier-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  background: var(--primary-light);
  color: var(--primary-color);
  white-space: nowrap;
}

.model-tier-badge.required {
  background: var(--primary-light);
  color: var(--text-primary);
}

.model-tier-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}

.model-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-row {
  display: flex;
  gap: 8px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.field-group.flex-1 {
  flex: 1;
}

.field-group label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

.field-group select {
  cursor: pointer;
}

.input-with-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
}

.input-with-toggle .global-input {
  flex: 1;
}

.toggle-visibility {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  color: var(--text-tertiary);
  background: none;
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-visibility:hover {
  color: var(--text-primary);
  background: var(--border-color);
}

.text-area {
  resize: vertical;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.slider-label {
  font-size: 11px;
  color: var(--text-tertiary);
  min-width: 28px;
  text-align: center;
}

.range-input {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border-color);
  border-radius: var(--radius-sm);
  outline: none;
}

.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--primary-color);
  cursor: pointer;
}

.persona-preview {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.persona-preview label {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 6px;
}

.preview-text {
  font-size: 13px;
  color: var(--text-color);
  line-height: 1.5;
}

.inference-config-block {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
}

.capability-config-block {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
}

.capability-provider-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.capability-provider-item {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-color);
  transition: border-color 0.2s;
  overflow: hidden;
}

.capability-provider-item:hover {
  border-color: var(--primary-color);
}

.capability-provider-item.expanded {
  border-color: var(--primary-color);
}

.provider-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
}

.expand-icon {
  transition: transform 0.2s;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.expand-icon.rotated {
  transform: rotate(90deg);
}

.provider-detail {
  border-top: 1px solid var(--border-color);
  padding: 12px;
  background: var(--bg-secondary);
}

.cap-tool-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cap-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.cap-filter {
  flex: 1;
  font-size: 12px;
  padding: 4px 8px;
}

.cap-empty {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 12px;
  text-align: center;
}

.cap-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
}

.cap-item-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cap-item-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-color);
}

.cap-item-cat {
  font-size: 10px;
  color: var(--primary-color);
  background: var(--primary-light);
  padding: 1px 5px;
  border-radius: 3px;
}

.cap-item-ver {
  font-size: 10px;
  color: var(--text-tertiary);
}

.cap-item-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  line-height: 1.4;
}

.cap-item-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
}

.cap-state {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.cap-state.state-active {
  background: var(--primary-light);
  color: var(--text-primary);
}

.cap-state.state-inactive {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.cap-state.state-error {
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.cap-state.state-activating,
.cap-state.state-calling,
.cap-state.state-hibernating {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.mcp-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-color);
  margin-bottom: 8px;
}

.mcp-ai-result {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  background: var(--bg-secondary);
  margin-top: 4px;
}

.cli-ai-suggestion {
  font-size: 12px;
  line-height: 1.6;
  color: var(--text-secondary);
  padding: 8px;
  background: var(--bg-color);
  border-radius: 4px;
}

.cli-ai-suggestion :deep(code) {
  background: var(--bg-secondary);
  padding: 1px 4px;
  border-radius: 3px;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 11px;
}

.capability-checkboxes {
  display: flex;
  gap: 16px;
  align-items: center;
}

.cap-checkbox {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
}

.cap-checkbox input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--primary-color);
}

.inference-btn.sm {
  padding: 3px 10px;
  font-size: 11px;
}

.inference-btn.danger {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.inference-btn.danger:hover {
  background: var(--primary-light);
}

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}

.provider-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
}

.provider-count {
  font-size: 11px;
  color: var(--primary-color);
  background: var(--primary-light);
  padding: 1px 6px;
  border-radius: 4px;
}

.provider-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  display: block;
}

.capability-summary-bar {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding: 10px 12px;
  background: var(--bg-color);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.summary-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 48px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--primary-color);
}

.stat-label {
  font-size: 10px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.capability-actions {
  margin-top: 12px;
}

.llm-advanced-block {
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  background: var(--bg-secondary);
}

.lab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.lab-row label:first-child {
  font-size: 14px;
  color: var(--text-color);
}

.global-switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
  cursor: pointer;
}

.global-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.global-switch .slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--border-color);
  border-radius: 22px;
  transition: 0.2s;
}

.global-switch .slider::before {
  content: '';
  position: absolute;
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.2s;
}

.global-switch input:checked + .slider {
  background: var(--primary-color);
}

.global-switch input:checked + .slider::before {
  transform: translateX(18px);
}

.inference-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.inference-btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: opacity 0.15s;
  border: none;
}

.inference-btn:hover {
  opacity: 0.9;
}

.inference-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inference-btn.unload {
  background: var(--border-color);
  color: var(--text-secondary);
}

.inference-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.inference-status.status-ok {
  background: var(--primary-light);
  color: var(--text-primary);
}

.inference-status.status-idle {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.inference-test {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.inference-test label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 6px;
  display: block;
}

.test-row {
  display: flex;
  gap: 8px;
}

.test-row .global-input {
  flex: 1;
}

.test-result {
  margin-top: 8px;
  padding: 10px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-color);
  line-height: 1.5;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.save-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.save-btn {
  padding: 6px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.save-btn:hover {
  opacity: 0.9;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn.saved {
  background: var(--text-secondary);
  animation: save-pop 0.35s ease;
}

.save-btn.save-error {
  background: var(--text-primary);
  animation: save-shake 0.4s ease;
}

.check-icon {
  width: 14px;
  height: 14px;
}

@keyframes save-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.08); }
  100% { transform: scale(1); }
}

@keyframes save-shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-3px); }
  40% { transform: translateX(3px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
}

.cancel-btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
}

.cancel-btn:hover {
  background: var(--border-color);
}

.save-error-text {
  font-size: 12px;
  color: var(--text-primary);
  margin-left: 4px;
}
</style>
