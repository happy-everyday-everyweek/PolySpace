<template>
  <div class="finance-view">
    <div class="finance-header">
      <h3 class="section-label">Finance</h3>
      <button class="add-btn" @click="showAddDialog">+ Transaction</button>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiBudgetCheck">AI Budget</button>
        <button class="ai-header-btn" @click="aiReport">AI Report</button>
        <button class="ai-header-btn" @click="aiForecast">AI Forecast</button>
      </div>
    </div>
    <div class="finance-body">
      <div class="finance-summary">
        <div class="summary-card income">
          <span class="summary-label">Income</span>
          <span class="summary-amount">{{ totalIncome.toFixed(2) }}</span>
        </div>
        <div class="summary-card expense">
          <span class="summary-label">Expense</span>
          <span class="summary-amount">{{ totalExpense.toFixed(2) }}</span>
        </div>
        <div class="summary-card balance">
          <span class="summary-label">Balance</span>
          <span class="summary-amount" :class="{ negative: balance < 0 }">{{ balance.toFixed(2) }}</span>
        </div>
      </div>
      <div class="transaction-list">
        <div v-for="t in sortedTransactions" :key="t.id" class="transaction-item">
          <div class="txn-left">
            <span :class="['txn-type', t.type]">{{ t.type === 'income' ? '+' : '-' }}</span>
            <div class="txn-info">
              <span class="txn-desc">{{ t.description }}</span>
              <span class="txn-category">{{ t.category }}</span>
            </div>
          </div>
          <div class="txn-right">
            <span :class="['txn-amount', t.type]">{{ t.type === 'income' ? '+' : '-' }}{{ t.amount.toFixed(2) }}</span>
            <span class="txn-date">{{ t.date }}</span>
          </div>
        </div>
        <p v-if="!transactions.length" class="no-txn">No transactions yet</p>
      </div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Finance Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is analyzing...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.alerts?.length" class="ai-section"><h5>Budget Alerts</h5><div v-for="a in aiResult.alerts" :key="a.category" class="alert-item"><span class="alert-cat">{{ a.category }}</span><span class="alert-detail">{{ a.spent?.toFixed(0) }}/{{ a.budget?.toFixed(0) }} ({{ a.percentage?.toFixed(0) }}%)</span></div></div>
          <div v-if="aiResult.summary" class="ai-section"><h5>Financial Report</h5><p class="report-text">{{ aiResult.summary }}</p><div v-if="aiResult.expenses?.length" class="expense-breakdown"><div v-for="e in aiResult.expenses" :key="e.category" class="breakdown-item"><span>{{ e.category }}</span><span>{{ e.amount?.toFixed(2) }}</span></div></div></div>
          <div v-if="aiResult.forecast?.length" class="ai-section"><h5>Forecast</h5><div v-for="f in aiResult.forecast" :key="f.month" class="forecast-item"><span>{{ f.month }}</span><span>In: {{ f.projected_income?.toFixed(0) }} Out: {{ f.projected_expenses?.toFixed(0) }}</span></div></div>
          <div v-if="aiResult.result && !aiResult.alerts && !aiResult.summary && !aiResult.forecast" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>Add Transaction</h4>
        <div class="dialog-row">
          <label>Type</label>
          <div class="type-toggle">
            <button :class="['type-opt', { active: dialogType === 'income' }]" @click="dialogType = 'income'">Income</button>
            <button :class="['type-opt', { active: dialogType === 'expense' }]" @click="dialogType = 'expense'">Expense</button>
          </div>
        </div>
        <input ref="dialogInput" v-model="dialogDesc" class="dialog-input" placeholder="Description" @keydown.enter="confirmAdd" @keydown.escape="dialogVisible = false" />
        <input v-model.number="dialogAmount" class="dialog-input" type="number" min="0" step="0.01" placeholder="Amount" @keydown.enter="confirmAdd" />
        <input v-model="dialogCategory" class="dialog-input" :placeholder="dialogType === 'income' ? 'Category (e.g. salary)' : 'Category (e.g. food)'" @keydown.enter="confirmAdd" />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmAdd" :disabled="!dialogDesc.trim() || !dialogAmount || dialogAmount <= 0">Add</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import api from '../../utils/api'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import type { FinanceTransaction } from '../../types/workspace'

const transactions = ref<FinanceTransaction[]>([])
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

const dialogVisible = ref(false)
const dialogDesc = ref('')
const dialogAmount = ref<number | null>(null)
const dialogCategory = ref('')
const dialogType = ref<'income' | 'expense'>('expense')
const dialogInput = ref<HTMLInputElement | null>(null)

const { saveDoc, loadDoc } = useDocumentPersistence('finance')

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', { transactions: transactions.value, updatedAt: Date.now() })
  }, 1500)
}

watch(transactions, debouncedSave, { deep: true })

onMounted(async () => {
  const saved = await loadDoc('default')
  if (saved?.transactions) transactions.value = saved.transactions as FinanceTransaction[]
})

const totalIncome = computed(() => transactions.value.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0))
const totalExpense = computed(() => transactions.value.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0))
const balance = computed(() => totalIncome.value - totalExpense.value)
const sortedTransactions = computed(() => [...transactions.value].sort((a, b) => b.date.localeCompare(a.date)))

function genId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }

function showAddDialog() {
  dialogDesc.value = ''
  dialogAmount.value = null
  dialogCategory.value = ''
  dialogType.value = 'expense'
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function confirmAdd() {
  if (!dialogDesc.value.trim() || !dialogAmount.value || dialogAmount.value <= 0) return
  transactions.value.push({
    id: genId(),
    type: dialogType.value,
    amount: dialogAmount.value,
    category: dialogCategory.value.trim() || (dialogType.value === 'income' ? 'salary' : 'food'),
    description: dialogDesc.value.trim(),
    date: new Date().toISOString().slice(0, 10),
    tags: [],
  })
  dialogVisible.value = false
}

async function aiBudgetCheck() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/finance/assist', { action: 'budget_check', params: { transactions: transactions.value.slice(-30) } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Budget check failed.' } }
  finally { aiLoading.value = false }
}

async function aiReport() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/finance/assist', { action: 'report', params: { transactions: transactions.value } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Report failed.' } }
  finally { aiLoading.value = false }
}

async function aiForecast() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/finance/assist', { action: 'forecast', params: { transactions: transactions.value.slice(-60) } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Forecast failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.finance-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.finance-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.add-btn { padding: 6px 12px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; font-size: 13px; border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-md); font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.finance-body { flex: 1; overflow-y: auto; padding: 16px; }
.finance-summary { display: flex; gap: 12px; margin-bottom: 20px; }
.summary-card { flex: 1; padding: 16px; background: var(--bg-secondary); border-radius: var(--radius-lg); display: flex; flex-direction: column; gap: 4px; }
.summary-label { font-size: 12px; color: var(--text-tertiary); }
.summary-amount { font-size: 22px; font-weight: 600; }
.summary-card.income .summary-amount { color: var(--ws-success); }
.summary-card.expense .summary-amount { color: var(--ws-danger); }
.summary-card.balance .summary-amount { color: var(--ws-accent); }
.summary-amount.negative { color: var(--ws-danger); }
.transaction-list { display: flex; flex-direction: column; gap: 4px; }
.transaction-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: var(--bg-secondary); border-radius: var(--radius-lg); }
.txn-left { display: flex; align-items: center; gap: 10px; }
.txn-type { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; }
.txn-type.income { background: var(--ws-accent-light); color: var(--ws-success); }
.txn-type.expense { background: var(--ws-accent-light); color: var(--ws-danger); }
.txn-info { display: flex; flex-direction: column; }
.txn-desc { font-size: 13px; color: var(--text-primary); }
.txn-category { font-size: 11px; color: var(--text-tertiary); }
.txn-right { display: flex; flex-direction: column; align-items: flex-end; }
.txn-amount { font-size: 14px; font-weight: 600; }
.txn-amount.income { color: var(--ws-success); }
.txn-amount.expense { color: var(--ws-danger); }
.txn-date { font-size: 11px; color: var(--text-tertiary); }
.no-txn { color: var(--text-tertiary); text-align: center; padding: 24px; }
.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.alert-item { padding: 6px 8px; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 4px; display: flex; justify-content: space-between; }
.alert-cat { font-size: 12px; color: var(--ws-accent-soft); }
.alert-detail { font-size: 12px; color: var(--text-secondary); }
.report-text { font-size: 13px; line-height: 1.6; color: var(--text-secondary); padding: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); }
.expense-breakdown { margin-top: 8px; }
.breakdown-item { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); padding: 4px 8px; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 2px; }
.forecast-item { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-secondary); padding: 6px 8px; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 4px; }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 200; }
.dialog-box { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; min-width: 360px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px; }
.dialog-box h4 { margin: 0; font-size: 15px; color: var(--text-primary); }
.dialog-row { display: flex; align-items: center; gap: 8px; }
.dialog-row label { font-size: 12px; color: var(--text-tertiary); min-width: 50px; }
.type-toggle { display: flex; gap: 4px; }
.type-opt { padding: 4px 12px; border-radius: var(--radius-md); font-size: 12px; border: 1px solid var(--border-color); background: none; color: var(--text-tertiary); cursor: pointer; }
.type-opt.active { background: var(--ws-accent); color: #fff; border-color: var(--ws-accent); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--input-bg); color: var(--text-primary); font-size: 14px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 3px var(--ws-accent-light); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.dialog-cancel { padding: 6px 16px; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.dialog-cancel:hover { background: var(--border-color); }
.dialog-confirm { padding: 6px 16px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; border: none; cursor: pointer; font-size: 13px; }
.dialog-confirm:hover { background: var(--ws-accent-hover); }
.dialog-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
