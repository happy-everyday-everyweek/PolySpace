import { defineStore } from 'pinia'
import { ref } from 'vue'

export type AppMode = 'agent' | 'workspace'

export const useModeStore = defineStore('mode', () => {
  const currentMode = ref<AppMode>('agent')

  function switchMode(mode: AppMode) {
    currentMode.value = mode
  }

  function setMode(mode: AppMode) {
    currentMode.value = mode
  }

  function toggleMode() {
    currentMode.value = currentMode.value === 'agent' ? 'workspace' : 'agent'
  }

  return { currentMode, switchMode, setMode, toggleMode }
}, {
  persist: {
    key: 'polyspace-mode',
    paths: ['currentMode'],
  },
})
