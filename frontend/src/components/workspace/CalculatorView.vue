<template>
  <div class="calc-view">
    <div class="calc-header">
      <h3 class="section-label">Calculator</h3>
      <div class="mode-tabs">
        <button :class="['mode-btn', { active: mode === 'basic' }]" @click="mode = 'basic'">Basic</button>
        <button :class="['mode-btn', { active: mode === 'convert' }]" @click="mode = 'convert'">Convert</button>
        <button :class="['mode-btn', { active: mode === 'ai' }]" @click="mode = 'ai'">AI</button>
      </div>
    </div>
    <div class="calc-body">
      <div v-if="mode === 'basic'" class="basic-calc">
        <div class="calc-display">
          <div class="calc-expression">{{ expression || '0' }}</div>
          <div v-if="result !== null" class="calc-result">= {{ result }}</div>
        </div>
        <div class="calc-history" v-if="history.length">
          <div v-for="(h, i) in history.slice(-5)" :key="i" class="history-item" @click="loadHistory(h)">
            <span class="history-expr">{{ h.expression }}</span>
            <span class="history-result">= {{ h.result }}</span>
          </div>
        </div>
        <div class="calc-grid">
          <button v-for="btn in buttons" :key="btn" :class="['calc-btn', { op: '+-*/'.includes(btn), eq: btn === '=' }]" @click="handleBtn(btn)">{{ btn }}</button>
        </div>
      </div>
      <div v-else-if="mode === 'convert'" class="convert-calc">
        <div class="convert-group">
          <label>From</label>
          <input v-model.number="convertFrom" type="number" />
          <select v-model="fromUnit">
            <option v-for="u in currentUnits" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="convert-arrow">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
        </div>
        <div class="convert-group">
          <label>To</label>
          <input :value="convertResult" readonly />
          <select v-model="toUnit">
            <option v-for="u in currentUnits" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="convert-category">
          <button v-for="cat in Object.keys(unitCategories)" :key="cat" :class="['cat-btn', { active: convertCategory === cat }]" @click="convertCategory = cat">{{ cat }}</button>
        </div>
      </div>
      <div v-else class="ai-calc">
        <textarea class="ai-input" v-model="aiQuery" placeholder="Ask in natural language...&#10;e.g. What is 3.5% compound interest over 10 years on 10000?"></textarea>
        <button class="ai-calc-btn" @click="aiCompute">Compute</button>
        <div v-if="aiResult" class="ai-calc-result">
          <div v-if="aiResult.result != null" class="ai-result-value">{{ aiResult.result }}</div>
          <div v-if="aiResult.steps?.length" class="ai-steps"><div v-for="(s, i) in aiResult.steps" :key="i" class="step-item">{{ s.step }}: {{ s.explanation }}</div></div>
          <div v-if="aiResult.formula_used" class="ai-formula">Formula: {{ aiResult.formula_used }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '../../utils/api'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'

const mode = ref<'basic' | 'convert' | 'ai'>('basic')
const expression = ref('')
const result = ref<number | null>(null)
const aiQuery = ref('')
const aiResult = ref<any>(null)
const convertFrom = ref(1)
const fromUnit = ref('km')
const toUnit = ref('mi')
const convertCategory = ref('length')
const history = ref<{ expression: string; result: number }[]>([])

const buttons = ['C', '(', ')', '/', '7', '8', '9', '*', '4', '5', '6', '-', '1', '2', '3', '+', '0', '.', '=']

const unitCategories: Record<string, Record<string, number>> = {
  length: { km: 1000, m: 1, cm: 0.01, mm: 0.001, mi: 1609.344, ft: 0.3048, in: 0.0254 },
  weight: { kg: 1, g: 0.001, mg: 0.000001, lb: 0.453592, oz: 0.0283495 },
  temperature: { c: 0, f: 0, k: 0 },
  volume: { l: 1, ml: 0.001, gal: 3.78541, qt: 0.946353, cup: 0.236588 },
}

const currentUnits = computed(() => Object.keys(unitCategories[convertCategory.value] || {}))

const convertResult = computed(() => {
  const cat = unitCategories[convertCategory.value]
  if (!cat) return ''
  if (convertCategory.value === 'temperature') {
    let celsius = convertFrom.value
    if (fromUnit.value === 'f') celsius = (convertFrom.value - 32) * 5 / 9
    else if (fromUnit.value === 'k') celsius = convertFrom.value - 273.15
    if (toUnit.value === 'c') return celsius.toFixed(4)
    if (toUnit.value === 'f') return (celsius * 9 / 5 + 32).toFixed(4)
    if (toUnit.value === 'k') return (celsius + 273.15).toFixed(4)
    return celsius.toFixed(4)
  }
  const baseVal = convertFrom.value * cat[fromUnit.value]
  return (baseVal / cat[toUnit.value]).toFixed(6)
})

const { saveDoc, loadDoc } = useDocumentPersistence('calculator')

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', { history: history.value.slice(-20), mode: mode.value, updatedAt: Date.now() })
  }, 1500)
}

watch([history, mode], debouncedSave, { deep: true })

onMounted(async () => {
  const saved = await loadDoc('default')
  if (saved?.history) history.value = saved.history
  if (saved?.mode) mode.value = saved.mode
})

function handleBtn(btn: string) {
  if (btn === 'C') { expression.value = ''; result.value = null; return }
  if (btn === '=') {
    try {
      const val = Function('"use strict";return (' + expression.value + ')')()
      result.value = val
      history.value.push({ expression: expression.value, result: val })
      if (history.value.length > 20) history.value.shift()
    } catch { result.value = null }
    return
  }
  expression.value += btn
}

function loadHistory(h: { expression: string; result: number }) {
  expression.value = h.expression
  result.value = h.result
}

async function aiCompute() {
  if (!aiQuery.value) return
  try { const res = await api.post('/ai/workspace/calculator/assist', { action: 'compute', params: { query: aiQuery.value } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Computation failed.' } }
}
</script>

<style scoped>
.calc-view { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.calc-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.mode-tabs { display: flex; gap: 4px; }
.mode-btn { padding: 4px 12px; border-radius: var(--radius-md); font-size: 12px; color: var(--text-tertiary); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.mode-btn.active { background: var(--ws-accent); color: #fff; border-color: var(--ws-accent); }
.calc-body { flex: 1; padding: 16px; overflow-y: auto; }
.basic-calc { max-width: 320px; margin: 0 auto; }
.calc-display { padding: 16px; background: var(--bg-secondary); border-radius: var(--radius-lg); margin-bottom: 12px; text-align: right; }
.calc-expression { font-size: 20px; color: var(--text-primary); min-height: 28px; word-break: break-all; }
.calc-result { font-size: 28px; font-weight: 300; color: var(--ws-accent); margin-top: 4px; }
.calc-history { margin-bottom: 8px; max-height: 120px; overflow-y: auto; }
.history-item { display: flex; justify-content: space-between; padding: 4px 8px; border-radius: var(--radius-sm); cursor: pointer; font-size: 12px; color: var(--text-tertiary); }
.history-item:hover { background: var(--bg-secondary); color: var(--text-secondary); }
.history-result { color: var(--ws-accent); }
.calc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }
.calc-btn { padding: 14px; border-radius: var(--radius-md); border: none; font-size: 16px; cursor: pointer; background: var(--bg-secondary); color: var(--text-primary); }
.calc-btn:hover { background: var(--bg-tertiary); }
.calc-btn.op { color: var(--ws-accent); }
.calc-btn.eq { background: var(--ws-accent); color: var(--bg-primary); }
.calc-btn.eq:hover { background: var(--ws-accent-hover); }
.convert-calc { max-width: 400px; margin: 0 auto; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.convert-group { width: 100%; display: flex; flex-direction: column; gap: 6px; }
.convert-group label { font-size: 12px; color: var(--text-tertiary); }
.convert-group input { padding: 10px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-primary); font-size: 16px; outline: none; }
.convert-group input:focus { border-color: var(--ws-accent); }
.convert-group select { padding: 8px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-primary); font-size: 13px; outline: none; }
.convert-arrow { color: var(--ws-accent); }
.convert-category { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; margin-top: 12px; }
.cat-btn { padding: 4px 12px; border-radius: var(--radius-md); font-size: 12px; color: var(--text-tertiary); background: none; border: 1px solid var(--border-color); cursor: pointer; text-transform: capitalize; }
.cat-btn.active { background: var(--ws-accent); color: var(--bg-primary); border-color: var(--ws-accent); }
.ai-calc { max-width: 500px; margin: 0 auto; }
.ai-input { width: 100%; min-height: 80px; padding: 12px; background: var(--input-bg); border: 1px solid var(--border-color); border-radius: var(--radius-lg); color: var(--text-primary); font-size: 14px; outline: none; resize: vertical; font-family: inherit; }
.ai-input::placeholder { color: var(--text-tertiary); }
.ai-input:focus { border-color: var(--ws-accent); }
.ai-calc-btn { width: 100%; padding: 10px; background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-md); font-size: 14px; cursor: pointer; margin-top: 8px; }
.ai-calc-btn:hover { background: var(--ws-accent-hover); }
.ai-calc-result { margin-top: 16px; padding: 12px; background: var(--bg-secondary); border-radius: var(--radius-lg); }
.ai-result-value { font-size: 24px; font-weight: 600; color: var(--ws-accent); margin-bottom: 8px; }
.ai-steps { margin-top: 8px; }
.step-item { font-size: 12px; color: var(--text-secondary); padding: 4px 0; }
.ai-formula { font-size: 12px; color: var(--ws-accent-soft); margin-top: 8px; font-family: monospace; }
</style>
