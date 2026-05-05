<template>
  <div class="settings-section overview-section">
    <h2 class="global-section-title">概览</h2>

    <div class="period-selector">
      <button
        v-for="p in periods"
        :key="p.value"
        class="period-btn"
        :class="{ active: selectedPeriod === p.value }"
        @click="changePeriod(p.value)"
      >
        {{ p.label }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <svg class="spin-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="10" stroke="var(--border-color)" stroke-width="2"/>
        <path d="M12 2a10 10 0 0 1 10 10" stroke="var(--primary-color)" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <span>加载中...</span>
    </div>

    <div v-else-if="error" class="error-state">{{ error }}</div>

    <template v-else-if="stats">
      <div class="stats-group">
        <h3 class="group-title">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M2 4h14M2 9h14M2 14h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          文档编辑
        </h3>
        <div class="card-grid">
          <div class="stat-card card-blue">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="4" y="2" width="16" height="20" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M8 7h8M8 11h8M8 15h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
            <div class="card-value">{{ stats.documents.documents_edited }}</div>
            <div class="card-label">编辑文档数</div>
          </div>
          <div class="stat-card card-indigo">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M4 4h4v4H4zM10 4h4v4h-4zM16 4h4v4h-4zM4 10h4v4H4zM10 10h4v4h-4zM16 10h4v4h-4zM4 16h4v4H4zM10 16h4v4h-4z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.documents.document_estimated_words) }}</div>
            <div class="card-label">编辑字数</div>
          </div>
          <div class="stat-card card-cyan">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 1 1 3 3L7 19l-4 1 1-4L16.5 3.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.ai_activity.file_edits) }}</div>
            <div class="card-label">文件编辑次数</div>
          </div>
        </div>
      </div>

      <div class="stats-group">
        <h3 class="group-title">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M3 14l3-5 3 3 4-6 2 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          AI 对话
        </h3>
        <div class="card-grid">
          <div class="stat-card card-green">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ stats.chat.session_count }}</div>
            <div class="card-label">对话会话数</div>
          </div>
          <div class="stat-card card-emerald">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" stroke="currentColor" stroke-width="1.5"/><path d="M8 9h.01M16 9h.01M9 15c.8 1 1.8 1.5 3 1.5s2.2-.5 3-1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
            <div class="card-value">{{ stats.chat.user_message_count }}</div>
            <div class="card-label">你说了多少句</div>
          </div>
          <div class="stat-card card-teal">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2a10 10 0 0 1 10 10 10 10 0 0 1-10 10A10 10 0 0 1 2 12 10 10 0 0 1 12 2z" stroke="currentColor" stroke-width="1.5"/><path d="M8 14s1.5 2 4 2 4-2 4-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="9" cy="9" r="1" fill="currentColor"/><circle cx="15" cy="9" r="1" fill="currentColor"/></svg>
            </div>
            <div class="card-value">{{ stats.chat.assistant_message_count }}</div>
            <div class="card-label">AI 回复了多少句</div>
          </div>
          <div class="stat-card card-lime">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.chat.user_characters_typed) }}</div>
            <div class="card-label">你打了多少字</div>
          </div>
        </div>
      </div>

      <div class="stats-group">
        <h3 class="group-title">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M9 2l2.5 5 5.5.8-4 3.9.9 5.5L9 14.5 4.1 17.2l.9-5.5-4-3.9L6.5 7z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
          AI 贡献
        </h3>
        <div class="card-grid">
          <div class="stat-card card-orange">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ stats.ai_activity.ai_tasks_completed }}</div>
            <div class="card-label">AI 完成任务数</div>
          </div>
          <div class="stat-card card-amber">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ stats.ai_activity.tool_calls_made }}</div>
            <div class="card-label">工具调用次数</div>
          </div>
          <div class="stat-card card-rose">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/><path d="M12 6v6l4 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatDuration(stats.ai_activity.ai_duration_seconds) }}</div>
            <div class="card-label">AI 工作时长</div>
          </div>
          <div class="stat-card card-pink">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
            <div class="card-value">{{ formatTimeSaved(stats.ai_activity.ai_estimated_time_saved_minutes) }}</div>
            <div class="card-label">AI 节省时间</div>
          </div>
        </div>
      </div>

      <div class="stats-group">
        <h3 class="group-title">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="3" width="14" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M6 7h6M6 10h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          Token 消耗
        </h3>
        <div class="card-grid">
          <div class="stat-card card-violet">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.tokens.total_tokens) }}</div>
            <div class="card-label">总 Token 数</div>
          </div>
          <div class="stat-card card-purple">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.tokens.total_input_tokens) }}</div>
            <div class="card-label">输入 Token</div>
          </div>
          <div class="stat-card card-fuchsia">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 10h8M8 14h5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
            </div>
            <div class="card-value">{{ formatNumber(stats.tokens.total_output_tokens) }}</div>
            <div class="card-label">输出 Token</div>
          </div>
          <div class="stat-card card-sky">
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </div>
            <div class="card-value">{{ stats.tokens.total_records }}</div>
            <div class="card-label">API 调用次数</div>
          </div>
        </div>
      </div>

      <div class="stats-group" v-if="stats.tokens.by_model && stats.tokens.by_model.length > 0">
        <h3 class="group-title">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><rect x="2" y="2" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M2 7h14M7 2v14" stroke="currentColor" stroke-width="1.5"/></svg>
          模型用量明细
        </h3>
        <div class="model-table-wrap">
          <table class="model-table">
            <thead>
              <tr>
                <th>模型</th>
                <th>调用次数</th>
                <th>输入 Token</th>
                <th>输出 Token</th>
                <th>总 Token</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in stats.tokens.by_model" :key="m.model_name">
                <td class="model-name">{{ m.model_name || '未知' }}</td>
                <td>{{ m.count }}</td>
                <td>{{ formatNumber(m.input_tokens) }}</td>
                <td>{{ formatNumber(m.output_tokens) }}</td>
                <td>{{ formatNumber(m.input_tokens + m.output_tokens) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useOverview } from '@/composables/useOverview'

const { stats, loading, error, fetchStats } = useOverview()

const selectedPeriod = ref('all')

const periods = [
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
  { value: 'all', label: '全部' },
]

function changePeriod(period: string) {
  selectedPeriod.value = period
  fetchStats(period === 'all' ? undefined : period)
}

function formatNumber(n: number): string {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return seconds + '秒'
  if (seconds < 3600) return Math.round(seconds / 60) + '分钟'
  return (seconds / 3600).toFixed(1) + '小时'
}

function formatTimeSaved(minutes: number): string {
  if (minutes < 1) return '<1分钟'
  if (minutes < 60) return Math.round(minutes) + '分钟'
  if (minutes < 1440) return (minutes / 60).toFixed(1) + '小时'
  return (minutes / 1440).toFixed(1) + '天'
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.overview-section {
  max-width: 100%;
}

.period-selector {
  display: flex;
  gap: 6px;
  margin-bottom: 24px;
}

.period-btn {
  padding: 6px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  transition: all var(--transition-fast);
}

.period-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.period-btn.active {
  background: var(--primary-color);
  color: #fff;
  border-color: var(--primary-color);
}

.loading-state,
.error-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.error-state {
  color: #ef4444;
}

.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.stats-group {
  margin-bottom: 28px;
}

.group-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: box-shadow var(--transition-fast);
}

.stat-card:hover {
  box-shadow: var(--shadow);
}

.card-icon {
  margin-bottom: 4px;
}

.card-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1.2;
}

.card-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-blue .card-icon { color: #3b82f6; }
.card-indigo .card-icon { color: #6366f1; }
.card-cyan .card-icon { color: #06b6d4; }
.card-green .card-icon { color: #10b981; }
.card-emerald .card-icon { color: #059669; }
.card-teal .card-icon { color: #14b8a6; }
.card-lime .card-icon { color: #84cc16; }
.card-orange .card-icon { color: #f97316; }
.card-amber .card-icon { color: #f59e0b; }
.card-rose .card-icon { color: #f43f5e; }
.card-pink .card-icon { color: #ec4899; }
.card-violet .card-icon { color: #8b5cf6; }
.card-purple .card-icon { color: #a855f7; }
.card-fuchsia .card-icon { color: #d946ef; }
.card-sky .card-icon { color: #0ea5e9; }

.model-table-wrap {
  overflow-x: auto;
}

.model-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.model-table th {
  text-align: left;
  padding: 8px 12px;
  border-bottom: 2px solid var(--border-color);
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.model-table td {
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

.model-table tr:hover {
  background: var(--bg-secondary);
}

.model-name {
  font-family: monospace;
  font-size: 12px;
}
</style>
