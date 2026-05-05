<template>
  <div class="research-view">
    <div class="research-header">
      <h2>深度研究</h2>
      <p class="research-desc">AI 驱动的多步骤研究，自动搜索、分析、综合</p>
    </div>
    <div v-if="!currentResearch" class="research-start">
      <div class="research-input-wrap">
        <textarea
          v-model="query"
          class="research-input"
          placeholder="输入你想研究的主题..."
          rows="3"
          @keydown.ctrl.enter="startResearch"
        />
        <button class="research-start-btn" :disabled="!query.trim() || loading" @click="startResearch">
          {{ loading ? '规划中...' : '开始研究' }}
        </button>
      </div>
    </div>
    <div v-else class="research-progress">
      <div class="research-query">
        <h3>{{ currentResearch.query }}</h3>
        <span class="research-phase" :class="'phase-' + currentResearch.phase">{{ phaseLabel }}</span>
      </div>
      <div v-if="currentResearch.plan.length" class="research-plan">
        <h4>研究计划</h4>
        <div v-for="(step, i) in currentResearch.plan" :key="i" class="research-step">
          <span class="step-num">{{ i + 1 }}</span>
          <span class="step-query">{{ step.query }}</span>
          <span class="step-reason">{{ step.reason }}</span>
          <button class="step-exec-btn" @click="executeStep(i)" :disabled="stepLoading">
            {{ stepLoading ? '执行中...' : '执行' }}
          </button>
        </div>
      </div>
      <div v-if="currentResearch.sources.length" class="research-sources">
        <h4>信息来源 ({{ currentResearch.sources.length }})</h4>
        <div v-for="(src, i) in currentResearch.sources" :key="i" class="research-source">
          <span class="source-type">{{ src.type }}</span>
          <span class="source-content">{{ src.title || src.content || src.snippet || '' }}</span>
        </div>
      </div>
      <div v-if="currentResearch.findings.length" class="research-findings">
        <h4>研究发现</h4>
        <div v-for="(f, i) in currentResearch.findings" :key="i" class="research-finding">
          <span class="finding-text">{{ f.finding }}</span>
          <span class="finding-confidence">置信度: {{ (f.confidence * 100).toFixed(0) }}%</span>
        </div>
      </div>
      <div v-if="currentResearch.report" class="research-report">
        <h4>研究报告</h4>
        <div class="report-content" v-html="renderedReport" />
      </div>
      <div v-if="currentResearch.gaps.length" class="research-gaps">
        <h4>信息缺口</h4>
        <div v-for="(gap, i) in currentResearch.gaps" :key="i" class="research-gap">
          {{ gap }}
        </div>
      </div>
      <div class="research-actions">
        <button v-if="currentResearch.plan.length && !currentResearch.report" class="research-btn primary" @click="executeAllSteps" :disabled="stepLoading">
          执行所有步骤
        </button>
        <button v-if="currentResearch.findings.length && !currentResearch.report" class="research-btn primary" @click="synthesize" :disabled="stepLoading">
          生成报告
        </button>
        <button v-if="currentResearch.phase === 'iterating'" class="research-btn" @click="synthesize" :disabled="stepLoading">
          继续迭代
        </button>
        <button class="research-btn" @click="resetResearch">新研究</button>
      </div>
    </div>
    <div v-if="researchHistory.length" class="research-history">
      <h4>研究历史</h4>
      <div v-for="r in researchHistory" :key="r.id" class="history-item" @click="loadResearch(r)">
        <span class="history-query">{{ r.query }}</span>
        <span class="history-phase">{{ r.phase }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '@/utils/api'

const md = new MarkdownIt({ html: false, linkify: true })

const query = ref('')
const loading = ref(false)
const stepLoading = ref(false)
const currentResearch = ref<any>(null)
const researchHistory = ref<any[]>([])

const phaseLabels: Record<string, string> = {
  planning: '规划中', searching: '搜索中', analyzing: '分析中',
  synthesizing: '综合中', iterating: '迭代中', completed: '已完成', failed: '失败',
}

const phaseLabel = computed(() => phaseLabels[currentResearch.value?.phase] || '')
const renderedReport = computed(() => currentResearch.value?.report ? md.render(currentResearch.value.report) : '')

async function startResearch() {
  if (!query.value.trim()) return
  loading.value = true
  try {
    const { data } = await api.post('/ai/research', { query: query.value, max_iterations: 3 })
    currentResearch.value = data
  } catch (e) {
    console.error('Failed to start research:', e)
  } finally {
    loading.value = false
  }
}

async function executeStep(index: number) {
  if (!currentResearch.value) return
  stepLoading.value = true
  try {
    await api.post(`/ai/research/${currentResearch.value.id}/step`, { step_index: index })
    const { data } = await api.get(`/ai/research/${currentResearch.value.id}`)
    currentResearch.value = data
  } catch (e) {
    console.error('Failed to execute step:', e)
  } finally {
    stepLoading.value = false
  }
}

async function executeAllSteps() {
  if (!currentResearch.value) return
  for (let i = 0; i < currentResearch.value.plan.length; i++) {
    await executeStep(i)
  }
}

async function synthesize() {
  if (!currentResearch.value) return
  stepLoading.value = true
  try {
    const { data } = await api.post(`/ai/research/${currentResearch.value.id}/synthesize`)
    currentResearch.value = data
  } catch (e) {
    console.error('Failed to synthesize:', e)
  } finally {
    stepLoading.value = false
  }
}

function resetResearch() {
  if (currentResearch.value) {
    researchHistory.value.unshift(currentResearch.value)
  }
  currentResearch.value = null
  query.value = ''
}

function loadResearch(r: any) {
  currentResearch.value = r
}
</script>

<style scoped>
.research-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
.research-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 4px;
}
.research-desc {
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 13px;
  margin: 0 0 20px;
}
.research-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.research-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 14px;
  resize: vertical;
  outline: none;
}
.research-input:focus {
  border-color: var(--accent-color, #6366f1);
}
.research-start-btn {
  align-self: flex-end;
  padding: 8px 24px;
  background: var(--accent-color, #6366f1);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.research-start-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.research-query {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}
.research-query h3 {
  font-size: 16px;
  color: var(--text-primary, var(--text-primary));
  margin: 0;
  flex: 1;
}
.research-phase {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-secondary, var(--text-tertiary));
}
.phase-completed { background: #166534; color: #4ade80; }
.phase-failed { background: #7f1d1d; color: #f87171; }
.research-plan, .research-sources, .research-findings, .research-report, .research-gaps {
  margin-bottom: 16px;
}
.research-plan h4, .research-sources h4, .research-findings h4, .research-report h4, .research-gaps h4 {
  font-size: 14px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 8px;
}
.research-step {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  margin-bottom: 6px;
}
.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-color, #6366f1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}
.step-query {
  font-size: 13px;
  color: var(--text-primary, var(--text-primary));
  flex: 1;
}
.step-reason {
  font-size: 12px;
  color: var(--text-secondary, var(--text-tertiary));
}
.step-exec-btn {
  padding: 4px 12px;
  background: var(--bg-tertiary, #1e1e3a);
  color: var(--text-primary, var(--text-primary));
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.step-exec-btn:disabled { opacity: 0.5; }
.research-source, .research-finding, .research-gap {
  padding: 8px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  margin-bottom: 4px;
  font-size: 13px;
  color: var(--text-secondary, #ccc);
}
.source-type {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--bg-tertiary, #1e1e3a);
  color: var(--text-secondary, var(--text-tertiary));
  margin-right: 8px;
}
.finding-text { color: var(--text-primary, var(--text-primary)); }
.finding-confidence { float: right; font-size: 12px; color: var(--text-secondary, var(--text-tertiary)); }
.report-content {
  padding: 16px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 14px;
  line-height: 1.7;
}
.research-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}
.research-btn {
  padding: 8px 16px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  cursor: pointer;
}
.research-btn.primary {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.research-btn:disabled { opacity: 0.5; }
.research-history {
  margin-top: 24px;
  border-top: 1px solid var(--border-color, var(--border-color));
  padding-top: 16px;
}
.research-history h4 {
  font-size: 14px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 8px;
}
.history-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  margin-bottom: 4px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary, #ccc);
}
.history-item:hover {
  background: var(--bg-secondary, var(--border-color));
}
</style>
