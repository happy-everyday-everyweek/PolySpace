<template>
  <div class="artifact-renderer">
    <div class="artifact-header">
      <span class="artifact-type-badge">{{ typeLabel }}</span>
      <h3 class="artifact-title">{{ artifact.title }}</h3>
      <div class="artifact-actions">
        <button class="artifact-btn" @click="download" title="下载">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        </button>
        <button class="artifact-btn" @click="copyContent" title="复制">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
        <button class="artifact-btn" @click="$emit('close')" title="关闭">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>
    <div class="artifact-body">
      <div v-if="artifact.type === 'code'" class="artifact-code">
        <div class="code-header">
          <span class="code-lang">{{ artifact.language || 'code' }}</span>
          <button v-if="runnable" class="code-run-btn" @click="runCode">运行</button>
        </div>
        <pre><code>{{ artifact.content }}</code></pre>
      </div>
      <div v-else-if="artifact.type === 'html'" class="artifact-html">
        <iframe
          :srcdoc="artifact.content"
          sandbox="allow-scripts"
          class="html-preview"
        />
      </div>
      <div v-else-if="artifact.type === 'svg'" class="artifact-svg" v-html="artifact.content" />
      <div v-else-if="artifact.type === 'chart'" class="artifact-chart">
        <div ref="chartRef" class="chart-container" />
      </div>
      <div v-else-if="artifact.type === 'table'" class="artifact-table">
        <table>
          <thead>
            <tr>
              <th v-for="(_, key) in tableData[0] || {}" :key="key">{{ key }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in tableData" :key="i">
              <td v-for="(val, key) in row" :key="key">{{ val }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="artifact-document">
        <div class="doc-content" v-html="renderedMarkdown" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'

interface Artifact {
  id: string
  type: string
  title: string
  content: string
  language?: string
  metadata?: Record<string, unknown>
}

const props = defineProps<{ artifact: Artifact }>()
defineEmits<{ (e: 'close'): void }>()

const chartRef = ref<HTMLElement | null>(null)
const md = new MarkdownIt({ html: false, linkify: true })

const typeLabels: Record<string, string> = {
  document: '文档', code: '代码', chart: '图表', table: '表格',
  svg: '图形', html: '网页', image: '图片',
}

const typeLabel = computed(() => typeLabels[props.artifact.type] || '产出物')
const runnable = computed(() => ['python', 'javascript', 'html'].includes(props.artifact.language || ''))
const renderedMarkdown = computed(() => md.render(props.artifact.content))
const tableData = computed(() => {
  try {
    const parsed = JSON.parse(props.artifact.content)
    if (Array.isArray(parsed)) return parsed
    return [parsed]
  } catch {
    return [{ content: props.artifact.content }]
  }
})

function download() {
  const ext: Record<string, string> = {
    document: 'md', code: props.artifact.language || 'txt', chart: 'json',
    table: 'csv', svg: 'svg', html: 'html', image: 'png',
  }
  const filename = `${props.artifact.title || 'artifact'}.${ext[props.artifact.type] || 'txt'}`
  const blob = new Blob([props.artifact.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function copyContent() {
  navigator.clipboard.writeText(props.artifact.content)
}

function runCode() {
  if (props.artifact.language === 'html') {
    const win = window.open('', '_blank')
    if (win) {
      win.document.write(props.artifact.content)
      win.document.close()
    }
  }
}

onMounted(async () => {
  if (props.artifact.type === 'chart' && chartRef.value) {
    await nextTick()
    try {
      const echarts = await import('echarts')
      const chart = echarts.init(chartRef.value)
      const option = JSON.parse(props.artifact.content)
      chart.setOption(option)
      window.addEventListener('resize', () => chart.resize())
    } catch { /* ignore */ }
  }
})
</script>

<style scoped>
.artifact-renderer {
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-primary, var(--bg-secondary));
}
.artifact-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color, var(--border-color));
  gap: 10px;
}
.artifact-type-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--accent-color, #6366f1);
  color: #fff;
}
.artifact-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary, var(--text-primary));
  margin: 0;
}
.artifact-actions {
  display: flex;
  gap: 4px;
}
.artifact-btn {
  background: none;
  border: none;
  color: var(--text-secondary, var(--text-tertiary));
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}
.artifact-btn:hover {
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
}
.artifact-body {
  max-height: 400px;
  overflow: auto;
}
.artifact-code {
  position: relative;
}
.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 14px;
  background: var(--bg-secondary, #16162a);
  font-size: 12px;
}
.code-lang {
  color: var(--text-secondary, var(--text-tertiary));
}
.code-run-btn {
  background: var(--accent-color, #6366f1);
  color: #fff;
  border: none;
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
}
.code-run-btn:hover {
  opacity: 0.9;
}
.artifact-code pre {
  margin: 0;
  padding: 14px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary, var(--text-primary));
}
.artifact-html .html-preview {
  width: 100%;
  min-height: 200px;
  border: none;
  background: #fff;
}
.artifact-svg {
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.artifact-svg :deep(svg) {
  max-width: 100%;
  max-height: 300px;
}
.artifact-chart .chart-container {
  width: 100%;
  height: 300px;
}
.artifact-table {
  overflow-x: auto;
}
.artifact-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.artifact-table th,
.artifact-table td {
  padding: 8px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  text-align: left;
}
.artifact-table th {
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-weight: 500;
}
.artifact-table td {
  color: var(--text-secondary, #ccc);
}
.artifact-document .doc-content {
  padding: 16px;
  color: var(--text-primary, var(--text-primary));
  font-size: 14px;
  line-height: 1.7;
}
.artifact-document .doc-content :deep(h1),
.artifact-document .doc-content :deep(h2),
.artifact-document .doc-content :deep(h3) {
  margin-top: 16px;
  margin-bottom: 8px;
}
.artifact-document .doc-content :deep(code) {
  background: var(--bg-secondary, var(--border-color));
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}
</style>
