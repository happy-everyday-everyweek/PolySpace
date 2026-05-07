<template>
  <div class="notes-editor">
    <div class="notes-sidebar">
      <div class="sidebar-header">
        <h3>笔记</h3>
        <div class="header-actions">
          <button class="icon-btn" @click="showFilter = !showFilter" title="筛选">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/></svg>
          </button>
          <button class="icon-btn add-btn" @click="createNote('text')" title="新建笔记">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
          </button>
        </div>
      </div>
      <div v-if="showFilter" class="filter-bar">
        <select v-model="filterType" class="filter-select">
          <option value="">全部类型</option>
          <option value="text">文字</option>
          <option value="voice">语音</option>
          <option value="image">图片</option>
          <option value="link">链接</option>
        </select>
      </div>
      <div class="search-box">
        <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        <input v-model="searchQuery" placeholder="搜索笔记..." class="search-input" />
      </div>
      <div class="note-list">
        <div
          v-for="note in filteredNotes"
          :key="note.id"
          :class="['note-item', { active: activeNoteId === note.id, pinned: note.pinned }]"
          @click="selectNote(note.id)"
        >
          <div class="note-item-header">
            <div class="note-title-row">
              <span v-if="note.pinned" class="pin-indicator" title="已置顶">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
              </span>
              <span class="type-badge">{{ typeLabel(note.type) }}</span>
              <h4>{{ note.title || '未命名笔记' }}</h4>
            </div>
            <div class="note-actions">
              <button class="mini-btn" @click.stop="togglePin(note.id)" :title="note.pinned ? '取消置顶' : '置顶'">
                <svg width="12" height="12" viewBox="0 0 24 24" :fill="note.pinned ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.5"><path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"/></svg>
              </button>
              <button class="mini-btn delete-btn" @click.stop="deleteNote(note.id)" title="删除">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
              </button>
            </div>
          </div>
          <p class="note-preview">{{ note.content.substring(0, 80) || note.summary.substring(0, 80) || '空笔记' }}</p>
          <div class="note-meta">
            <span class="note-date">{{ formatDate(note.updatedAt) }}</span>
            <div class="note-tags">
              <span v-for="tag in note.tags.slice(0, 3)" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
        <div v-if="filteredNotes.length === 0" class="empty-list">
          <p>{{ searchQuery ? '没有匹配的笔记' : '暂无笔记，点击 + 创建' }}</p>
        </div>
      </div>
    </div>

    <div class="notes-main" v-if="activeNote">
      <div class="notes-toolbar">
        <input v-model="activeNote.title" class="note-title-input" placeholder="笔记标题" @input="onNoteChange" />
        <div class="view-toggle">
          <button :class="['toggle-btn', { active: viewMode === 'edit' }]" @click="viewMode = 'edit'">编辑</button>
          <button :class="['toggle-btn', { active: viewMode === 'preview' }]" @click="viewMode = 'preview'">预览</button>
          <button :class="['toggle-btn', { active: viewMode === 'split' }]" @click="viewMode = 'split'">分栏</button>
        </div>
        <div class="tags-area">
          <span v-for="tag in activeNote.tags" :key="tag" class="tag removable">
            {{ tag }}
            <button class="tag-remove" @click="removeTag(tag)">&times;</button>
          </span>
          <input v-model="newTag" class="tag-input" placeholder="+ 标签" @keydown.enter="addTag" />
        </div>
        <div class="ai-group">
          <button class="ai-btn" @click="aiAction('summarize')" title="AI 摘要">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/></svg>
            摘要
          </button>
          <button class="ai-btn" @click="aiAction('polish')" title="AI 润色">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            润色
          </button>
          <button class="ai-btn" @click="aiAction('correct')" title="AI 纠错">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>
            纠错
          </button>
          <button class="ai-btn" @click="aiAction('sprout')" title="笔记发芽">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 20h10"/><path d="M10 20c5.5-1 8-5 8.5-10H14c0-4 2.5-7.5 6-9"/><path d="M10 20c-5.5-1-8-5-8.5-10H6c0-4-2.5-7.5-6-9"/></svg>
            发芽
          </button>
          <button class="ai-btn more-ai-btn" @click="showMoreAI = !showMoreAI" title="更多 AI">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
          </button>
        </div>
        <div v-if="showMoreAI" class="more-ai-menu">
          <button @click="aiAction('auto_tag'); showMoreAI = false">AI 标签</button>
          <button @click="aiAction('link_suggest'); showMoreAI = false">AI 关联</button>
          <button @click="aiAction('refine'); showMoreAI = false">AI 精炼</button>
          <button @click="aiAction('voice_correct'); showMoreAI = false">语音纠错</button>
        </div>
      </div>

      <div v-if="activeNote.sourceUrl" class="source-url-bar">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
        <a :href="activeNote.sourceUrl" target="_blank" class="source-link">{{ activeNote.sourceUrl }}</a>
      </div>

      <div class="notes-content">
        <div class="editor-pane" v-if="viewMode !== 'preview'">
          <div v-if="activeNote.type === 'voice' && !activeNote.content" class="voice-recorder">
            <div class="voice-controls">
              <button :class="['record-btn', { recording: isRecording }]" @click="toggleRecording">
                <svg v-if="!isRecording" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
                <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>
              </button>
              <span class="record-status">{{ isRecording ? '录音中...点击停止' : '点击开始录音' }}</span>
              <span v-if="isRecording" class="record-timer">{{ formatDuration(recordingDuration) }}</span>
            </div>
            <div v-if="audioBlob && !activeNote.content" class="voice-preview">
              <audio :src="audioUrl" controls class="audio-player"></audio>
              <button class="icon-btn" @click="transcribeVoice" :disabled="aiLoading" title="转文字">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>
                转为文字
              </button>
            </div>
          </div>
          <div v-if="activeNote.type === 'image' && !activeNote.content" class="image-uploader">
            <div class="upload-area" @click="triggerImageUpload" @dragover.prevent @drop.prevent="handleImageDrop">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              <p>点击选择图片或拖拽到此处</p>
              <span class="upload-hint">支持 JPG、PNG、GIF、WebP</span>
            </div>
            <input ref="imageInputRef" type="file" accept="image/*" style="display:none" @change="handleImageSelect" />
            <div v-if="imagePreviewUrl" class="image-preview">
              <img :src="imagePreviewUrl" alt="预览" class="preview-img" />
              <div class="image-actions">
                <button class="icon-btn" @click="ocrImage" :disabled="aiLoading" title="OCR 识别">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
                  OCR 识别
                </button>
                <button class="icon-btn" @click="insertImageToContent" title="插入到笔记">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
                  插入笔记
                </button>
                <button class="icon-btn" @click="clearImage" title="清除">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
              </div>
            </div>
          </div>
          <textarea v-model="activeNote.content" class="note-textarea" :placeholder="textareaPlaceholder" @input="onNoteChange"></textarea>
        </div>
        <div class="preview-pane" v-if="viewMode !== 'edit'" v-html="renderedMarkdown"></div>
      </div>

      <div v-if="activeNote.sproutReport" class="sprout-bar" @click="showSprout = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 20h10"/><path d="M10 20c5.5-1 8-5 8.5-10H14c0-4 2.5-7.5 6-9"/><path d="M10 20c-5.5-1-8-5-8.5-10H6c0-4-2.5-7.5-6-9"/></svg>
        <span>查看发芽报告 ({{ activeNote.sproutReport.sections.length }} 章节)</span>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
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
      <div class="empty-content">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><path d="M12 18v-6"/><path d="M9 15h6"/></svg>
        <p>选择或创建笔记开始使用</p>
        <div class="quick-create">
          <button class="create-type-btn" @click="createNote('text')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
            <span>文字笔记</span>
          </button>
          <button class="create-type-btn" @click="createNote('voice')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
            <span>语音笔记</span>
          </button>
          <button class="create-type-btn" @click="createNote('image')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
            <span>图片笔记</span>
          </button>
          <button class="create-type-btn" @click="createNote('link')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
            <span>链接笔记</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showSprout && activeNote?.sproutReport" class="sprout-overlay" @click.self="showSprout = false">
      <div class="sprout-modal">
        <div class="sprout-header">
          <h3>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 20h10"/><path d="M10 20c5.5-1 8-5 8.5-10H14c0-4 2.5-7.5 6-9"/><path d="M10 20c-5.5-1-8-5-8.5-10H6c0-4-2.5-7.5-6-9"/></svg>
            发芽报告
          </h3>
          <span class="sprout-date">{{ activeNote.sproutReport.createdAt }}</span>
          <button class="close-btn" @click="showSprout = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="sprout-sections">
          <div v-for="(section, idx) in activeNote.sproutReport.sections" :key="idx" :class="['sprout-section', { active: sproutPage === idx }]">
            <div class="section-number">{{ String(section.number || idx + 1).padStart(2, '0') }}</div>
            <h4 class="section-title">{{ section.title }}</h4>
            <div class="section-content">{{ section.content }}</div>
            <div v-if="section.ahaMoment" class="aha-moment">
              <span class="aha-label">Aha 瞬间</span>
              <p>{{ section.ahaMoment }}</p>
            </div>
          </div>
        </div>
        <div class="sprout-nav">
          <button :disabled="sproutPage <= 0" @click="sproutPage--">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
          </button>
          <div class="sprout-dots">
            <span v-for="(_, idx) in activeNote.sproutReport.sections" :key="idx" :class="['dot', { active: sproutPage === idx }]" @click="sproutPage = idx"></span>
          </div>
          <button :disabled="sproutPage >= activeNote.sproutReport.sections.length - 1" @click="sproutPage++">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showLinkInput" class="link-overlay" @click.self="showLinkInput = false">
      <div class="link-dialog">
        <h4>链接笔记</h4>
        <p class="link-hint">粘贴网页链接，AI 自动解析生成结构化笔记</p>
        <div class="link-input-row">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
          <input v-model="linkUrl" placeholder="https://..." class="link-url-input" @keydown.enter="submitLink" />
        </div>
        <div class="link-actions">
          <button class="cancel-btn" @click="showLinkInput = false">取消</button>
          <button class="submit-btn" :disabled="!linkUrl.trim()" @click="submitLink">解析并生成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '../../utils/api'
import AiAssistantPanel from './AiAssistantPanel.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'

interface SproutSection {
  number: number
  title: string
  content: string
  ahaMoment: string
}

interface SproutReport {
  title: string
  sections: SproutSection[]
  createdAt: string
}

interface NoteItem {
  id: string
  type: 'text' | 'voice' | 'image' | 'link'
  title: string
  content: string
  summary: string
  tags: string[]
  category: string
  sourceUrl: string
  attachments: string[]
  sproutReport: SproutReport | null
  pinned: boolean
  createdAt: number
  updatedAt: number
}

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const notes = ref<NoteItem[]>([])
const activeNoteId = ref<string | null>(null)
const searchQuery = ref('')
const filterType = ref('')
const viewMode = ref<'edit' | 'preview' | 'split'>('edit')
const newTag = ref('')
const showFilter = ref(false)
const showMoreAI = ref(false)
const showSprout = ref(false)
const sproutPage = ref(0)
const showLinkInput = ref(false)
const linkUrl = ref('')

const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')

const isRecording = ref(false)
const recordingDuration = ref(0)
const audioBlob = ref<Blob | null>(null)
const audioUrl = ref('')
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []
let recordingTimer: ReturnType<typeof setInterval> | null = null

const imageInputRef = ref<HTMLInputElement | null>(null)
const imagePreviewUrl = ref('')
let imageBase64 = ''

const { saveDoc } = useDocumentPersistence('notes')

const activeNote = computed(() => notes.value.find(n => n.id === activeNoteId.value) || null)

const textareaPlaceholder = computed(() => {
  if (!activeNote.value) return ''
  const t = activeNote.value.type
  if (t === 'voice') return '录音转写内容将显示在这里，你也可以直接编辑...'
  if (t === 'image') return '图片识别内容将显示在这里，你也可以直接编辑...'
  if (t === 'link') return '链接解析内容将显示在这里，你也可以直接编辑...'
  return '使用 Markdown 书写...'
})

const filteredNotes = computed(() => {
  let result = notes.value
  if (filterType.value) {
    result = result.filter(n => n.type === filterType.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(n =>
      n.title.toLowerCase().includes(q) ||
      n.content.toLowerCase().includes(q) ||
      n.summary.toLowerCase().includes(q) ||
      n.tags.some(t => t.toLowerCase().includes(q))
    )
  }
  const pinned = result.filter(n => n.pinned).sort((a, b) => b.updatedAt - a.updatedAt)
  const unpinned = result.filter(n => !n.pinned).sort((a, b) => b.updatedAt - a.updatedAt)
  return [...pinned, ...unpinned]
})

const renderedMarkdown = computed(() => {
  if (!activeNote.value) return ''
  return md.render(activeNote.value.content)
})

function typeLabel(type: string): string {
  const map: Record<string, string> = { text: '文字', voice: '语音', image: '图片', link: '链接' }
  return map[type] || '文字'
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

function createNote(type: NoteItem['type'] = 'text') {
  if (type === 'link') {
    showLinkInput.value = true
    linkUrl.value = ''
    return
  }
  const note: NoteItem = {
    id: Date.now().toString(),
    type,
    title: type === 'voice' ? '语音笔记' : type === 'image' ? '图片笔记' : '新笔记',
    content: '',
    summary: '',
    tags: [],
    category: '',
    sourceUrl: '',
    attachments: [],
    sproutReport: null,
    pinned: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  notes.value.unshift(note)
  activeNoteId.value = note.id
  viewMode.value = 'edit'
  resetMediaState()
}

function resetMediaState() {
  isRecording.value = false
  recordingDuration.value = 0
  audioBlob.value = null
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
  audioUrl.value = ''
  audioChunks = []
  imagePreviewUrl.value = ''
  imageBase64 = ''
}

async function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder = new MediaRecorder(stream)
    audioChunks = []
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data)
    }
    mediaRecorder.onstop = () => {
      const blob = new Blob(audioChunks, { type: 'audio/webm' })
      audioBlob.value = blob
      if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
      audioUrl.value = URL.createObjectURL(blob)
      stream.getTracks().forEach(t => t.stop())
    }
    mediaRecorder.start()
    isRecording.value = true
    recordingDuration.value = 0
    recordingTimer = setInterval(() => { recordingDuration.value++ }, 1000)
  } catch {
    isRecording.value = false
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
  if (recordingTimer) { clearInterval(recordingTimer); recordingTimer = null }
}

async function transcribeVoice() {
  if (!audioBlob.value || !activeNote.value) return
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  aiCurrentAction.value = '语音转写'
  try {
    const reader = new FileReader()
    const base64Promise = new Promise<string>((resolve) => {
      reader.onloadend = () => resolve(reader.result as string)
      reader.readAsDataURL(audioBlob.value!)
    })
    const audioBase64 = await base64Promise
    const res = await api.post('/ai/workspace/notes/assist', {
      action: 'voice_correct',
      params: {
        content: '[语音录音数据]',
        title: activeNote.value.title,
        audio_data: audioBase64,
        note_type: 'voice',
      }
    })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: '语音转写失败，请手动输入内容。' }
  } finally {
    aiLoading.value = false
  }
}

function triggerImageUpload() {
  imageInputRef.value?.click()
}

function handleImageSelect(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) processImageFile(file)
}

function handleImageDrop(e: DragEvent) {
  const file = e.dataTransfer?.files?.[0]
  if (file && file.type.startsWith('image/')) processImageFile(file)
}

function processImageFile(file: File) {
  const reader = new FileReader()
  reader.onload = (ev) => {
    const dataUrl = ev.target?.result as string
    imagePreviewUrl.value = dataUrl
    imageBase64 = dataUrl
    if (activeNote.value) {
      activeNote.value.attachments = [dataUrl]
      onNoteChange()
    }
  }
  reader.readAsDataURL(file)
}

function insertImageToContent() {
  if (!imagePreviewUrl.value || !activeNote.value) return
  const imgMarkdown = `![图片](${imagePreviewUrl.value})\n\n`
  activeNote.value.content = imgMarkdown + activeNote.value.content
  onNoteChange()
}

async function ocrImage() {
  if (!imageBase64 || !activeNote.value) return
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  aiCurrentAction.value = 'OCR 识别'
  try {
    const res = await api.post('/ai/workspace/notes/assist', {
      action: 'ocr_note',
      params: {
        content: '[图片数据]',
        title: activeNote.value.title,
        image_data: imageBase64,
        note_type: 'image',
      }
    })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'OCR 识别失败，请手动输入内容。' }
  } finally {
    aiLoading.value = false
  }
}

function clearImage() {
  imagePreviewUrl.value = ''
  imageBase64 = ''
  if (activeNote.value) {
    activeNote.value.attachments = []
    onNoteChange()
  }
}

async function submitLink() {
  if (!linkUrl.value.trim()) return
  const note: NoteItem = {
    id: Date.now().toString(),
    type: 'link',
    title: '链接笔记',
    content: '',
    summary: '',
    tags: [],
    category: '',
    sourceUrl: linkUrl.value.trim(),
    attachments: [],
    sproutReport: null,
    pinned: false,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }
  notes.value.unshift(note)
  activeNoteId.value = note.id
  showLinkInput.value = false
  viewMode.value = 'edit'
  await aiAction('extract_url', { url: note.sourceUrl, content: '', title: '' })
}

function selectNote(id: string) {
  activeNoteId.value = id
  viewMode.value = 'edit'
  showMoreAI.value = false
  resetMediaState()
  if (activeNote.value?.attachments?.[0] && activeNote.value.type === 'image') {
    imagePreviewUrl.value = activeNote.value.attachments[0]
    imageBase64 = activeNote.value.attachments[0]
  }
}

function deleteNote(id: string) {
  const idx = notes.value.findIndex(n => n.id === id)
  if (idx < 0) return
  notes.value.splice(idx, 1)
  if (activeNoteId.value === id) {
    activeNoteId.value = notes.value.length > 0 ? notes.value[0].id : null
  }
}

function togglePin(id: string) {
  const note = notes.value.find(n => n.id === id)
  if (note) {
    note.pinned = !note.pinned
    note.updatedAt = Date.now()
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

async function aiAction(action: string, extraParams?: Record<string, any>) {
  if (!activeNote.value) return
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  aiCurrentAction.value = actionLabel(action)
  try {
    const params: Record<string, any> = {
      content: activeNote.value.content,
      title: activeNote.value.title,
      tags: activeNote.value.tags,
      note_type: activeNote.value.type,
      source_url: activeNote.value.sourceUrl,
      ...extraParams,
    }
    const res = await api.post('/ai/workspace/notes/assist', { action, params })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'AI 处理失败，请稍后重试。' }
  } finally {
    aiLoading.value = false
  }
}

function actionLabel(action: string): string {
  const map: Record<string, string> = {
    summarize: 'AI 摘要',
    auto_tag: 'AI 标签',
    link_suggest: 'AI 关联',
    generate: 'AI 生成',
    refine: 'AI 精炼',
    polish: 'AI 润色',
    correct: 'AI 纠错',
    sprout: '笔记发芽',
    extract_url: '链接解析',
    ocr_note: 'OCR 识别',
    voice_correct: '语音纠错',
  }
  return map[action] || action
}

function applyAIResult() {
  const data = aiResult.value
  if (!data || !activeNote.value) return

  const defaultTitles = ['新笔记', '链接笔记', '语音笔记', '图片笔记']

  if (data.title && defaultTitles.includes(activeNote.value.title)) {
    activeNote.value.title = data.title
  }

  if (data.polished_content) {
    activeNote.value.content = data.polished_content
  }
  if (data.corrected_content) {
    activeNote.value.content = data.corrected_content
  }
  if (data.refined_content) {
    activeNote.value.content = data.refined_content
  }
  if (data.organized_content) {
    activeNote.value.content = data.organized_content
  }
  if (data.structured_content) {
    activeNote.value.content = data.structured_content
  }
  if (data.content && aiCurrentAction.value === 'OCR 识别') {
    activeNote.value.content = data.content
  }
  if (data.content && aiCurrentAction.value === '链接解析') {
    activeNote.value.content = data.content
  }

  if (data.summary) {
    activeNote.value.summary = data.summary
  }

  if (data.key_points?.length) {
    activeNote.value.content += '\n\n---\n**核心要点：**\n' + data.key_points.map((p: string) => `- ${p}`).join('\n')
  }

  if (data.tags?.length) {
    data.tags.forEach((t: any) => {
      const name = typeof t === 'string' ? t : t.name
      if (name && !activeNote.value!.tags.includes(name)) activeNote.value!.tags.push(name)
    })
  }
  if (data.suggested_tags?.length) {
    data.suggested_tags.forEach((t: string) => {
      if (!activeNote.value!.tags.includes(t)) activeNote.value!.tags.push(t)
    })
  }

  if (data.sections?.length && (aiCurrentAction.value === '笔记发芽' || aiCurrentAction.value === 'sprout')) {
    activeNote.value.sproutReport = {
      title: data.title || '发芽报告',
      sections: data.sections.map((s: any, i: number) => ({
        number: s.number || i + 1,
        title: s.title || '',
        content: s.content || '',
        ahaMoment: s.aha_moment || s.ahaMoment || '',
      })),
      createdAt: new Date().toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' 生成',
    }
    showSprout.value = true
    sproutPage.value = 0
  }

  if (data.suggestions?.length) {
    activeNote.value.content += '\n\n---\n**关联笔记：**\n' + data.suggestions.map((s: any) => `- ${s.title}: ${s.reason}`).join('\n')
  }

  if (data.outline?.length) {
    activeNote.value.content += '\n\n---\n**大纲：**\n' + data.outline.map((item: any) => `${'  '.repeat((item.level || 1) - 1)}${item.level === 1 ? '#' : '##'} ${item.text}`).join('\n')
  }

  onNoteChange()
  aiPanelOpen.value = false
}

watch(showSprout, (v) => {
  if (v) sproutPage.value = 0
})

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer)
  if (recordingTimer) clearInterval(recordingTimer)
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop()
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
})
</script>

<style scoped>
.notes-editor { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); position: relative; }
.notes-sidebar { width: 280px; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; background: var(--bg-primary); flex-shrink: 0; }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-md) var(--spacing-lg); border-bottom: 1px solid var(--border-color); }
.sidebar-header h3 { margin: 0; font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); }
.header-actions { display: flex; gap: var(--spacing-xs); }
.icon-btn { background: none; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: var(--radius-sm); cursor: pointer; padding: var(--spacing-sm); display: flex; align-items: center; justify-content: center; gap: var(--spacing-xs); transition: all var(--transition-fast); font-size: var(--font-size-xs); }
.icon-btn:hover { background: var(--bg-secondary); color: var(--text-primary); }
.icon-btn:active { transform: scale(0.97); }
.icon-btn:disabled { opacity: 0.5; cursor: default; }
.add-btn { color: var(--text-primary); border-color: var(--text-primary); }
.add-btn:hover { background: var(--text-primary); color: var(--bg-primary); }
.add-btn:active { transform: scale(0.97); }
.filter-bar { padding: var(--spacing-sm) var(--spacing-md); border-bottom: 1px solid var(--border-color); }
.filter-select { width: 100%; padding: var(--spacing-sm) var(--spacing-md); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-primary); font-size: var(--font-size-sm); outline: none; transition: border-color var(--transition-fast); }
.filter-select:focus { border-color: var(--text-primary); }
.search-box { padding: var(--spacing-sm) var(--spacing-md); display: flex; align-items: center; gap: var(--spacing-sm); }
.search-icon { color: var(--text-tertiary); flex-shrink: 0; }
.search-input { flex: 1; padding: var(--spacing-sm) var(--spacing-md); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-primary); font-size: var(--font-size-sm); outline: none; transition: border-color var(--transition-fast); }
.search-input:focus { border-color: var(--text-primary); }
.note-list { flex: 1; overflow-y: auto; padding: var(--spacing-xs) var(--spacing-sm); }
.note-item { padding: var(--spacing-sm) var(--spacing-md); border-radius: var(--radius-md); cursor: pointer; margin-bottom: var(--spacing-xs); transition: all var(--transition-fast); border-left: 3px solid transparent; }
.note-item:hover { background: var(--bg-secondary); }
.note-item.active { background: var(--primary-light); border-left-color: var(--text-primary); }
.note-item.pinned { border-left-color: var(--text-primary); }
.note-item-header { display: flex; justify-content: space-between; align-items: flex-start; }
.note-title-row { display: flex; align-items: center; gap: var(--spacing-sm); flex: 1; min-width: 0; }
.pin-indicator { color: var(--text-primary); flex-shrink: 0; }
.type-badge { font-size: var(--font-size-xs); padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); font-weight: var(--font-weight-medium); flex-shrink: 0; background: var(--bg-secondary); color: var(--text-tertiary); }
.note-item-header h4 { margin: 0; font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.note-actions { display: flex; gap: 2px; opacity: 0; transition: opacity var(--transition-fast); }
.note-item:hover .note-actions { opacity: 1; }
.mini-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 2px; display: flex; border-radius: var(--radius-sm); transition: all var(--transition-fast); }
.mini-btn:hover { color: var(--text-primary); background: var(--bg-tertiary); }
.mini-btn:active { transform: scale(0.97); }
.delete-btn:hover { color: var(--ws-danger); }
.note-preview { font-size: var(--font-size-xs); color: var(--text-tertiary); margin: var(--spacing-xs) 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.note-meta { display: flex; justify-content: space-between; align-items: center; margin-top: var(--spacing-sm); }
.note-date { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.note-tags { display: flex; gap: var(--spacing-xs); }
.tag { font-size: var(--font-size-xs); padding: 1px var(--spacing-sm); background: var(--bg-secondary); color: var(--text-secondary); border-radius: var(--radius-sm); }
.tag.removable { display: flex; align-items: center; gap: 2px; }
.tag-remove { background: none; border: none; color: var(--text-tertiary); cursor: pointer; font-size: var(--font-size-sm); padding: 0; line-height: 1; transition: color var(--transition-fast); }
.tag-remove:hover { color: var(--ws-danger); }
.tag-input { width: 60px; padding: 1px var(--spacing-xs); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-primary); font-size: var(--font-size-xs); outline: none; transition: border-color var(--transition-fast); }
.tag-input:focus { border-color: var(--text-primary); }
.empty-list { padding: var(--spacing-xl); text-align: center; color: var(--text-tertiary); font-size: var(--font-size-sm); }
.notes-main { flex: 1; display: flex; flex-direction: column; position: relative; }
.notes-toolbar { display: flex; align-items: center; gap: var(--spacing-md); padding: var(--spacing-sm) var(--spacing-lg); border-bottom: 1px solid var(--border-color); background: var(--bg-secondary); flex-wrap: wrap; position: relative; }
.note-title-input { background: transparent; border: none; color: var(--text-primary); font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); outline: none; flex: 1; min-width: 120px; }
.note-title-input::placeholder { color: var(--text-tertiary); }
.view-toggle { display: flex; gap: 2px; background: var(--bg-tertiary); border-radius: var(--radius-sm); padding: 2px; }
.toggle-btn { padding: var(--spacing-xs) var(--spacing-md); border-radius: var(--radius-sm); font-size: var(--font-size-xs); color: var(--text-tertiary); background: transparent; border: none; cursor: pointer; transition: all var(--transition-fast); }
.toggle-btn.active { background: var(--text-primary); color: var(--bg-primary); }
.toggle-btn:active { transform: scale(0.97); }
.tags-area { display: flex; align-items: center; gap: var(--spacing-xs); flex-wrap: wrap; }
.ai-group { display: flex; gap: var(--spacing-xs); margin-left: auto; }
.ai-btn { padding: var(--spacing-xs) var(--spacing-sm); border-radius: var(--radius-sm); font-size: var(--font-size-xs); color: var(--text-secondary); background: none; border: 1px solid var(--border-color); cursor: pointer; display: flex; align-items: center; gap: var(--spacing-xs); transition: all var(--transition-fast); }
.ai-btn:hover { background: var(--bg-secondary); border-color: var(--text-primary); color: var(--text-primary); }
.ai-btn:active { transform: scale(0.97); }
.more-ai-btn { padding: var(--spacing-xs) var(--spacing-sm); }
.more-ai-menu { position: absolute; top: 100%; right: var(--spacing-lg); background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius-md); box-shadow: var(--shadow-md); z-index: 10; min-width: 120px; padding: var(--spacing-xs); animation: menuFadeIn var(--transition-fast); }
.more-ai-menu button { display: block; width: 100%; padding: var(--spacing-sm) var(--spacing-md); background: none; border: none; color: var(--text-primary); font-size: var(--font-size-sm); text-align: left; cursor: pointer; border-radius: var(--radius-sm); transition: background var(--transition-fast); }
.more-ai-menu button:hover { background: var(--bg-secondary); }
.more-ai-menu button:active { transform: scale(0.97); }
@keyframes menuFadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
.source-url-bar { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-sm) var(--spacing-lg); background: var(--bg-tertiary); border-bottom: 1px solid var(--border-color); font-size: var(--font-size-sm); color: var(--text-tertiary); }
.source-link { color: var(--text-primary); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: color var(--transition-fast); }
.source-link:hover { text-decoration: underline; }
.notes-content { flex: 1; display: flex; overflow: hidden; }
.editor-pane { flex: 1; display: flex; flex-direction: column; }
.note-textarea { flex: 1; padding: var(--spacing-lg); background: var(--bg-primary); border: none; color: var(--text-primary); font-size: var(--font-size-base); line-height: 1.5; resize: none; outline: none; font-family: inherit; }
.preview-pane { flex: 1; padding: var(--spacing-lg); overflow-y: auto; border-left: 1px solid var(--border-color); }
.preview-pane :deep(h1) { font-size: var(--font-size-xl); font-weight: var(--font-weight-bold); margin: 0 0 var(--spacing-md); }
.preview-pane :deep(h2) { font-size: var(--font-size-lg); font-weight: var(--font-weight-semibold); margin: 0 0 var(--spacing-sm); }
.preview-pane :deep(h3) { font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); margin: 0 0 var(--spacing-sm); }
.preview-pane :deep(p) { margin: 0 0 var(--spacing-sm); line-height: 1.5; }
.preview-pane :deep(ul), .preview-pane :deep(ol) { padding-left: 20px; margin: 0 0 var(--spacing-sm); }
.preview-pane :deep(code) { background: var(--bg-tertiary); padding: 2px var(--spacing-xs); border-radius: var(--radius-sm); font-size: var(--font-size-sm); }
.preview-pane :deep(pre) { background: var(--bg-secondary); padding: var(--spacing-md); border-radius: var(--radius-sm); overflow-x: auto; margin: 0 0 var(--spacing-sm); }
.preview-pane :deep(blockquote) { border-left: 3px solid var(--text-primary); padding-left: var(--spacing-md); color: var(--text-tertiary); margin: 0 0 var(--spacing-sm); }
.preview-pane :deep(img) { max-width: 100%; border-radius: var(--radius-md); }

.voice-recorder { padding: var(--spacing-xl); display: flex; flex-direction: column; align-items: center; gap: var(--spacing-lg); border-bottom: 1px solid var(--border-color); }
.voice-controls { display: flex; align-items: center; gap: var(--spacing-md); }
.record-btn { width: 48px; height: 48px; border-radius: var(--radius-full); border: 2px solid var(--border-color); background: var(--bg-secondary); color: var(--text-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all var(--transition-fast); }
.record-btn:hover { border-color: var(--text-primary); color: var(--text-primary); }
.record-btn:active { transform: scale(0.97); }
.record-btn.recording { border-color: var(--ws-danger); color: var(--ws-danger); background: rgba(239, 68, 68, 0.1); animation: pulse 1.5s ease infinite; }
@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3); } 50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); } }
.record-status { font-size: var(--font-size-sm); color: var(--text-secondary); }
.record-timer { font-size: var(--font-size-sm); color: var(--text-tertiary); font-variant-numeric: tabular-nums; }
.voice-preview { display: flex; align-items: center; gap: var(--spacing-md); }
.audio-player { height: 36px; border-radius: var(--radius-sm); }

.image-uploader { padding: var(--spacing-xl); display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md); border-bottom: 1px solid var(--border-color); }
.upload-area { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-2xl); border: 2px dashed var(--border-color); border-radius: var(--radius-lg); cursor: pointer; color: var(--text-tertiary); transition: all var(--transition-fast); }
.upload-area:hover { border-color: var(--text-primary); color: var(--text-secondary); }
.upload-area p { margin: 0; font-size: var(--font-size-sm); }
.upload-hint { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.image-preview { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm); }
.preview-img { max-width: 100%; max-height: 200px; object-fit: contain; border-radius: var(--radius-md); }
.image-actions { display: flex; gap: var(--spacing-sm); }

.sprout-bar { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-sm) var(--spacing-lg); background: var(--bg-secondary); border-top: 1px solid var(--border-color); cursor: pointer; color: var(--text-secondary); font-size: var(--font-size-sm); transition: background var(--transition-fast); }
.sprout-bar:hover { background: var(--bg-tertiary); }
.notes-empty { flex: 1; display: flex; align-items: center; justify-content: center; }
.empty-content { text-align: center; color: var(--text-tertiary); }
.empty-content svg { margin-bottom: var(--spacing-md); opacity: 0.3; }
.empty-content p { margin: 0 0 var(--spacing-xl); font-size: var(--font-size-base); }
.quick-create { display: flex; gap: var(--spacing-md); justify-content: center; }
.create-type-btn { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-md) var(--spacing-lg); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); cursor: pointer; color: var(--text-secondary); transition: all var(--transition-fast); }
.create-type-btn:hover { border-color: var(--text-primary); color: var(--text-primary); }
.create-type-btn:active { transform: scale(0.97); }
.create-type-btn span { font-size: var(--font-size-xs); }
.sprout-overlay { position: fixed; inset: 0; background: var(--overlay-bg); z-index: 100; display: flex; align-items: center; justify-content: center; animation: overlayFadeIn var(--transition-smooth); }
.sprout-modal { background: var(--bg-primary); border-radius: var(--radius-xl); width: 560px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: var(--shadow-lg); animation: modalSlideIn var(--transition-smooth); }
.sprout-header { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-lg) var(--spacing-xl); border-bottom: 1px solid var(--border-color); }
.sprout-header h3 { margin: 0; font-size: var(--font-size-md); display: flex; align-items: center; gap: var(--spacing-sm); color: var(--text-primary); }
.sprout-date { font-size: var(--font-size-xs); color: var(--text-tertiary); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: var(--spacing-xs); border-radius: var(--radius-sm); margin-left: auto; transition: all var(--transition-fast); }
.close-btn:hover { background: var(--bg-secondary); color: var(--text-primary); }
.close-btn:active { transform: scale(0.97); }
.sprout-sections { flex: 1; overflow-y: auto; padding: var(--spacing-xl); }
.sprout-section { padding: var(--spacing-lg); border-radius: var(--radius-lg); margin-bottom: var(--spacing-md); border: 1px solid var(--border-color); transition: border-color var(--transition-normal); }
.sprout-section.active { border-color: var(--text-primary); }
.section-number { font-size: var(--font-size-xs); color: var(--text-tertiary); font-weight: var(--font-weight-semibold); margin-bottom: var(--spacing-sm); }
.section-title { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); margin: 0 0 var(--spacing-sm); }
.section-content { font-size: var(--font-size-sm); line-height: 1.5; color: var(--text-secondary); margin-bottom: var(--spacing-md); }
.aha-moment { background: var(--bg-secondary); border-left: 3px solid var(--text-primary); padding: var(--spacing-sm) var(--spacing-md); border-radius: 0 var(--radius-md) var(--radius-md) 0; }
.aha-label { font-size: var(--font-size-xs); color: var(--text-tertiary); font-weight: var(--font-weight-semibold); text-transform: uppercase; letter-spacing: 0.5px; }
.aha-moment p { margin: var(--spacing-xs) 0 0; font-size: var(--font-size-sm); font-style: italic; color: var(--text-secondary); line-height: 1.5; }
.sprout-nav { display: flex; align-items: center; justify-content: center; gap: var(--spacing-lg); padding: var(--spacing-md); border-top: 1px solid var(--border-color); }
.sprout-nav button { background: none; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: var(--spacing-sm) var(--spacing-md); cursor: pointer; color: var(--text-secondary); display: flex; transition: all var(--transition-fast); }
.sprout-nav button:hover:not(:disabled) { background: var(--bg-secondary); }
.sprout-nav button:active:not(:disabled) { transform: scale(0.97); }
.sprout-nav button:disabled { opacity: 0.3; cursor: default; }
.sprout-dots { display: flex; gap: var(--spacing-sm); }
.dot { width: 8px; height: 8px; border-radius: var(--radius-full); background: var(--border-color); cursor: pointer; transition: background var(--transition-fast); }
.dot.active { background: var(--text-primary); }
.link-overlay { position: fixed; inset: 0; background: var(--overlay-bg); z-index: 100; display: flex; align-items: center; justify-content: center; animation: overlayFadeIn var(--transition-smooth); }
.link-dialog { background: var(--bg-primary); border-radius: var(--radius-lg); padding: var(--spacing-xl); width: 440px; box-shadow: var(--shadow-lg); animation: modalSlideIn var(--transition-smooth); }
.link-dialog h4 { margin: 0 0 var(--spacing-sm); font-size: var(--font-size-md); }
.link-hint { margin: 0 0 var(--spacing-lg); font-size: var(--font-size-sm); color: var(--text-tertiary); }
.link-input-row { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-sm) var(--spacing-md); background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); margin-bottom: var(--spacing-lg); }
.link-input-row svg { color: var(--text-secondary); flex-shrink: 0; }
.link-url-input { flex: 1; background: transparent; border: none; color: var(--text-primary); font-size: var(--font-size-base); outline: none; }
.link-url-input::placeholder { color: var(--text-tertiary); }
.link-actions { display: flex; justify-content: flex-end; gap: var(--spacing-sm); }
.cancel-btn { padding: var(--spacing-sm) var(--spacing-lg); background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-md); color: var(--text-secondary); cursor: pointer; font-size: var(--font-size-sm); transition: all var(--transition-fast); }
.cancel-btn:hover { background: var(--bg-tertiary); }
.cancel-btn:active { transform: scale(0.97); }
.submit-btn { padding: var(--spacing-sm) var(--spacing-lg); background: var(--text-primary); border: none; border-radius: var(--radius-md); color: var(--bg-primary); cursor: pointer; font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); transition: all var(--transition-fast); }
.submit-btn:hover { background: var(--primary-hover); }
.submit-btn:active { transform: scale(0.97); }
.submit-btn:disabled { opacity: 0.5; cursor: default; }
@keyframes overlayFadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes modalSlideIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
</style>
