<template>
  <div class="mindmap-view">
    <div class="mindmap-header">
      <h3 class="section-label">Mind Map</h3>
      <button class="add-btn" @click="showAddDialog('root')">+ Node</button>
      <div class="ai-header-group">
        <button class="ai-header-btn" @click="aiGenerate">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          AI Generate
        </button>
        <button class="ai-header-btn" @click="aiToTasks">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
          To Tasks
        </button>
      </div>
    </div>
    <div class="mindmap-canvas" ref="canvasRef">
      <div class="mindmap-root" v-if="rootNode">
        <MindMapNodeComp :node="rootNode" :depth="0" @add-child="onAddChild" @toggle="onToggle" @delete="onDelete" />
      </div>
      <div v-else class="mindmap-empty">
        <p>Click "+ Node" to start creating a mind map</p>
      </div>
    </div>
    <div v-if="showAIPanel" class="ai-panel">
      <div class="ai-panel-header">
        <h4>AI Mind Map Assistant</h4>
        <button class="close-btn" @click="showAIPanel = false">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="ai-panel-content">
        <div v-if="aiLoading" class="ai-loading"><div class="spinner"></div><span>AI is thinking...</span></div>
        <div v-else-if="aiResult" class="ai-result">
          <div v-if="aiResult.root" class="ai-section">
            <h5>Generated Mind Map</h5>
            <button class="apply-btn" @click="applyGeneratedMap">Apply</button>
          </div>
          <div v-if="aiResult.tasks?.length" class="ai-section">
            <h5>Extracted Tasks</h5>
            <div v-for="(t, i) in aiResult.tasks" :key="i" class="task-item">
              <span class="task-title">{{ t.title }}</span>
              <span class="task-priority" :class="t.priority">{{ t.priority }}</span>
            </div>
          </div>
          <div v-if="aiResult.result && !aiResult.root && !aiResult.tasks" class="ai-section"><p>{{ aiResult.result }}</p></div>
        </div>
      </div>
    </div>
    <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
      <div class="dialog-box">
        <h4>{{ dialogTitle }}</h4>
        <input
          ref="dialogInput"
          v-model="dialogValue"
          class="dialog-input"
          :placeholder="dialogPlaceholder"
          @keydown.enter="confirmDialog"
          @keydown.escape="dialogVisible = false"
        />
        <div class="dialog-actions">
          <button class="dialog-cancel" @click="dialogVisible = false">Cancel</button>
          <button class="dialog-confirm" @click="confirmDialog" :disabled="!dialogValue.trim()">Confirm</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineComponent, h, onMounted, watch, nextTick } from 'vue'
import api from '../../utils/api'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import type { MindMapNode } from '../../types/workspace'

const MindMapNodeComp: any = defineComponent({
  name: 'MindMapNodeComp',
  props: { node: { type: Object as () => MindMapNode, required: true }, depth: { type: Number, default: 0 } },
  emits: ['add-child', 'toggle', 'delete'],
  setup(props: any, { emit }: any) {
    return (): any => {
      const colors = ['var(--ws-accent)', 'var(--ws-success)', 'var(--ws-warning)', 'var(--ws-info)', 'var(--ws-danger)', 'var(--ws-accent-soft)']
      const color = colors[props.depth % colors.length]
      return h('div', { class: 'mm-node-wrap' }, [
        h('div', { class: 'mm-node', style: { borderColor: color } }, [
          h('span', { class: 'mm-node-text' }, props.node.text),
          h('div', { class: 'mm-node-actions' }, [
            h('button', { class: 'mm-action-btn', onClick: () => emit('add-child', props.node.id), title: 'Add child' }, '+'),
            h('button', { class: 'mm-action-btn', onClick: () => emit('toggle', props.node.id), title: 'Toggle' }, props.node.collapsed ? '>' : 'v'),
            props.depth > 0 ? h('button', { class: 'mm-action-btn mm-delete', onClick: () => emit('delete', props.node.id), title: 'Delete' }, 'x') : null,
          ]),
        ]),
        !props.node.collapsed && props.node.children.length ? h('div', { class: 'mm-children' },
          props.node.children.map((child: MindMapNode) => h(MindMapNodeComp, { node: child, depth: props.depth + 1, key: child.id, onAddChild: (id: string) => emit('add-child', id), onToggle: (id: string) => emit('toggle', id), onDelete: (id: string) => emit('delete', id) }))
        ) : null,
      ])
    }
  },
})

const rootNode = ref<MindMapNode | null>(null)
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const canvasRef = ref<HTMLElement | null>(null)

const dialogVisible = ref(false)
const dialogValue = ref('')
const dialogTitle = ref('')
const dialogPlaceholder = ref('')
const dialogCallback = ref<((val: string) => void) | null>(null)
const dialogInput = ref<HTMLInputElement | null>(null)

const { saveDoc, loadDoc } = useDocumentPersistence('mindmap')

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    if (rootNode.value) {
      saveDoc('default', { root: rootNode.value, updatedAt: Date.now() })
    }
  }, 1500)
}

watch(rootNode, debouncedSave, { deep: true })

onMounted(async () => {
  const saved = await loadDoc('default')
  if (saved?.root) rootNode.value = saved.root as MindMapNode
})

function genId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }

function showAddDialog(targetId: string) {
  dialogTitle.value = targetId === 'root' && !rootNode.value ? 'Root Node' : 'Child Node'
  dialogPlaceholder.value = 'Enter node text...'
  dialogValue.value = ''
  dialogCallback.value = (text: string) => {
    if (!text.trim()) return
    if (targetId === 'root' && !rootNode.value) {
      rootNode.value = { id: genId(), text: text.trim(), children: [] }
    } else {
      const parent = rootNode.value ? findNode([rootNode.value], targetId) : null
      if (parent) parent.children.push({ id: genId(), text: text.trim(), children: [] })
    }
  }
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function confirmDialog() {
  if (dialogCallback.value && dialogValue.value.trim()) {
    dialogCallback.value(dialogValue.value.trim())
  }
  dialogVisible.value = false
}

function findNode(nodes: MindMapNode[], id: string): MindMapNode | null {
  for (const n of nodes) {
    if (n.id === id) return n
    const found = findNode(n.children, id)
    if (found) return found
  }
  return null
}

function removeNode(nodes: MindMapNode[], id: string): boolean {
  for (let i = 0; i < nodes.length; i++) {
    if (nodes[i].id === id) { nodes.splice(i, 1); return true }
    if (removeNode(nodes[i].children, id)) return true
  }
  return false
}

function onAddChild(parentId: string) {
  showAddDialog(parentId)
}

function onToggle(id: string) {
  const node = rootNode.value ? findNode([rootNode.value], id) : null
  if (node) node.collapsed = !node.collapsed
}

function onDelete(id: string) {
  if (rootNode.value) {
    if (rootNode.value.id === id) { rootNode.value = null; return }
    removeNode(rootNode.value.children, id)
  }
}

async function aiGenerate() {
  dialogTitle.value = 'Generate Mind Map'
  dialogPlaceholder.value = 'Enter topic for mind map generation...'
  dialogValue.value = ''
  dialogCallback.value = async (topic: string) => {
    if (!topic.trim()) return
    aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
    try {
      const res = await api.post('/ai/workspace/mindmap/assist', { action: 'generate', params: { topic } })
      aiResult.value = res.data
    } catch { aiResult.value = { result: 'Generation failed.' } }
    finally { aiLoading.value = false }
  }
  dialogVisible.value = true
  nextTick(() => dialogInput.value?.focus())
}

function applyGeneratedMap() {
  if (aiResult.value?.root) rootNode.value = aiResult.value.root
  showAIPanel.value = false
}

async function aiToTasks() {
  if (!rootNode.value) return
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/mindmap/assist', { action: 'to_tasks', params: { mindmap: rootNode.value } })
    aiResult.value = res.data
  } catch { aiResult.value = { result: 'Task extraction failed.' } }
  finally { aiLoading.value = false }
}
</script>

<style scoped>
.mindmap-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.mindmap-header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.section-label { font-size: 16px; font-weight: 600; margin: 0; flex: 1; }
.add-btn { padding: 6px 12px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; font-size: 13px; border: none; cursor: pointer; }
.add-btn:hover { background: var(--ws-accent-hover); }
.ai-header-group { display: flex; gap: 6px; }
.ai-header-btn { display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: var(--radius-md); font-size: 11px; color: var(--ws-accent); background: none; border: 1px solid var(--border-color); cursor: pointer; }
.ai-header-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }
.mindmap-canvas { flex: 1; overflow: auto; padding: 24px; }
.mindmap-root { display: flex; justify-content: center; }
.mindmap-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-tertiary); }
.mm-node-wrap { margin: 8px 0 8px 24px; }
.mm-node { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--bg-secondary); border: 2px solid; border-radius: var(--radius-lg); }
.mm-node-text { font-size: 13px; color: var(--text-primary); }
.mm-node-actions { display: flex; gap: 2px; }
.mm-action-btn { width: 20px; height: 20px; border-radius: var(--radius-sm); border: none; background: var(--bg-tertiary); color: var(--text-tertiary); font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.mm-action-btn:hover { background: var(--border-color); color: var(--text-primary); }
.mm-delete:hover { background: rgba(239,68,68,0.15); color: var(--ws-danger); }
.mm-children { border-left: 2px solid var(--border-color); margin-left: 16px; padding-left: 8px; }
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
.apply-btn { width: 100%; padding: 8px; background: var(--ws-accent); color: #fff; border: none; border-radius: var(--radius-md); cursor: pointer; font-size: 12px; margin-top: 8px; }
.apply-btn:hover { background: var(--ws-accent-hover); }
.task-item { padding: 6px 8px; background: var(--bg-tertiary); border-radius: var(--radius-sm); margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }
.task-title { font-size: 13px; color: var(--text-secondary); }
.task-priority { font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm); }
.task-priority.high { background: rgba(239,68,68,0.15); color: var(--ws-danger); }
.task-priority.medium { background: rgba(255,152,0,0.15); color: var(--ws-warning); }
.task-priority.low { background: rgba(76,175,80,0.15); color: var(--ws-success); }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 200; }
.dialog-box { background: var(--card-bg); border-radius: var(--radius-xl); padding: 20px; min-width: 360px; box-shadow: var(--shadow-lg); }
.dialog-box h4 { margin: 0 0 12px; font-size: 15px; color: var(--text-primary); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-lg); background: var(--input-bg); color: var(--text-primary); font-size: 14px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 3px var(--ws-accent-light); }
.dialog-actions { display: flex; gap: 8px; margin-top: 14px; justify-content: flex-end; }
.dialog-cancel { padding: 6px 16px; border-radius: var(--radius-md); background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.dialog-cancel:hover { background: var(--border-color); }
.dialog-confirm { padding: 6px 16px; border-radius: var(--radius-md); background: var(--ws-accent); color: #fff; border: none; cursor: pointer; font-size: 13px; }
.dialog-confirm:hover { background: var(--ws-accent-hover); }
.dialog-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
