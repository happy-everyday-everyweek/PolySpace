<template>
  <div class="dataviz-view">
    <div class="dataviz-header">
      <h2>数据可视化</h2>
      <p class="dataviz-desc">上传数据或描述需求，AI 自动生成图表</p>
    </div>
    <div class="dataviz-toolbar">
      <select v-model="chartType" class="chart-type-select">
        <option value="line">折线图</option>
        <option value="bar">柱状图</option>
        <option value="pie">饼图</option>
        <option value="scatter">散点图</option>
        <option value="radar">雷达图</option>
        <option value="heatmap">热力图</option>
      </select>
      <button class="dataviz-btn" @click="generateFromAI">AI 生成</button>
      <button class="dataviz-btn" @click="loadSampleData">示例数据</button>
      <button class="dataviz-btn" @click="exportChart">导出图片</button>
    </div>
    <div class="dataviz-content">
      <div class="dataviz-chart-area">
        <div ref="chartRef" class="chart-container" />
      </div>
      <div class="dataviz-data-area">
        <textarea
          v-model="dataInput"
          class="data-input"
          placeholder="输入 JSON 数据，例如:&#10;[&#10;  {&quot;name&quot;: &quot;一月&quot;, &quot;value&quot;: 120},&#10;  {&quot;name&quot;: &quot;二月&quot;, &quot;value&quot;: 200}&#10;]"
          rows="10"
        />
        <textarea
          v-model="aiPrompt"
          class="ai-prompt-input"
          placeholder="描述你想生成的图表，例如：展示过去6个月的销售趋势"
          rows="2"
        />
        <button class="dataviz-btn primary" @click="renderChart">渲染图表</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import api from '@/utils/api'

const chartRef = ref<HTMLElement | null>(null)
const chartType = ref('bar')
const dataInput = ref('')
const aiPrompt = ref('')
let chartInstance: any = null

function parseData() {
  try {
    return JSON.parse(dataInput.value)
  } catch {
    return null
  }
}

function buildOption(data: any[], type: string) {
  const names = data.map((d: any) => d.name || d.label || d.category || '')
  const values = data.map((d: any) => d.value || d.count || d.amount || 0)

  const baseOption: Record<string, any> = {
    tooltip: { trigger: type === 'pie' ? 'item' : 'axis' },
    backgroundColor: 'transparent',
    textStyle: { color: '#ccc' },
  }

  if (type === 'pie') {
    return {
      ...baseOption,
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.map((d: any) => ({ name: d.name || d.label, value: d.value || d.count })),
        emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } },
      }],
    }
  }

  if (type === 'scatter') {
    return {
      ...baseOption,
      xAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border-color)' } } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border-color)' } } },
      series: [{ type: 'scatter', data: data.map((d: any) => [d.x || d.name, d.y || d.value]), symbolSize: 10 }],
    }
  }

  if (type === 'radar') {
    const maxVal = Math.max(...values) * 1.2
    return {
      ...baseOption,
      radar: { indicator: names.map((n: string) => ({ name: n, max: maxVal })) },
      series: [{ type: 'radar', data: [{ value: values, name: '数据' }] }],
    }
  }

  return {
    ...baseOption,
    xAxis: { type: 'category', data: names, axisLine: { lineStyle: { color: 'var(--border-color)' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border-color)' } } },
    series: [{ type, data: values, smooth: type === 'line', areaStyle: type === 'line' ? { opacity: 0.3 } : undefined }],
  }
}

async function renderChart() {
  const data = parseData()
  if (!data || !chartRef.value) return
  await nextTick()
  try {
    const echarts = await import('echarts')
    if (chartInstance) chartInstance.dispose()
    chartInstance = echarts.init(chartRef.value)
    const option = buildOption(Array.isArray(data) ? data : [data], chartType.value)
    chartInstance.setOption(option)
  } catch (e) {
    console.error('Chart render failed:', e)
  }
}

async function generateFromAI() {
  if (!aiPrompt.value.trim()) return
  try {
    const { data } = await api.post('/ai/workspace/dataviz/assist', {
      prompt: aiPrompt.value,
      chart_type: chartType.value,
    })
    if (data.data) {
      dataInput.value = JSON.stringify(data.data, null, 2)
      await renderChart()
    }
  } catch (e) {
    console.error('AI generation failed:', e)
  }
}

function loadSampleData() {
  dataInput.value = JSON.stringify([
    { name: '一月', value: 120 },
    { name: '二月', value: 200 },
    { name: '三月', value: 150 },
    { name: '四月', value: 310 },
    { name: '五月', value: 280 },
    { name: '六月', value: 420 },
  ], null, 2)
  renderChart()
}

function exportChart() {
  if (chartInstance) {
    const url = chartInstance.getDataURL({ type: 'png', pixelRatio: 2 })
    const a = document.createElement('a')
    a.href = url
    a.download = 'chart.png'
    a.click()
  }
}

onMounted(() => {
  loadSampleData()
})

onUnmounted(() => {
  if (chartInstance) chartInstance.dispose()
})
</script>

<style scoped>
.dataviz-view {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}
.dataviz-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0 0 4px;
}
.dataviz-desc {
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 13px;
  margin: 0 0 16px;
}
.dataviz-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.chart-type-select {
  padding: 6px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  outline: none;
}
.dataviz-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-size: 13px;
  cursor: pointer;
}
.dataviz-btn.primary {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.dataviz-btn:hover { opacity: 0.9; }
.dataviz-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 16px;
}
.dataviz-chart-area {
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-primary, var(--bg-secondary));
  padding: 16px;
}
.chart-container {
  width: 100%;
  height: 400px;
}
.dataviz-data-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.data-input,
.ai-prompt-input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, #16162a);
  color: var(--text-primary, var(--text-primary));
  font-size: 12px;
  font-family: monospace;
  resize: vertical;
  outline: none;
}
.data-input:focus,
.ai-prompt-input:focus {
  border-color: var(--accent-color, #6366f1);
}
</style>
