<template>
  <div class="settings-section audit-section">
    <h2 class="section-title">审计日志</h2>

    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总记录数</div>
      </div>
      <div class="stat-card stat-warn">
        <div class="stat-value">{{ stats.by_level?.warn || 0 }}</div>
        <div class="stat-label">警告</div>
      </div>
      <div class="stat-card stat-error">
        <div class="stat-value">{{ stats.by_level?.error || 0 }}</div>
        <div class="stat-label">错误</div>
      </div>
      <div class="stat-card stat-ok">
        <div class="stat-value">{{ stats.by_status?.success || 0 }}</div>
        <div class="stat-label">成功</div>
      </div>
    </div>

    <div class="filter-bar">
      <select v-model="filterCategory" @change="applyFilter" class="filter-select">
        <option value="">全部分类</option>
        <option v-for="cat in categories" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
      </select>
      <select v-model="filterLevel" @change="applyFilter" class="filter-select">
        <option value="">全部级别</option>
        <option value="info">INFO</option>
        <option value="warn">WARN</option>
        <option value="error">ERROR</option>
        <option value="critical">CRITICAL</option>
      </select>
      <select v-model="filterStatus" @change="applyFilter" class="filter-select">
        <option value="">全部状态</option>
        <option value="success">成功</option>
        <option value="error">失败</option>
        <option value="timeout">超时</option>
      </select>
      <input
        type="text"
        v-model="filterDevice"
        placeholder="设备ID"
        class="filter-input"
        @keyup.enter="applyFilter"
      />
      <button class="btn btn-primary" @click="applyFilter">查询</button>
      <button class="btn btn-secondary" @click="runIntegrityCheck">完整性校验</button>
    </div>

    <div v-if="integrityResult" class="integrity-result" :class="{ 'integrity-ok': integrityResult.integrity_rate >= 0.99, 'integrity-fail': integrityResult.integrity_rate < 0.99 }">
      完整性校验: {{ (integrityResult.integrity_rate * 100).toFixed(2) }}% ({{ integrityResult.verified }}/{{ integrityResult.total }} 通过)
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error-msg">{{ error }}</div>
    <div v-else-if="logs.length === 0" class="empty-msg">暂无审计记录</div>

    <div v-else class="audit-table-wrap">
      <table class="audit-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>分类</th>
            <th>级别</th>
            <th>操作</th>
            <th>操作者</th>
            <th>源设备</th>
            <th>目标设备</th>
            <th>状态</th>
            <th>耗时</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id" @click="selectLog(log)" class="audit-row" :class="'level-' + log.level">
            <td class="td-time">{{ formatTime(log.timestamp) }}</td>
            <td><span class="badge badge-category">{{ log.category }}</span></td>
            <td><span class="badge" :class="'badge-' + log.level">{{ log.level }}</span></td>
            <td class="td-action">{{ log.action }}</td>
            <td>{{ log.actor_type }}:{{ log.actor_id ? log.actor_id.substring(0, 8) : '-' }}</td>
            <td>{{ log.source_device_id ? log.source_device_id.substring(0, 8) : '-' }}</td>
            <td>{{ log.target_device_id ? log.target_device_id.substring(0, 8) : '-' }}</td>
            <td><span class="badge" :class="log.status === 'success' ? 'badge-success' : 'badge-error'">{{ log.status }}</span></td>
            <td>{{ log.duration_ms != null ? log.duration_ms.toFixed(1) + 'ms' : '-' }}</td>
            <td class="td-detail">
              <button class="btn-link" @click.stop="showDetail(log)">查看</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination" v-if="totalCount > pageSize">
      <button class="btn btn-secondary" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button class="btn btn-secondary" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</button>
    </div>

    <div v-if="selectedLog" class="detail-overlay" @click.self="selectedLog = null">
      <div class="detail-panel">
        <div class="detail-header">
          <h3>审计记录详情</h3>
          <button class="btn-close" @click="selectedLog = null">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
        <div class="detail-body">
          <div class="detail-row"><span class="detail-key">ID</span><span class="detail-val">{{ selectedLog.id }}</span></div>
          <div class="detail-row"><span class="detail-key">Trace ID</span><span class="detail-val"><button class="btn-link" @click="viewTrace(selectedLog.trace_id)">{{ selectedLog.trace_id }}</button></span></div>
          <div class="detail-row"><span class="detail-key">Span ID</span><span class="detail-val">{{ selectedLog.span_id }}</span></div>
          <div class="detail-row"><span class="detail-key">Parent Span</span><span class="detail-val">{{ selectedLog.parent_span_id || '-' }}</span></div>
          <div class="detail-row"><span class="detail-key">时间</span><span class="detail-val">{{ selectedLog.timestamp }}</span></div>
          <div class="detail-row"><span class="detail-key">分类</span><span class="detail-val">{{ selectedLog.category }}</span></div>
          <div class="detail-row"><span class="detail-key">级别</span><span class="detail-val">{{ selectedLog.level }}</span></div>
          <div class="detail-row"><span class="detail-key">操作</span><span class="detail-val">{{ selectedLog.action }}</span></div>
          <div class="detail-row"><span class="detail-key">操作者</span><span class="detail-val">{{ selectedLog.actor_type }}:{{ selectedLog.actor_id }}</span></div>
          <div class="detail-row"><span class="detail-key">IP</span><span class="detail-val">{{ selectedLog.actor_ip || '-' }}</span></div>
          <div class="detail-row"><span class="detail-key">源设备</span><span class="detail-val">{{ selectedLog.source_device_id || '-' }} ({{ selectedLog.source_platform || '-' }})</span></div>
          <div class="detail-row"><span class="detail-key">目标设备</span><span class="detail-val">{{ selectedLog.target_device_id || '-' }} ({{ selectedLog.target_platform || '-' }})</span></div>
          <div class="detail-row"><span class="detail-key">资源</span><span class="detail-val">{{ selectedLog.resource_type }}:{{ selectedLog.resource_id }}</span></div>
          <div class="detail-row"><span class="detail-key">状态</span><span class="detail-val">{{ selectedLog.status }}</span></div>
          <div class="detail-row"><span class="detail-key">耗时</span><span class="detail-val">{{ selectedLog.duration_ms != null ? selectedLog.duration_ms + 'ms' : '-' }}</span></div>
          <div class="detail-row" v-if="selectedLog.request_summary"><span class="detail-key">请求摘要</span><span class="detail-val detail-pre">{{ selectedLog.request_summary }}</span></div>
          <div class="detail-row" v-if="selectedLog.response_summary"><span class="detail-key">响应摘要</span><span class="detail-val detail-pre">{{ selectedLog.response_summary }}</span></div>
          <div class="detail-row" v-if="selectedLog.detail"><span class="detail-key">详情</span><span class="detail-val detail-pre">{{ formatDetail(selectedLog.detail) }}</span></div>
          <div class="detail-row"><span class="detail-key">校验和</span><span class="detail-val">{{ selectedLog.checksum ? selectedLog.checksum.substring(0, 16) + '...' : '-' }}</span></div>
        </div>
      </div>
    </div>

    <div v-if="traceChain" class="detail-overlay" @click.self="traceChain = null">
      <div class="detail-panel">
        <div class="detail-header">
          <h3>链路追踪: {{ traceChain.trace_id }}</h3>
          <button class="btn-close" @click="traceChain = null">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>
        <div class="detail-body">
          <div v-for="(span, idx) in traceChain.spans" :key="span.span_id" class="trace-step">
            <div class="trace-connector" v-if="idx > 0"></div>
            <div class="trace-node">
              <div class="trace-idx">#{{ idx + 1 }}</div>
              <div class="trace-info">
                <div class="trace-action">{{ span.action }}</div>
                <div class="trace-meta">
                  <span class="badge badge-category">{{ span.category }}</span>
                  <span class="badge" :class="span.status === 'success' ? 'badge-success' : 'badge-error'">{{ span.status }}</span>
                  <span v-if="span.duration_ms">{{ span.duration_ms }}ms</span>
                  <span v-if="span.source_device_id">from:{{ span.source_device_id?.substring(0, 8) }}</span>
                  <span v-if="span.target_device_id">to:{{ span.target_device_id?.substring(0, 8) }}</span>
                </div>
                <div class="trace-time">{{ span.timestamp }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAudit } from '@/composables/useAudit'
import type { AuditLogEntry, IntegrityResult } from '@/composables/useAudit'

const { logs, stats, loading, error, totalCount, fetchLogs, fetchStats, fetchTraceChain, verifyIntegrity } = useAudit()

const filterCategory = ref('')
const filterLevel = ref('')
const filterStatus = ref('')
const filterDevice = ref('')
const currentPage = ref(1)
const pageSize = 50
const selectedLog = ref<AuditLogEntry | null>(null)
const traceChain = ref<{ trace_id: string; spans: any[] } | null>(null)
const integrityResult = ref<IntegrityResult | null>(null)

const categories = [
  { value: 'api_request', label: 'API请求' },
  { value: 'device_connect', label: '设备连接' },
  { value: 'device_disconnect', label: '设备断开' },
  { value: 'device_execute', label: '远程执行' },
  { value: 'device_broadcast', label: '设备广播' },
  { value: 'device_capability', label: '能力更新' },
  { value: 'sync_push', label: '同步推送' },
  { value: 'sync_pull', label: '同步拉取' },
  { value: 'sync_conflict', label: '同步冲突' },
  { value: 'tool_call', label: '工具调用' },
  { value: 'tool_register', label: '工具注册' },
  { value: 'tool_unregister', label: '工具注销' },
  { value: 'agent_run', label: '智能体运行' },
  { value: 'agent_tool_call', label: '智能体工具调用' },
  { value: 'policy_evaluate', label: '策略评估' },
  { value: 'policy_block', label: '策略拦截' },
  { value: 'policy_confirm', label: '策略确认' },
  { value: 'memory_write', label: '记忆写入' },
  { value: 'memory_read', label: '记忆读取' },
  { value: 'memory_consolidate', label: '记忆巩固' },
  { value: 'websocket', label: 'WebSocket' },
]

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize))

function formatTime(ts: string | null): string {
  if (!ts) return '-'
  try {
    const d = new Date(ts)
    return d.toLocaleString('zh-CN', { hour12: false })
  } catch {
    return ts
  }
}

function formatDetail(detail: string): string {
  try {
    const parsed = JSON.parse(detail)
    return JSON.stringify(parsed, null, 2)
  } catch {
    return detail
  }
}

function applyFilter() {
  currentPage.value = 1
  loadLogs()
}

function goPage(page: number) {
  currentPage.value = page
  loadLogs()
}

function loadLogs() {
  fetchLogs({
    category: filterCategory.value || undefined,
    level: filterLevel.value || undefined,
    status: filterStatus.value || undefined,
    source_device_id: filterDevice.value || undefined,
    limit: pageSize,
    offset: (currentPage.value - 1) * pageSize,
  })
}

function selectLog(log: AuditLogEntry) {
  selectedLog.value = log
}

function showDetail(log: AuditLogEntry) {
  selectedLog.value = log
}

async function viewTrace(traceId: string) {
  selectedLog.value = null
  const result = await fetchTraceChain(traceId)
  if (result) {
    traceChain.value = result
  }
}

async function runIntegrityCheck() {
  integrityResult.value = await verifyIntegrity()
}

onMounted(() => {
  fetchStats()
  loadLogs()
})
</script>

<style scoped>
.audit-section {
  max-width: 100%;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 16px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-color);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stat-warn .stat-value { color: #f59e0b; }
.stat-error .stat-value { color: #ef4444; }
.stat-ok .stat-value { color: #10b981; }

.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-select, .filter-input {
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--input-bg);
  color: var(--text-color);
  font-size: 13px;
}

.filter-input {
  width: 140px;
}

.btn {
  padding: 6px 14px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  transition: background var(--transition-normal);
}

.btn-primary {
  background: var(--primary-color);
  color: #fff;
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text-color);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--border-color);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.integrity-result {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 500;
}

.integrity-ok {
  background: #ecfdf5;
  color: #065f46;
}

.integrity-fail {
  background: #fef2f2;
  color: #991b1b;
}

.loading, .empty-msg, .error-msg {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 14px;
}

.error-msg {
  color: #ef4444;
}

.audit-table-wrap {
  overflow-x: auto;
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.audit-table th {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 2px solid var(--border-color);
  color: var(--text-secondary);
  font-weight: 600;
  white-space: nowrap;
}

.audit-table td {
  padding: 6px 10px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.audit-row {
  cursor: pointer;
  transition: background var(--transition-fast);
}

.audit-row:hover {
  background: var(--bg-secondary);
}

.audit-row.level-error {
  background: #fef2f2;
}

.audit-row.level-warn {
  background: #fffbeb;
}

.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
}

.badge-category {
  background: #eef2ff;
  color: #4338ca;
}

.badge-info {
  background: #eff6ff;
  color: #1d4ed8;
}

.badge-warn {
  background: #fffbeb;
  color: #b45309;
}

.badge-error {
  background: #fef2f2;
  color: #dc2626;
}

.badge-critical {
  background: #7f1d1d;
  color: #fff;
}

.badge-success {
  background: #ecfdf5;
  color: #065f46;
}

.td-time {
  font-family: monospace;
  font-size: 11px;
}

.td-action {
  font-family: monospace;
}

.btn-link {
  color: var(--primary-color);
  font-size: 12px;
  cursor: pointer;
  background: none;
  border: none;
  text-decoration: underline;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}

.page-info {
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-panel {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  animation: scaleIn var(--transition-smooth);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.detail-header h3 {
  font-size: 16px;
  font-weight: 600;
}

.btn-close {
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
}

.detail-body {
  padding: 16px 20px;
}

.detail-row {
  display: flex;
  padding: 6px 0;
  border-bottom: 1px solid var(--bg-secondary);
  font-size: 13px;
}

.detail-key {
  width: 100px;
  flex-shrink: 0;
  color: var(--text-secondary);
  font-weight: 500;
}

.detail-val {
  flex: 1;
  word-break: break-all;
}

.detail-pre {
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  background: var(--bg-secondary);
  padding: 8px;
  border-radius: var(--radius-sm);
  max-height: 200px;
  overflow-y: auto;
}

.trace-step {
  position: relative;
}

.trace-connector {
  width: 2px;
  height: 20px;
  background: var(--border-color);
  margin-left: 16px;
}

.trace-node {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.trace-idx {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary-color);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.trace-info {
  flex: 1;
}

.trace-action {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.trace-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.trace-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  font-family: monospace;
}
</style>
