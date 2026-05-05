<template>
  <div class="ai-panel">
    <div class="ai-header">
      <div class="mode-switch">
        <button class="mode-btn" :class="{ active: aiMode === 'result' }" @click="$emit('close')">分析</button>
        <button class="mode-btn" :class="{ active: aiMode === 'chat' }" @click="$emit('close')">对话</button>
      </div>
      <button class="ai-close" @click="$emit('close')" title="关闭">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <div v-if="aiLoading" class="ai-loading">
      <svg class="spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-dasharray="30 70"/></svg>
      <span>AI 正在分析...</span>
    </div>
    <template v-else>
      <div v-if="aiMode === 'result' && aiResult" class="ai-result">
        <div class="ai-section">
          <div class="section-title">AI 分析结果</div>
          <div class="ai-content">{{ aiResult?.result || '暂无分析结果' }}</div>
        </div>
        <div v-if="aiResult?.suggestions?.length" class="ai-section">
          <div class="section-title">建议操作</div>
          <div class="suggestion-list">
            <div v-for="(s, i) in aiResult.suggestions" :key="i" class="suggestion-item">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <span>{{ s }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="aiMode === 'chat'" class="ai-chat">
        <div class="chat-messages">
          <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
            <div class="msg-bubble">{{ msg.content }}</div>
          </div>
        </div>
        <div class="chat-input-wrap">
          <input class="chat-input" v-model="chatInput" @keyup.enter="sendChat" placeholder="输入消息..." />
          <button class="chat-send" @click="sendChat">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>
      </div>
      <div v-else class="ai-empty">点击"分析"开始 AI 辅助剪辑</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AIAnalysisResult, ChatMessage, AISubtitle, AIEditStep } from '../../../composables/useEditorCore'

defineProps<{
  aiMode: 'result' | 'chat'
  aiLoading: boolean
  aiResult: AIAnalysisResult | null
  chatMessages: ChatMessage[]
}>()

const emit = defineEmits<{
  close: []
  'send-chat': [msg: string]
  'apply-auto-edit': [plan: AIEditStep[]]
  'apply-subtitles': [subs: AISubtitle[]]
}>()

const chatInput = ref('')

function sendChat() {
  if (chatInput.value.trim()) {
    emit('send-chat', chatInput.value.trim())
    chatInput.value = ''
  }
}
</script>

<style scoped>
.ai-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-color);
}

.mode-switch {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  padding: 2px;
}

.mode-btn {
  padding: 4px 12px;
  font-size: 12px;
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.mode-btn.active {
  background: var(--bg-primary);
  color: var(--text-primary);
  box-shadow: var(--shadow);
}

.mode-btn:hover:not(.active) { color: var(--text-primary); }

.ai-close {
  color: var(--text-tertiary);
  transition: color var(--transition-fast);
}

.ai-close:hover { color: var(--text-primary); }

.ai-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 24px;
  color: var(--text-secondary);
  font-size: 13px;
  justify-content: center;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.ai-result { padding: 12px; overflow-y: auto; flex: 1; }

.ai-section { margin-bottom: 16px; }

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.ai-content {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.6;
}

.suggestion-list { display: flex; flex-direction: column; gap: 6px; }

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-primary);
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

.suggestion-item svg { color: var(--primary); }

.ai-chat { display: flex; flex-direction: column; height: 100%; }

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-msg { max-width: 85%; }

.chat-msg.user { align-self: flex-end; }

.msg-bubble {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
}

.chat-msg.user .msg-bubble {
  background: var(--primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-msg.ai .msg-bubble {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-bottom-left-radius: 4px;
}

.chat-input-wrap {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-top: 1px solid var(--border-color);
}

.chat-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
}

.chat-input:focus { border-color: var(--primary); outline: none; }

.chat-send {
  padding: 8px;
  border-radius: var(--radius-md);
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-fast);
}

.chat-send:hover { background: var(--primary-hover); }

.ai-empty {
  text-align: center;
  padding: 40px 12px;
  color: var(--text-tertiary);
  font-size: 13px;
}
</style>
