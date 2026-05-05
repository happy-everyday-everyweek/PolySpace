import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, EmotionState } from '@/types/chat'

const MAX_MESSAGES = 200

export interface ConversationSnapshot {
  sessionId: string
  messages: ChatMessage[]
  emotion: EmotionState | null
  savedAt: number
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const currentSessionId = ref('')
  const currentEmotion = ref<EmotionState | null>(null)
  const showInnerVoices = ref<Record<string, boolean>>({})
  const lastMessageTime = ref<number>(0)
  const previousConversation = ref<ConversationSnapshot | null>(null)
  const taskPanelVisible = ref(false)
  const selectedTaskId = ref<string | null>(null)

  const messageCount = computed(() => messages.value.length)
  const hasPreviousConversation = computed(() => previousConversation.value !== null)

  function addMessage(message: ChatMessage) {
    messages.value.push(message)
    if (messages.value.length > MAX_MESSAGES) {
      messages.value = messages.value.slice(-MAX_MESSAGES)
    }
    lastMessageTime.value = Date.now()
  }

  function updateLastAssistant(content: string) {
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'assistant') {
        messages.value[i].content += content
        break
      }
    }
  }

  function clearMessages() {
    messages.value = []
    currentEmotion.value = null
    showInnerVoices.value = {}
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function setSessionId(id: string) {
    currentSessionId.value = id
  }

  function setEmotion(emotion: EmotionState) {
    currentEmotion.value = emotion
  }

  function toggleInnerVoice(messageId: string) {
    showInnerVoices.value[messageId] = !showInnerVoices.value[messageId]
  }

  function isInnerVoiceVisible(messageId: string): boolean {
    return !!showInnerVoices.value[messageId]
  }

  function saveAndClearConversation() {
    if (messages.value.length > 0) {
      previousConversation.value = {
        sessionId: currentSessionId.value,
        messages: [...messages.value],
        emotion: currentEmotion.value,
        savedAt: Date.now(),
      }
    }
    messages.value = []
    currentEmotion.value = null
    showInnerVoices.value = {}
    currentSessionId.value = ''
    lastMessageTime.value = 0
  }

  function restorePreviousConversation() {
    if (!previousConversation.value) return
    const prev = previousConversation.value
    previousConversation.value = null
    messages.value = prev.messages
    currentSessionId.value = prev.sessionId
    currentEmotion.value = prev.emotion
    lastMessageTime.value = Date.now()
  }

  function openTaskPanel(taskId: string) {
    selectedTaskId.value = taskId
    taskPanelVisible.value = true
  }

  function closeTaskPanel() {
    taskPanelVisible.value = false
    selectedTaskId.value = null
  }

  return {
    messages,
    isLoading,
    currentSessionId,
    currentEmotion,
    showInnerVoices,
    messageCount,
    lastMessageTime,
    previousConversation,
    hasPreviousConversation,
    addMessage,
    updateLastAssistant,
    clearMessages,
    setLoading,
    setSessionId,
    setEmotion,
    toggleInnerVoice,
    isInnerVoiceVisible,
    saveAndClearConversation,
    restorePreviousConversation,
    taskPanelVisible,
    selectedTaskId,
    openTaskPanel,
    closeTaskPanel,
  }
}, {
  persist: {
    key: 'polyspace-chat',
    paths: ['currentSessionId', 'messages', 'lastMessageTime', 'previousConversation'],
  },
})
