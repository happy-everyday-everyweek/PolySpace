<template>
  <div class="chat-input-wrapper">
    <!-- AI任务浮动显示 -->
    <AITaskFloat />

    <!-- 输入框主体 -->
    <div class="chat-input-container">
      <div v-if="showSlashMenu" class="slash-menu">
        <button
          v-for="cmd in filteredCommands"
          :key="cmd.key"
          class="slash-item"
          @click="selectCommand(cmd)"
        >
          <span class="slash-label">{{ cmd.label }}</span>
          <span class="slash-desc">{{ cmd.description }}</span>
        </button>
      </div>

      <div class="input-area">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-textarea"
          :placeholder="placeholder"
          rows="1"
          @keydown="handleKeydown"
          @input="handleInput"
        />

        <!-- 底部工具栏 -->
        <div class="input-toolbar">
          <div class="toolbar-left">
            <!-- 斜杠命令按钮 - 参考图片中的方形图标 -->
            <button class="toolbar-btn slash-btn" title="命令" @click="toggleSlashMenu">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" stroke-width="2"/>
                <line x1="8" y1="12" x2="16" y2="12" stroke-width="2"/>
              </svg>
            </button>
          </div>

          <div class="toolbar-right">
            <!-- 语音输入按钮 -->
            <button class="toolbar-btn" title="语音输入">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                <path d="M19 10v2a7 7 0 01-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>

            <!-- 发送按钮 -->
            <button
              class="send-btn"
              :class="{ 'send-active': justSent }"
              :disabled="!inputText.trim()"
              @click="handleSend"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { SLASH_COMMANDS } from '@/utils/constants'
import { useChatStore } from '@/stores/chat'
import AITaskFloat from './AITaskFloat.vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const router = useRouter()
const chatStore = useChatStore()
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const showSlashMenu = ref(false)
const justSent = ref(false)

const placeholder = '输入消息，或输入 / 查看命令...'

const filteredCommands = computed(() => {
  if (!inputText.value.startsWith('/')) return SLASH_COMMANDS
  const query = inputText.value.slice(1).toLowerCase()
  return SLASH_COMMANDS.filter(cmd =>
    cmd.label.includes(query) || cmd.key.includes(query)
  )
})

function handleInput() {
  showSlashMenu.value = inputText.value.startsWith('/')
  autoResize()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text) return
  inputText.value = ''
  showSlashMenu.value = false
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
  justSent.value = true
  emit('send', text)
  setTimeout(() => { justSent.value = false }, 300)
}

function toggleSlashMenu() {
  showSlashMenu.value = !showSlashMenu.value
  if (showSlashMenu.value) {
    inputText.value = '/'
    inputRef.value?.focus()
  }
}

function selectCommand(cmd: typeof SLASH_COMMANDS[number]) {
  showSlashMenu.value = false
  inputText.value = ''

  switch (cmd.key) {
    case 'settings':
      router.push('/settings')
      break
    case 'clear':
      chatStore.clearMessages()
      break
    case 'mode':
      break
  }
}

function autoResize() {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 200) + 'px'
  }
}
</script>

<style scoped>
.chat-input-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

.chat-input-container {
  position: relative;
}

.input-area {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow);
  transition: all var(--transition-normal);
}

.input-area:focus-within {
  border-color: var(--text-tertiary);
  box-shadow: var(--shadow-md);
}

.chat-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 200px;
  resize: none;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.6;
  outline: none;
  padding: 0;
  margin-bottom: var(--spacing-md);
}

.chat-textarea::placeholder {
  color: var(--text-tertiary);
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  background: transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-secondary);
}

.toolbar-btn:active:not(:disabled) {
  transform: scale(0.95);
  background: var(--bg-tertiary);
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--primary-color);
  color: white;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.send-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.send-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  background: var(--text-tertiary);
}

.send-btn.send-active {
  animation: send-pulse 0.3s ease;
}

@keyframes send-pulse {
  0% { transform: scale(1); }
  30% { transform: scale(0.88); }
  60% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.slash-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  margin-bottom: var(--spacing-sm);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  animation: scaleIn 0.2s ease;
}

.slash-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  width: 100%;
  padding: var(--spacing-md) var(--spacing-lg);
  text-align: left;
  color: var(--text-color);
  transition: background var(--transition-fast);
  cursor: pointer;
}

.slash-item:hover {
  background: var(--bg-secondary);
}

.slash-item:first-child {
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.slash-item:last-child {
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
}

.slash-label {
  font-weight: var(--font-weight-medium);
  min-width: 80px;
  font-size: var(--font-size-base);
}

.slash-desc {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
