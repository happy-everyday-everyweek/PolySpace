<template>
  <div class="workflow-builder">
    <div class="wf-header">
      <h2>工作流构建器</h2>
      <div class="wf-toolbar">
        <button class="wf-btn" @click="addNode('trigger')">+ 触发器</button>
        <button class="wf-btn" @click="addNode('condition')">+ 条件</button>
        <button class="wf-btn" @click="addNode('action')">+ 动作</button>
        <button class="wf-btn" @click="addNode('loop')">+ 循环</button>
        <button class="wf-btn primary" @click="saveWorkflow">保存</button>
        <button class="wf-btn" @click="runWorkflow">运行</button>
      </div>
    </div>
    <div class="wf-canvas" ref="canvasRef" @drop="onDrop" @dragover.prevent>
      <div v-for="(node, i) in nodes" :key="node.id" class="wf-node" :class="'node-' + node.type" :style="{ left: node.x + 'px', top: node.y + 'px' }" draggable="true" @dragstart="onDragStart($event, i)">
        <div class="node-header">
          <span class="node-type-badge">{{ nodeTypeLabels[node.type] }}</span>
          <button class="node-delete" @click="removeNode(i)">&times;</button>
        </div>
        <div class="node-body">
          <input v-model="node.label" class="node-label" placeholder="节点名称" />
          <select v-model="node.service" class="node-service">
            <option value="">选择服务</option>
            <option v-for="s in services" :key="s" :value="s">{{ s }}</option>
          </select>
          <textarea v-model="node.config" class="node-config" placeholder="配置 (JSON)" rows="2" />
        </div>
        <div v-if="i < nodes.length - 1" class="node-connector">
          <svg width="20" height="30"><line x1="10" y1="0" x2="10" y2="30" stroke="var(--accent-color, #6366f1)" stroke-width="2" stroke-dasharray="4"/></svg>
        </div>
      </div>
      <div v-if="!nodes.length" class="wf-empty">
        拖拽或点击上方按钮添加节点
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/utils/api'

interface WorkflowNode {
  id: string
  type: string
  label: string
  service: string
  config: string
  x: number
  y: number
}

const canvasRef = ref<HTMLElement | null>(null)
const nodes = ref<WorkflowNode[]>([])
const dragIndex = ref(-1)

const nodeTypeLabels: Record<string, string> = {
  trigger: '触发器', condition: '条件', action: '动作', loop: '循环',
}

const services = [
  'email_send', 'webhook_call', 'ai_chat', 'file_read', 'file_write',
  'calendar_event', 'todo_create', 'notification_send', 'data_transform',
  'http_request', 'knowledge_search', 'code_execute',
]

let nodeIdCounter = 0

function addNode(type: string) {
  const yOffset = nodes.value.length * 120 + 20
  nodes.value.push({
    id: `node_${++nodeIdCounter}`,
    type,
    label: '',
    service: '',
    config: '{}',
    x: 40,
    y: yOffset,
  })
}

function removeNode(index: number) {
  nodes.value.splice(index, 1)
}

function onDragStart(e: DragEvent, index: number) {
  dragIndex.value = index
  e.dataTransfer?.setData('text/plain', String(index))
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  const fromIndex = dragIndex.value
  if (fromIndex < 0 || fromIndex >= nodes.value.length) return
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  const node = nodes.value[fromIndex]
  node.x = e.clientX - rect.left - 80
  node.y = e.clientY - rect.top - 30
}

async function saveWorkflow() {
  const workflow = {
    name: '自定义工作流',
    nodes: nodes.value.map(n => ({
      id: n.id,
      type: n.type,
      label: n.label,
      service: n.service,
      config: (() => { try { return JSON.parse(n.config) } catch { return {} } })(),
    })),
    edges: nodes.value.slice(0, -1).map((n, i) => ({ from: n.id, to: nodes.value[i + 1].id })),
  }
  try {
    await api.post('/ai/coordination/workflow/create', workflow)
  } catch { /* ignore */ }
}

async function runWorkflow() {
  try {
    await api.post('/ai/coordination/workflow/execute', { nodes: nodes.value.map(n => n.id) })
  } catch { /* ignore */ }
}
</script>

<style scoped>
.workflow-builder {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.wf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.wf-header h2 {
  font-size: 20px;
  color: var(--text-primary, var(--text-primary));
  margin: 0;
}
.wf-toolbar {
  display: flex;
  gap: 6px;
}
.wf-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 6px;
  background: var(--bg-secondary, var(--border-color));
  color: var(--text-primary, var(--text-primary));
  font-size: 12px;
  cursor: pointer;
}
.wf-btn.primary {
  background: var(--accent-color, #6366f1);
  border-color: var(--accent-color, #6366f1);
  color: #fff;
}
.wf-canvas {
  flex: 1;
  position: relative;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-primary, var(--bg-secondary));
  overflow: auto;
  min-height: 400px;
}
.wf-node {
  position: absolute;
  width: 200px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 8px;
  background: var(--bg-secondary, #16162a);
  cursor: move;
}
.node-trigger { border-left: 3px solid #4ade80; }
.node-condition { border-left: 3px solid #fbbf24; }
.node-action { border-left: 3px solid #60a5fa; }
.node-loop { border-left: 3px solid #c084fc; }
.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border-color, var(--border-color));
}
.node-type-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: var(--bg-tertiary, #1e1e3a);
  color: var(--text-secondary, var(--text-tertiary));
}
.node-delete {
  background: none;
  border: none;
  color: var(--text-secondary, var(--text-tertiary));
  cursor: pointer;
  font-size: 14px;
}
.node-delete:hover { color: #f87171; }
.node-body {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.node-label,
.node-service,
.node-config {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid var(--border-color, var(--border-color));
  border-radius: 4px;
  background: var(--bg-primary, var(--bg-secondary));
  color: var(--text-primary, var(--text-primary));
  font-size: 12px;
  outline: none;
  box-sizing: border-box;
}
.node-config {
  font-family: monospace;
  resize: vertical;
}
.node-connector {
  position: absolute;
  bottom: -30px;
  left: 50%;
  transform: translateX(-50%);
}
.wf-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary, var(--text-tertiary));
  font-size: 14px;
}
</style>
