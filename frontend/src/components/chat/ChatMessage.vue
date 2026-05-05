<template>
  <div class="chat-message" :class="[`role-${message.role}`]">
    <div class="message-body">
      <div v-if="hasToolCalls" class="tool-calls-section">
        <div v-for="(tc, idx) in message.toolCalls" :key="tc.id || idx" class="tool-call-wrapper">
          <ToolResultItem
            :tool-call="tc"
            :tool-result="getToolResult(tc.id)"
          />
        </div>
      </div>
      <div class="message-content">
        <template v-for="(block, idx) in contentBlocks" :key="idx">
          <div v-if="block.type === 'text'" class="content-text" v-html="renderTextBlock(block.content)"></div>
          <div v-else-if="block.type === 'html'" class="content-html">
            <div class="html-preview-header">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
              </svg>
              <span class="html-preview-label">HTML 预览</span>
              <button class="html-toggle-btn" @click="toggleHtmlPreview(idx)">
                {{ htmlPreviewState[idx] !== false ? '查看代码' : '预览效果' }}
              </button>
              <button class="html-open-btn" @click="openHtmlFullscreen(block.content)" title="全屏打开">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
                </svg>
              </button>
            </div>
            <div v-if="htmlPreviewState[idx] !== false" class="html-preview-frame">
              <iframe :srcdoc="block.content" sandbox="allow-scripts" class="html-iframe" />
            </div>
            <div v-else class="html-code-view">
              <pre><code>{{ block.content }}</code></pre>
            </div>
          </div>
          <div v-else-if="block.type === 'math'" class="content-math" :class="{ 'math-display': block.mathDisplay }">
            <div v-html="renderMathBlock(block.content, !!block.mathDisplay)"></div>
          </div>
          <div v-else-if="block.type === 'card' && block.cardType === 'task'" class="content-card">
            <TaskCard
              :data="getCardData(block)"
              @click="handleTaskCardClick"
            />
          </div>
        </template>
      </div>
      <div v-if="message.innerVoice && message.innerVoice.visibility !== 'private'" class="inner-voice-section">
        <button class="inner-voice-toggle" @click="chatStore.toggleInnerVoice(message.id)">
          <svg viewBox="0 0 16 16" width="14" height="14" class="inner-voice-icon">
            <path d="M8 1a5 5 0 0 0-5 5v3l-1 2h12l-1-2V6a5 5 0 0 0-5-5z" fill="none" stroke="currentColor" stroke-width="1.2"/>
            <path v-if="innerVoiceVisible" d="M6 12a2 2 0 0 0 4 0" fill="none" stroke="currentColor" stroke-width="1.2"/>
          </svg>
          <span class="inner-voice-label">{{ innerVoiceVisible ? '收起内心' : '看看内心' }}</span>
        </button>
        <div v-if="innerVoiceVisible" class="inner-voice-content">
          {{ message.innerVoice.text }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useChatStore } from '@/stores/chat'
import type { ChatMessage, ToolResult } from '@/types/chat'
import { parseContent, renderMarkdown, renderMath, parseCardData } from '@/utils/contentRenderer'
import type { ContentBlock, CardData } from '@/utils/contentRenderer'
import TaskCard from './cards/TaskCard.vue'
import ToolResultItem from './ToolResult.vue'

const props = defineProps<{ message: ChatMessage }>()
const chatStore = useChatStore()

const innerVoiceVisible = computed(() => chatStore.isInnerVoiceVisible(props.message.id))

const hasToolCalls = computed(() => props.message.role === 'assistant' && props.message.toolCalls && props.message.toolCalls.length > 0)

function getToolResult(toolCallId: string): ToolResult | undefined {
  return props.message.toolResults?.find(tr => tr.toolCallId === toolCallId)
}

function handleTaskCardClick(data: CardData) {
  const taskId = String(data.task_id || '')
  if (taskId) {
    chatStore.openTaskPanel(taskId)
  }
}

const contentBlocks = computed<ContentBlock[]>(() => {
  if (props.message.role !== 'assistant') {
    return [{ type: 'text' as const, content: props.message.content }]
  }
  return parseContent(props.message.content)
})

const htmlPreviewState = reactive<Record<number, boolean>>({})

function toggleHtmlPreview(idx: number) {
  htmlPreviewState[idx] = htmlPreviewState[idx] !== false ? false : true
}

function renderTextBlock(content: string): string {
  return renderMarkdown(content)
}

function renderMathBlock(formula: string, displayMode: boolean): string {
  return renderMath(formula, displayMode)
}

function getCardData(block: ContentBlock): CardData {
  return parseCardData(block.content)
}

function openHtmlFullscreen(html: string) {
  const win = window.open('', '_blank')
  if (win) {
    win.document.write(html)
    win.document.close()
  }
}
</script>

<style scoped>
.chat-message {
  padding: var(--spacing-sm) var(--spacing-lg);
  animation: slide-up 0.25s ease both;
}

.chat-message.role-user {
  display: flex;
  justify-content: flex-end;
}

.chat-message.role-assistant {
  display: flex;
  justify-content: flex-start;
}

.message-body {
  max-width: 85%;
  min-width: 0;
}

.message-content {
  line-height: 1.7;
  font-size: var(--font-size-base);
  word-break: break-word;
}

.role-user .message-content {
  padding: var(--spacing-md) var(--spacing-lg);
  background: var(--primary-color);
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.role-user .message-content :deep(code) {
  background: rgba(255,255,255,0.2);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: var(--font-size-sm);
}

.role-assistant .message-content {
  color: var(--text-color);
}

.content-text :deep(p) {
  margin: 0 0 var(--spacing-sm) 0;
}

.content-text :deep(p:last-child) {
  margin-bottom: 0;
}

.content-text :deep(pre.code-block) {
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  overflow-x: auto;
  margin: var(--spacing-sm) 0;
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.content-text :deep(pre.code-block code) {
  font-family: var(--font-code);
}

.content-text :deep(code) {
  background: var(--bg-tertiary);
  padding: 1px 5px;
  border-radius: 3px;
  font-size: var(--font-size-sm);
  font-family: var(--font-code);
}

.content-text :deep(pre.code-block code) {
  background: none;
  padding: 0;
}

.content-html {
  margin: var(--spacing-sm) 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--card-bg);
}

.html-preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: var(--font-size-sm);
}

.html-preview-label {
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
  flex: 1;
}

.html-toggle-btn {
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  border: none;
  transition: all var(--transition-fast);
}

.html-toggle-btn:hover {
  opacity: 0.9;
}

.html-toggle-btn:active {
  transform: scale(0.95);
}

.html-open-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  border: none;
  background: none;
}

.html-open-btn:hover {
  background: var(--bg-tertiary);
  color: var(--text-color);
}

.html-preview-frame {
  min-height: 150px;
  max-height: 400px;
}

.html-iframe {
  width: 100%;
  min-height: 150px;
  max-height: 400px;
  border: none;
  background: var(--card-bg);
}

.html-code-view {
  max-height: 300px;
  overflow: auto;
  padding: 10px;
}

.html-code-view pre {
  margin: 0;
  font-size: var(--font-size-sm);
  line-height: 1.5;
}

.html-code-view code {
  font-family: var(--font-code);
  color: var(--text-secondary);
}

.content-math {
  margin: 6px 0;
  overflow-x: auto;
}

.content-math.math-display {
  text-align: center;
  padding: var(--spacing-sm) 0;
}

.content-card {
  margin: var(--spacing-sm) 0;
  display: block;
}

.tool-calls-section {
  margin-bottom: var(--spacing-sm);
}

.tool-call-wrapper {
  margin: 2px 0;
}

.content-card :deep(.card) {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md) 14px;
  box-shadow: var(--shadow);
}

.inner-voice-section {
  margin-top: 6px;
}

.inner-voice-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
}

.inner-voice-toggle:hover {
  color: var(--text-secondary);
  background: var(--bg-tertiary);
}

.inner-voice-toggle:active {
  transform: scale(0.95);
}

.inner-voice-icon {
  opacity: 0.7;
}

.inner-voice-label {
  font-size: var(--font-size-xs);
}

.inner-voice-content {
  margin-top: 6px;
  padding: 10px 14px;
  background: var(--bg-inner-voice);
  border-left: 3px solid var(--text-tertiary);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  animation: fadeSlideIn var(--transition-smooth);
}
</style>
