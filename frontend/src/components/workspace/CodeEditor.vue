<template>
  <div class="code-view">
    <div class="code-header">
      <h3 class="section-label">Code Editor</h3>
      <div class="lang-select">
        <select v-model="language">
          <option value="python">Python</option>
          <option value="javascript">JavaScript</option>
          <option value="typescript">TypeScript</option>
          <option value="html">HTML</option>
          <option value="css">CSS</option>
          <option value="json">JSON</option>
          <option value="sql">SQL</option>
          <option value="markdown">Markdown</option>
        </select>
      </div>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiAction('explain')">AI Explain</button>
        <button class="ai-header-btn" @click="aiAction('refactor')">AI Refactor</button>
        <button class="ai-header-btn" @click="aiAction('review')">AI Review</button>
        <button class="ai-header-btn" @click="aiAction('generate')">AI Generate</button>
      </div>
    </div>
    <div class="code-body">
      <div ref="editorRef" class="code-editor-container"></div>
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
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, shallowRef } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLineGutter, highlightSpecialChars, drawSelection, dropCursor, rectangularSelection, crosshairCursor, highlightActiveLine } from '@codemirror/view'
import { EditorState, Compartment } from '@codemirror/state'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { syntaxHighlighting, defaultHighlightStyle, bracketMatching, foldGutter, indentOnInput, foldKeymap } from '@codemirror/language'
import { oneDark } from '@codemirror/theme-one-dark'
import { autocompletion, completionKeymap, closeBrackets, closeBracketsKeymap } from '@codemirror/autocomplete'
import { searchKeymap, highlightSelectionMatches } from '@codemirror/search'
import { python } from '@codemirror/lang-python'
import { javascript } from '@codemirror/lang-javascript'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { json } from '@codemirror/lang-json'
import { sql } from '@codemirror/lang-sql'
import { markdown } from '@codemirror/lang-markdown'
import api from '../../utils/api'
import AiAssistantPanel from './AiAssistantPanel.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'

const language = ref('python')
const editorRef = ref<HTMLElement>()
const view = shallowRef<EditorView>()
const langCompartment = new Compartment()

const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')

const { saveDoc } = useDocumentPersistence('code')

let saveTimer: ReturnType<typeof setTimeout> | null = null

function getLangExtension(lang: string) {
  switch (lang) {
    case 'python': return python()
    case 'javascript': return javascript()
    case 'typescript': return javascript({ typescript: true })
    case 'html': return html()
    case 'css': return css()
    case 'json': return json()
    case 'sql': return sql()
    case 'markdown': return markdown()
    default: return []
  }
}

function getCode(): string {
  return view.value?.state.doc.toString() || ''
}

function setCode(code: string) {
  if (!view.value) return
  view.value.dispatch({
    changes: { from: 0, to: view.value.state.doc.length, insert: code },
  })
}

function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', { content: getCode(), language: language.value, updatedAt: Date.now() })
  }, 1500)
}

onMounted(() => {
  if (!editorRef.value) return
  const state = EditorState.create({
    doc: '',
    extensions: [
      lineNumbers(),
      highlightActiveLineGutter(),
      highlightSpecialChars(),
      history(),
      foldGutter(),
      drawSelection(),
      dropCursor(),
      EditorState.allowMultipleSelections.of(true),
      indentOnInput(),
      syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
      bracketMatching(),
      closeBrackets(),
      autocompletion(),
      rectangularSelection(),
      crosshairCursor(),
      highlightActiveLine(),
      highlightSelectionMatches(),
      keymap.of([
        ...closeBracketsKeymap,
        ...defaultKeymap,
        ...searchKeymap,
        ...historyKeymap,
        ...foldKeymap,
        ...completionKeymap,
        indentWithTab,
      ]),
      oneDark,
      langCompartment.of(getLangExtension(language.value)),
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          debouncedSave()
        }
      }),
      EditorView.theme({
        '&': { height: '100%', fontSize: '13px' },
        '.cm-scroller': { overflow: 'auto', fontFamily: "'Consolas', 'Monaco', monospace" },
      }),
    ],
  })
  view.value = new EditorView({ state, parent: editorRef.value })
})

watch(language, (newLang) => {
  if (view.value) {
    view.value.dispatch({
      effects: langCompartment.reconfigure(getLangExtension(newLang)),
    })
  }
})

async function aiAction(action: string) {
  const code = getCode()
  if (!code && action !== 'generate') return
  aiCurrentAction.value = action.charAt(0).toUpperCase() + action.slice(1)
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/code/assist', {
      action,
      params: action === 'generate'
        ? { description: 'Generate code', language: language.value }
        : { code, language: language.value },
    })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'AI processing failed.' }
  } finally {
    aiLoading.value = false
  }
}

function applyAIResult() {
  const data = aiResult.value
  if (!data) return
  if (data.refactored_code) setCode(data.refactored_code)
  else if (data.code) setCode(data.code)
  else if (data.result) setCode(data.result)
  aiPanelOpen.value = false
}

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer)
  view.value?.destroy()
})
</script>

<style scoped>
.code-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.code-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.lang-select select { padding: 4px 8px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; color: var(--text-primary); font-size: 12px; outline: none; }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 6px; font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.code-body { flex: 1; overflow: hidden; }
.code-editor-container { height: 100%; }
.code-editor-container :deep(.cm-editor) { height: 100%; }
</style>
