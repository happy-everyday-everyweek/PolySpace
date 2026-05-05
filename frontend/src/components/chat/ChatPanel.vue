<template>
  <div class="chat-panel">
    <div class="chat-area">
      <DotGrid
        v-if="chatStore.messages.length === 0"
        class="chat-bg"
        :base-color="dotGridBaseColor"
        :active-color="dotGridActiveColor"
        :exclude-rect="excludeRect"
      />

      <div
        class="chat-messages"
        ref="messagesRef"
        @wheel="handleWheel"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
      >
        <div
          v-if="chatStore.hasPreviousConversation && chatStore.messages.length === 0"
          class="prev-conv-banner"
          :class="{ 'pull-ready': pullDistance >= PULL_THRESHOLD }"
          :style="{ transform: `translateY(${pullDistance}px)` }"
          @click="handleRestoreClick"
        >
          <svg class="banner-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
          <span class="banner-text">{{ pullDistance >= PULL_THRESHOLD ? '松开恢复对话' : '返回上一段对话' }}</span>
        </div>

        <div v-if="chatStore.messages.length === 0" class="empty-state">
          <h1 ref="greetingRef" class="greeting-text">Hi, I'm Poly</h1>
        </div>

        <ChatMessage v-for="msg in chatStore.messages" :key="msg.id" :message="msg" />
        <div v-if="chatStore.isLoading" class="thinking-indicator">
          <span class="thinking-text">让我想想</span>
        </div>
      </div>
    </div>
    <ChatInput @send="handleSend" />
    <TaskDetailPanel
      :visible="chatStore.taskPanelVisible"
      :task-id="chatStore.selectedTaskId"
      @close="chatStore.closeTaskPanel()"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch, computed, onMounted, onUnmounted } from 'vue'
import { useChat } from '@/composables/useChat'
import { useChatStore } from '@/stores/chat'
import { useSettingsStore } from '@/stores/settings'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'
import DotGrid from './DotGrid.vue'
import TaskDetailPanel from './TaskDetailPanel.vue'

const { sendMessage } = useChat()
const chatStore = useChatStore()
const settingsStore = useSettingsStore()
const messagesRef = ref<HTMLElement | null>(null)
const greetingRef = ref<HTMLElement | null>(null)

const IDLE_TIMEOUT = 30 * 60 * 1000
const PULL_THRESHOLD = 60

const pullDistance = ref(0)
let idleTimer: ReturnType<typeof setTimeout> | null = null
let touchStartY = 0
let isTouchPulling = false

const isDark = computed(() => settingsStore.settings.general.theme === 'dark')

const dotGridBaseColor = computed(() => isDark.value ? '#3a3a3a' : '#cccccc')
const dotGridActiveColor = computed(() => isDark.value ? '#e0e0e0' : '#1a1a1a')
const excludeRect = ref<{ x: number; y: number; w: number; h: number } | undefined>(undefined)

function updateExcludeRect() {
  if (chatStore.messages.length > 0 || !greetingRef.value) {
    excludeRect.value = undefined
    return
  }
  const el = greetingRef.value
  const padding = 40
  excludeRect.value = {
    x: el.offsetLeft - padding,
    y: el.offsetTop - padding,
    w: el.offsetWidth + padding * 2,
    h: el.offsetHeight + padding * 2,
  }
}

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer)
  if (chatStore.messages.length > 0) {
    idleTimer = setTimeout(() => {
      chatStore.saveAndClearConversation()
    }, IDLE_TIMEOUT)
  }
}

async function handleSend(content: string) {
  await sendMessage(content)
  await nextTick()
  scrollToBottom()
  resetIdleTimer()
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function handleRestoreClick() {
  chatStore.restorePreviousConversation()
  pullDistance.value = 0
  nextTick(scrollToBottom)
}

function handleWheel(e: WheelEvent) {
  if (!chatStore.hasPreviousConversation || chatStore.messages.length > 0) {
    pullDistance.value = 0
    return
  }

  const el = messagesRef.value
  if (!el) return

  if (el.scrollTop <= 0 && e.deltaY < 0) {
    e.preventDefault()
    pullDistance.value = Math.min(pullDistance.value + Math.abs(e.deltaY) * 0.5, PULL_THRESHOLD * 1.5)

    if (pullDistance.value >= PULL_THRESHOLD) {
      chatStore.restorePreviousConversation()
      pullDistance.value = 0
      nextTick(scrollToBottom)
    }
  } else {
    pullDistance.value = Math.max(0, pullDistance.value - 2)
  }
}

function handleTouchStart(e: TouchEvent) {
  if (!chatStore.hasPreviousConversation || chatStore.messages.length > 0) return
  const el = messagesRef.value
  if (!el || el.scrollTop > 0) return

  touchStartY = e.touches[0].clientY
  isTouchPulling = true
}

function handleTouchMove(e: TouchEvent) {
  if (!isTouchPulling) return
  const currentY = e.touches[0].clientY
  const delta = currentY - touchStartY

  if (delta > 0) {
    e.preventDefault()
    pullDistance.value = Math.min(delta * 0.5, PULL_THRESHOLD * 1.5)

    if (pullDistance.value >= PULL_THRESHOLD) {
      chatStore.restorePreviousConversation()
      pullDistance.value = 0
      isTouchPulling = false
      nextTick(scrollToBottom)
    }
  }
}

function handleTouchEnd() {
  isTouchPulling = false
  pullDistance.value = 0
}

watch(() => chatStore.messages.length, () => {
  nextTick(scrollToBottom)
  nextTick(updateExcludeRect)
})

watch(() => chatStore.lastMessageTime, () => {
  resetIdleTimer()
})

onMounted(() => {
  nextTick(updateExcludeRect)
  if (chatStore.messages.length > 0 && chatStore.lastMessageTime > 0) {
    const elapsed = Date.now() - chatStore.lastMessageTime
    if (elapsed >= IDLE_TIMEOUT) {
      chatStore.saveAndClearConversation()
    } else {
      resetIdleTimer()
    }
  }
})

onUnmounted(() => {
  if (idleTimer) {
    clearTimeout(idleTimer)
    idleTimer = null
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.chat-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.chat-messages {
  position: relative;
  z-index: 1;
  height: 100%;
  overflow-y: auto;
  padding: var(--spacing-sm) 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
  animation: fadeIn 0.6s ease;
}

.greeting-text {
  font-size: 42px;
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: -1px;
  line-height: 1.2;
}

.prev-conv-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 0;
  cursor: pointer;
  transition: transform var(--transition-fast);
  user-select: none;
  -webkit-user-select: none;
}

.banner-arrow {
  color: var(--text-tertiary);
  transition: transform var(--transition-smooth), color var(--transition-normal);
  animation: bounceDown 2s ease-in-out infinite;
}

.prev-conv-banner.pull-ready .banner-arrow {
  transform: rotate(180deg);
  color: var(--text-primary);
}

.banner-text {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  transition: color var(--transition-normal);
}

.prev-conv-banner.pull-ready .banner-text {
  color: var(--text-primary);
}

.prev-conv-banner:hover .banner-text {
  color: var(--text-secondary);
}

.prev-conv-banner:hover .banner-arrow {
  color: var(--text-secondary);
}

@keyframes bounceDown {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(3px); }
}

.thinking-indicator {
  display: flex;
  align-items: center;
  padding: var(--spacing-md) 20px;
}

.thinking-text {
  font-size: var(--font-size-base);
  color: var(--text-tertiary);
  animation: thinking-fade 2s ease-in-out infinite;
}

@keyframes thinking-fade {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
