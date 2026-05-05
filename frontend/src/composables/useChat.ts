import { ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import { API_BASE } from '@/utils/constants'
import type { ChatMessage, EmotionState, InnerVoice, ToolCall, ToolResult } from '@/types/chat'

export function useChat() {
  const chatStore = useChatStore()
  const isTyping = ref(false)
  const isStreaming = ref(false)
  let abortController: AbortController | null = null
  let sendDebounceTimer: ReturnType<typeof setTimeout> | null = null

  async function sendMessageStream(content: string) {
    stopStreaming()
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    chatStore.addMessage(userMessage)
    chatStore.setLoading(true)
    isStreaming.value = true

    const assistantMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      toolCalls: [],
    }
    chatStore.addMessage(assistantMessage)

    abortController = new AbortController()

    try {
      const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          session_id: chatStore.currentSessionId || undefined,
        }),
        signal: abortController.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6)
          try {
            const chunk = JSON.parse(jsonStr)
            handleStreamChunk(chunk, assistantMessage.id)
          } catch {
            // skip malformed chunks
          }
        }
      }
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        // user cancelled
      } else {
        const errorMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'system',
          content: '请求失败，请重试',
          timestamp: Date.now(),
        }
        chatStore.addMessage(errorMessage)
      }
    } finally {
      chatStore.setLoading(false)
      isStreaming.value = false
      abortController = null
    }
  }

  function handleStreamChunk(chunk: { type: string; data: unknown }, messageId: string) {
    const lastIdx = chatStore.messages.findIndex(m => m.id === messageId)
    if (lastIdx < 0) return

    switch (chunk.type) {
      case 'emotion': {
        const emotion = chunk.data as EmotionState
        chatStore.setEmotion(emotion)
        break
      }
      case 'inner_voice': {
        const innerVoice = chunk.data as InnerVoice | null
        if (innerVoice && innerVoice.visibility !== 'private') {
          chatStore.messages[lastIdx].innerVoice = innerVoice
        }
        break
      }
      case 'action': {
        const actionData = chunk.data as { action_type: string }
        chatStore.messages[lastIdx].actionType = actionData.action_type
        break
      }
      case 'tool_call': {
        const toolCallData = chunk.data as { id: string; name: string; arguments: string }
        if (!chatStore.messages[lastIdx].toolCalls) {
          chatStore.messages[lastIdx].toolCalls = []
        }
        let parsedArgs: Record<string, unknown> = {}
        try {
          parsedArgs = JSON.parse(toolCallData.arguments)
        } catch {
          parsedArgs = { raw: toolCallData.arguments }
        }
        chatStore.messages[lastIdx].toolCalls!.push({
          id: toolCallData.id,
          name: toolCallData.name,
          arguments: parsedArgs,
        })
        break
      }
      case 'tool_result': {
        const toolResultData = chunk.data as { tool_call_id: string; name: string; result: unknown; executed: boolean }
        if (!chatStore.messages[lastIdx].toolResults) {
          chatStore.messages[lastIdx].toolResults = []
        }
        chatStore.messages[lastIdx].toolResults!.push({
          toolCallId: toolResultData.tool_call_id,
          name: toolResultData.name,
          result: toolResultData.result,
          error: typeof toolResultData.result === 'object' && toolResultData.result !== null && 'error' in (toolResultData.result as Record<string, unknown>)
            ? String((toolResultData.result as Record<string, unknown>).error)
            : undefined,
        })
        break
      }
      case 'content': {
        const contentData = chunk.data as { content: string }
        chatStore.messages[lastIdx].content += contentData.content
        break
      }
      case 'done': {
        const doneData = chunk.data as {
          session_id: string
          tool_calls: unknown[]
          cards: unknown[]
          reflection: unknown
        }
        if (doneData.session_id) {
          chatStore.setSessionId(doneData.session_id)
        }
        if (doneData.tool_calls && (!chatStore.messages[lastIdx].toolCalls || chatStore.messages[lastIdx].toolCalls!.length === 0)) {
          const parsedToolCalls: ToolCall[] = (doneData.tool_calls as Array<{id: string; name: string; arguments: string; executed?: boolean; result?: unknown}>).map(tc => {
            let parsedArgs: Record<string, unknown> = {}
            try {
              parsedArgs = JSON.parse(tc.arguments)
            } catch {
              parsedArgs = { raw: tc.arguments }
            }
            return {
              id: tc.id,
              name: tc.name,
              arguments: parsedArgs,
            }
          })
          chatStore.messages[lastIdx].toolCalls = parsedToolCalls
        }
        if (doneData.tool_calls && chatStore.messages[lastIdx].toolCalls && chatStore.messages[lastIdx].toolCalls!.length > 0) {
          if (!chatStore.messages[lastIdx].toolResults) {
            chatStore.messages[lastIdx].toolResults = []
          }
          const doneToolCalls = doneData.tool_calls as Array<{id: string; name: string; arguments: string; executed?: boolean; result?: unknown}>
          for (const tc of doneToolCalls) {
            const existingResult = chatStore.messages[lastIdx].toolResults!.find(tr => tr.toolCallId === tc.id)
            if (!existingResult && tc.result !== undefined) {
              chatStore.messages[lastIdx].toolResults!.push({
                toolCallId: tc.id,
                name: tc.name,
                result: tc.result,
                error: typeof tc.result === 'object' && tc.result !== null && 'error' in (tc.result as Record<string, unknown>)
                  ? String((tc.result as Record<string, unknown>).error)
                  : undefined,
              })
            }
          }
        }
        if (doneData.cards && Array.isArray(doneData.cards)) {
          for (const card of doneData.cards) {
            const cardData = card as Record<string, unknown>
            if (cardData.type === 'task') {
              const cardText = `:::card:task\n${JSON.stringify(cardData)}\n:::`
              chatStore.messages[lastIdx].content += '\n' + cardText
            }
          }
        }
        break
      }
      case 'error': {
        const errorData = chunk.data as { message: string }
        chatStore.messages[lastIdx].content += `\n\n[错误] ${errorData.message}`
        break
      }
    }
  }

  async function sendMessage(content: string) {
    if (sendDebounceTimer) {
      clearTimeout(sendDebounceTimer)
    }
    return new Promise<void>((resolve) => {
      sendDebounceTimer = setTimeout(() => {
        sendDebounceTimer = null
        sendMessageStream(content).then(resolve)
      }, 300)
    })
  }

  function stopStreaming() {
    if (abortController) {
      abortController.abort()
      abortController = null
    }
    isStreaming.value = false
    isTyping.value = false
  }

  function clearChat() {
    stopStreaming()
    chatStore.clearMessages()
    chatStore.setSessionId('')
  }

  return {
    messages: chatStore.messages,
    isLoading: chatStore.isLoading,
    isTyping,
    isStreaming,
    sendMessage,
    clearChat,
    stopStreaming,
  }
}
