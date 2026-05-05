<template>
  <div class="contacts-view">
    <div class="contacts-header">
      <h3 class="section-label">Contacts</h3>
      <button class="add-btn" @click="showAddDialog">+ Add</button>
      <div class="search-wrap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input v-model="search" placeholder="Search..." />
      </div>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiSuggestConnect">AI Connect</button>
        <button class="ai-header-btn" @click="aiPrepareMeeting">AI Meeting</button>
      </div>
    </div>
    <div class="contacts-body">
      <div class="contacts-list">
        <div v-for="c in filteredContacts" :key="c.id" :class="['contact-card', { active: activeId === c.id }]" @click="activeId = c.id">
          <div class="contact-avatar">{{ c.name.charAt(0) }}</div>
          <div class="contact-info">
            <span class="contact-name">{{ c.name }}</span>
            <span class="contact-role">{{ c.role }}{{ c.company ? ' @ ' + c.company : '' }}</span>
          </div>
        </div>
      </div>
      <div class="contact-detail" v-if="activeContact">
        <div class="detail-header">
          <div class="detail-avatar">{{ activeContact.name.charAt(0) }}</div>
          <div>
            <h4>{{ activeContact.name }}</h4>
            <span class="detail-role">{{ activeContact.role }}{{ activeContact.company ? ' @ ' + activeContact.company : '' }}</span>
          </div>
        </div>
        <div class="detail-fields">
          <div v-if="activeContact.email" class="field"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h12a1 1 0 011 1v8a1 1 0 01-1 1H2a1 1 0 01-1-1V4a1 1 0 011-1zm0 1l6 4 6-4"/></svg><span>{{ activeContact.email }}</span></div>
          <div v-if="activeContact.phone" class="field"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg><span>{{ activeContact.phone }}</span></div>
          <div v-if="activeContact.birthday" class="field"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg><span>{{ activeContact.birthday }}</span></div>
        </div>
        <div v-if="activeContact.notes" class="detail-notes">{{ activeContact.notes }}</div>
        <div class="detail-tags"><span v-for="t in activeContact.tags" :key="t" class="tag">{{ t }}</span></div>
      </div>
      <div v-else class="contacts-empty">Select a contact</div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header"><h4>AI Contacts Assistant</h4><button class="close-btn" @click="showAIPanel = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is thinking...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.suggestions?.length" class="ai-section"><h5>Connect Suggestions</h5><div v-for="s in aiResult.suggestions" :key="s.name" class="suggestion-item"><span class="sug-name">{{ s.name }}</span><span class="sug-reason">{{ s.reason }}</span></div></div>
          <div v-if="aiResult.brief" class="ai-section"><h5>Meeting Brief</h5><div v-for="a in aiResult.brief.attendees || []" :key="a.name" class="brief-item"><span class="brief-name">{{ a.name }}</span><span class="brief-info">{{ a.key_info }}</span></div></div>
          <div v-if="aiResult.result && !aiResult.suggestions && !aiResult.brief" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>Add Contact</h4>
        <input ref="dialogInput" v-model="dialogName" class="dialog-input" placeholder="Contact name" @keydown.enter="confirmAddContact" @keydown.escape="dialogVisible = false" />
        <input v-model="dialogEmail" class="dialog-input" placeholder="Email (optional)" @keydown.enter="confirmAddContact" />
        <input v-model="dialogCompany" class="dialog-input" placeholder="Company (optional)" @keydown.enter="confirmAddContact" />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmAddContact" :disabled="!dialogName.trim()">Add</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '../../utils/api'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import type { ContactItem } from '../../types/workspace'

const contacts = ref<ContactItem[]>([])
const activeId = ref<string | null>(null)
const search = ref('')
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)

const dialogVisible = ref(false)
const dialogName = ref('')
const dialogEmail = ref('')
const dialogCompany = ref('')
const dialogInput = ref<HTMLInputElement | null>(null)

const { saveDoc, loadDoc } = useDocumentPersistence('contacts')

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', { contacts: contacts.value, updatedAt: Date.now() })
  }, 1500)
}

watch(contacts, debouncedSave, { deep: true })

onMounted(async () => {
  const saved = await loadDoc('default')
  if (saved?.contacts) contacts.value = saved.contacts as ContactItem[]
})

const activeContact = computed(() => contacts.value.find(c => c.id === activeId.value) || null)
const filteredContacts = computed(() => {
  if (!search.value) return contacts.value
  const q = search.value.toLowerCase()
  return contacts.value.filter(c => c.name.toLowerCase().includes(q) || c.email?.toLowerCase().includes(q) || c.company?.toLowerCase().includes(q))
})

function genId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }

function showAddDialog() {
  dialogName.value = ''
  dialogEmail.value = ''
  dialogCompany.value = ''
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function confirmAddContact() {
  if (!dialogName.value.trim()) return
  contacts.value.push({
    id: genId(),
    name: dialogName.value.trim(),
    email: dialogEmail.value.trim() || undefined,
    company: dialogCompany.value.trim() || undefined,
    tags: [],
  })
  activeId.value = contacts.value[contacts.value.length - 1].id
  dialogVisible.value = false
}

async function aiSuggestConnect() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/contacts/assist', { action: 'suggest_connect', params: { contacts: contacts.value.map(c => ({ name: c.name, company: c.company, role: c.role })) } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Suggestion failed.' } }
  finally { aiLoading.value = false }
}

async function aiPrepareMeeting() {
  if (!activeContact.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try { const res = await api.post('/ai/workspace/contacts/assist', { action: 'prepare_meeting', params: { attendees: [activeContact.value.name], context: `Meeting with ${activeContact.value.name}, ${activeContact.value.role} at ${activeContact.value.company}` } }); aiResult.value = res.data }
  catch { aiResult.value = { result: 'Meeting prep failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.contacts-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.contacts-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.add-btn { padding: 6px 12px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; font-size: 13px; border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.search-wrap { display: flex; align-items: center; gap: 6px; padding: 4px 8px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); }
.search-wrap input { background: none; border: none; color: var(--text-primary); font-size: 13px; outline: none; width: 120px; }
.search-wrap input::placeholder { color: var(--text-tertiary); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-md); font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.contacts-body { flex: 1; display: flex; overflow: hidden; }
.contacts-list { width: 240px; border-right: 1px solid var(--border-color); overflow-y: auto; padding: 8px; }
.contact-card { display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: var(--radius-lg); cursor: pointer; margin-bottom: 4px; }
.contact-card:hover { background: var(--bg-secondary); }
.contact-card.active { background: var(--ws-accent-light); }
.contact-avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--ws-accent); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); flex-shrink: 0; }
.contact-info { display: flex; flex-direction: column; }
.contact-name { font-size: 13px; color: var(--text-primary); }
.contact-role { font-size: 11px; color: var(--text-tertiary); }
.contact-detail { flex: 1; padding: 24px; overflow-y: auto; }
.detail-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.detail-avatar { width: 56px; height: 56px; border-radius: 50%; background: var(--ws-accent); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: var(--font-weight-semibold); }
.detail-header h4 { margin: 0; font-size: 18px; color: var(--text-primary); }
.detail-role { font-size: 13px; color: var(--text-tertiary); }
.detail-fields { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.field { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }
.field svg { color: var(--ws-accent); flex-shrink: 0; }
.detail-notes { padding: 12px; background: var(--bg-secondary); border-radius: var(--radius-lg); font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.detail-tags { display: flex; gap: 4px; flex-wrap: wrap; }
.tag { font-size: 10px; padding: 2px 8px; background: var(--ws-accent-light); color: var(--ws-accent-soft); border-radius: var(--radius-sm); }
.contacts-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); }
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
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.suggestion-item { padding: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); margin-bottom: 4px; }
.sug-name { font-size: 13px; color: var(--ws-accent-soft); display: block; }
.sug-reason { font-size: 11px; color: var(--text-tertiary); }
.brief-item { padding: 6px 8px; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 4px; }
.brief-name { font-size: 13px; color: var(--ws-accent-soft); margin-right: 8px; }
.brief-info { font-size: 12px; color: var(--text-secondary); }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 200; }
.dialog-box { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; min-width: 360px; box-shadow: var(--shadow-lg); display: flex; flex-direction: column; gap: 10px; }
.dialog-box h4 { margin: 0; font-size: 15px; color: var(--text-primary); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--input-bg); color: var(--text-primary); font-size: 14px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 3px var(--ws-accent-light); }
.dialog-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.dialog-cancel { padding: 6px 16px; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.dialog-cancel:hover { background: var(--border-color); }
.dialog-confirm { padding: 6px 16px; border-radius: var(--radius-md); background: var(--ws-accent); color: var(--bg-primary); border: none; cursor: pointer; font-size: var(--font-size-sm); }
.dialog-confirm:hover { background: var(--ws-accent-hover); }
.dialog-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
