<template>
  <div class="notes-editor">
    <div class="notes-sidebar">
      <div class="sidebar-header">
        <h3>Notes</h3>
        <button class="add-btn" @click="createNote" title="New Note">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>
      <div class="search-box">
        <input v-model="searchQuery" placeholder="Search notes..." class="search-input" />
      </div>
      <div class="note-list">
        <div
          v-for="note in filteredNotes"
          :key="note.id"
          :class="['note-item', { active: activeNoteId === note.id }]"
          @click="selectNote(note.id)"
        >
          <div class="note-item-header">
            <h4>{{ note.title || 'Untitled' }}</h4>
            <button class="delete-btn" @click.stop="deleteNote(note.id)" title="Delete">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <p class="note-preview">{{ note.content.substring(0, 80) }}</p>
          <div class="note-meta">
            <span class="note-date">{{ formatDate(note.updatedAt) }}</span>
            <div class="note-tags">
              <span v-for="tag in note.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
        <div v-if="filteredNotes.length === 0" class="empty-list">
          <p>{{ searchQuery ? 'No matching notes' : 'No notes yet' }}</p>
        </div>
      </div>
    </div>
    <div class="notes-main" v-if="activeNote">
      <div class="notes-toolbar">
        <input v-model="activeNote.title" class="note-title-input" placeholder="Note title" @input="onNoteChange" />
        <div class="view-toggle">
          <button :class="['toggle-btn', { active: viewMode === 'edit' }]" @click="viewMode = 'edit'">Edit</button>
          <button :class="['toggle-btn', { active: viewMode === 'preview' }]" @click="viewMode = 'preview'">Preview</button>
          <button :class="['toggle-btn', { active: viewMode === 'split' }]" @click="viewMode = 'split'">Split</button>
        </div>
        <div class="tags-area">
          <span v-for="tag in activeNote.tags" :key="tag" class="tag removable">
            {{ tag }}
            <button class="tag-remove" @click="removeTag(tag)">&times;</button>
          </span>
          <input
            v-model="newTag"
            class="tag-input"
            placeholder="+ tag"
            @keydown.enter="addTag"
          />
        </div>
        <div class="ai-group">
          <button class="ai-btn" @click="aiAction('auto_tag')">AI Tag</button>
          <button class="ai-btn" @click="aiAction('summarize')">AI Summary</button>
          <button class="ai-btn" @click="aiAction('link_suggest')">AI Links</button>
        </div>
      </div>
      <div class="notes-content">
        <div class="editor-pane" v-if="viewMode !== 'preview'">
          <textarea v-model="activeNote.content" class="note-textarea" placeholder="Write in Markdown..." @input="onNoteChange"></textarea>
        </div>
        <div class="preview-pane" v-if="viewMode !== 'edit'" v-html="renderedMarkdown"></div>
      </div>
      <AiAssistantPanel
        v-if="aiPanelOpen"
        :loading="aiLoading"
        :result="aiResult"
        :action-label="aiCurrentAction"
        @close="aiPanelOpen = false"
        @apply="applyAIResult"
      />
    </div>
    <div v-else class="notes-empty">
      <p>Select or create a note to get started</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '../../utils/api'
import AiAssistantPanel from './AiAssistantPanel.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'

interface NoteItem {
  id: string
  title: string
  content: string
  tags: string[]
  links: string[]
  createdAt: number
  updatedAt: number
}

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const notes = ref<NoteItem[]>([])
const activeNoteId = ref<string | null>(null)
const searchQuery = ref('')
const viewMode = ref<'edit' | 'preview' | 'split'>('edit')
const newTag = ref('')

const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')

const { saveDoc } = useDocumentPersistence('notes')

const activeNote = computed(() => notes.value.find(n => n.id === activeNoteId.value) || null)

const filteredNotes = computed(() => {
  if (!searchQuery.value) return notes.value
  const q = searchQuery.value.toLowerCase()
  return notes.value.filter(n =>
    n.title.toLowerCase().includes(q) ||
    n.content.toLowerCase().includes(q) ||
    n.tags.some(t => t.toLowerCase().includes(q))
  )
})

const renderedMarkdown = computed(() => {
  if (!activeNote.value) return ''
  return md.render(activeNote.value.content)
})

function createNote() {
  const note: NoteItem = {
    id: Date.now().toString(),
    title: 'New Note',
    content: '',
    tags: [],
    links: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  notes.value.unshift(note)
  activeNoteId.value = note.id
}

function selectNote(id: string) {
  activeNoteId.value = id
  viewMode.value = 'edit'
}

function deleteNote(id: string) {
  const idx = notes.value.findIndex(n => n.id === id)
  if (idx < 0) return
  notes.value.splice(idx, 1)
  if (activeNoteId.value === id) {
    activeNoteId.value = notes.value.length > 0 ? notes.value[0].id : null
  }
}

function addTag() {
  if (!newTag.value.trim() || !activeNote.value) return
  if (!activeNote.value.tags.includes(newTag.value.trim())) {
    activeNote.value.tags.push(newTag.value.trim())
  }
  newTag.value = ''
  onNoteChange()
}

function removeTag(tag: string) {
  if (!activeNote.value) return
  activeNote.value.tags = activeNote.value.tags.filter(t => t !== tag)
  onNoteChange()
}

function onNoteChange() {
  if (activeNote.value) activeNote.value.updatedAt = Date.now()
}

function formatDate(ts: number): string {
  return new Date(ts).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('all', { notes: notes.value, updatedAt: Date.now() })
  }, 1500)
}
watch(notes, debouncedSave, { deep: true })

async function aiAction(action: string) {
  if (!activeNote.value) return
  aiLoading.value = true; aiPanelOpen.value = true; aiResult.value = null
  aiCurrentAction.value = action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  try {
    const res = await api.post('/ai/workspace/notes/assist', {
      action,
      params: { content: activeNote.value.content, title: activeNote.value.title, tags: activeNote.value.tags }
    })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'AI processing failed.' } }
  finally { aiLoading.value = false }
}

function applyAIResult() {
  const data = aiResult.value
  if (!data || !activeNote.value) return
  if (data.tags?.length) {
    data.tags.forEach((t: any) => {
      const name = typeof t === 'string' ? t : t.name
      if (!activeNote.value!.tags.includes(name)) activeNote.value!.tags.push(name)
    })
  }
  if (data.summary) {
    activeNote.value.content += `\n\n---\n**AI Summary:** ${data.summary}`
  }
  aiPanelOpen.value = false
}

onBeforeUnmount(() => { if (saveTimer) clearTimeout(saveTimer) })
</script>

<style scoped>
.notes-editor { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.notes-sidebar { width: 260px; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; background: var(--bg-primary); }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid var(--border-color); }
.sidebar-header h3 { margin: 0; font-size: 15px; }
.add-btn { background: none; border: 1px solid var(--border-color); color: var(--ws-accent); border-radius: 4px; cursor: pointer; padding: 4px; display: flex; }
.add-btn:hover { background: var(--border-color); }
.search-box { padding: 8px 12px; }
.search-input { width: 100%; padding: 6px 10px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-primary); font-size: 12px; outline: none; }
.search-input:focus { border-color: var(--ws-accent); }
.note-list { flex: 1; overflow-y: auto; padding: 4px 8px; }
.note-item { padding: 10px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; transition: all 0.15s; }
.note-item:hover { background: var(--bg-secondary); }
.note-item.active { background: var(--ws-accent-light); border-left: 3px solid var(--ws-accent); }
.note-item-header { display: flex; justify-content: space-between; align-items: center; }
.note-item-header h4 { margin: 0; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.delete-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 2px; display: flex; opacity: 0; transition: opacity 0.15s; }
.note-item:hover .delete-btn { opacity: 1; }
.delete-btn:hover { color: var(--ws-danger); }
.note-preview { font-size: 11px; color: var(--text-tertiary); margin: 4px 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.note-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.note-date { font-size: 10px; color: var(--text-tertiary); }
.note-tags { display: flex; gap: 3px; }
.tag { font-size: 10px; padding: 1px 6px; background: var(--border-color); color: var(--ws-accent-soft); border-radius: 3px; }
.tag.removable { display: flex; align-items: center; gap: 2px; }
.tag-remove { background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: 12px; padding: 0; line-height: 1; }
.tag-remove:hover { color: var(--ws-danger); }
.tag-input { width: 60px; padding: 1px 4px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 3px; color: var(--text-primary); font-size: 10px; outline: none; }
.tag-input:focus { border-color: var(--ws-accent); }
.empty-list { padding: 20px; text-align: center; color: var(--text-tertiary); font-size: 12px; }
.notes-main { flex: 1; display: flex; flex-direction: column; }
.notes-toolbar { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary); flex-wrap: wrap; }
.note-title-input { background: transparent; border: none; color: var(--text-primary); font-size: 16px; font-weight: 600; outline: none; flex: 1; min-width: 120px; }
.note-title-input::placeholder { color: var(--text-tertiary); }
.view-toggle { display: flex; gap: 2px; background: var(--bg-secondary); border-radius: 6px; padding: 2px; }
.toggle-btn { padding: 4px 10px; border-radius: 4px; font-size: 11px; color: var(--text-tertiary); background: transparent; border: none; cursor: pointer; }
.toggle-btn.active { background: var(--ws-accent); color: #fff; }
.tags-area { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.ai-group { display: flex; gap: 4px; margin-left: auto; }
.ai-btn { padding: 4px 8px; border-radius: 4px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.notes-content { flex: 1; display: flex; overflow: hidden; }
.editor-pane { flex: 1; display: flex; }
.note-textarea { flex: 1; padding: 16px; background: var(--bg-primary); border: none; color: var(--text-primary); font-size: 14px; line-height: 1.8; resize: none; outline: none; font-family: inherit; }
.preview-pane { flex: 1; padding: 16px; overflow-y: auto; border-left: 1px solid var(--border-color); }
.preview-pane :deep(h1) { font-size: 24px; font-weight: 700; margin: 0 0 12px; }
.preview-pane :deep(h2) { font-size: 20px; font-weight: 600; margin: 0 0 10px; }
.preview-pane :deep(h3) { font-size: 16px; font-weight: 600; margin: 0 0 8px; }
.preview-pane :deep(p) { margin: 0 0 8px; line-height: 1.7; }
.preview-pane :deep(ul), .preview-pane :deep(ol) { padding-left: 20px; margin: 0 0 8px; }
.preview-pane :deep(code) { background: var(--border-color); padding: 2px 4px; border-radius: 3px; font-size: 13px; }
.preview-pane :deep(pre) { background: var(--bg-secondary); padding: 12px; border-radius: 6px; overflow-x: auto; margin: 0 0 8px; }
.preview-pane :deep(blockquote) { border-left: 3px solid var(--ws-accent); padding-left: 12px; color: var(--text-tertiary); margin: 0 0 8px; }
.notes-empty { flex: 1; display: flex; align-items: center; justify-content: center; color: var(--text-tertiary); }
</style>
