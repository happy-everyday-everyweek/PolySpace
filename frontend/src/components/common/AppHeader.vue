<template>
  <header class="app-header">
    <div class="header-left">
      <button
        class="mode-toggle-btn"
        :class="[currentMode === 'agent' ? 'chat-state' : 'workspace-state']"
        @click="toggleMode"
      >
        <span class="mode-icon" :class="{ 'icon-left': currentMode === 'agent', 'icon-right': currentMode === 'workspace' }">
          <Transition name="icon-fade" mode="out-in">
            <svg v-if="currentMode === 'agent'" key="agent-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
            </svg>
            <svg v-else key="workspace-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1.5"/>
              <rect x="14" y="3" width="7" height="7" rx="1.5"/>
              <rect x="14" y="14" width="7" height="7" rx="1.5"/>
              <rect x="3" y="14" width="7" height="7" rx="1.5"/>
            </svg>
          </Transition>
        </span>

        <span class="mode-label-wrapper">
          <Transition name="text-fade" mode="out-in">
            <span v-if="currentMode === 'agent'" key="agent-text" class="mode-label">AI Agent</span>
            <span v-else key="workspace-text" class="mode-label">工作台</span>
          </Transition>
        </span>
      </button>
    </div>

    <HeaderSearch @execute="handleSearchExecute" />

    <div class="header-right">
      <button class="icon-btn" title="设置" @click="goSettings">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
        </svg>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useModeStore } from '@/stores/mode'
import type { AppMode } from '@/stores/mode'
import HeaderSearch from './HeaderSearch.vue'

const props = defineProps<{
  currentMode: AppMode
}>()

const router = useRouter()
const modeStore = useModeStore()

function toggleMode() {
  const newMode = props.currentMode === 'agent' ? 'workspace' : 'agent'
  modeStore.switchMode(newMode)
  if (newMode === 'agent') {
    router.push('/')
  } else {
    router.push('/workspace')
  }
}

function goSettings() {
  router.push('/settings')
}

function handleSearchExecute(result: any) {
  switch (result.action) {
    case 'toggle_mode':
      toggleMode()
      break
    default:
      break
  }
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 var(--spacing-lg);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-color);
  flex-shrink: 0;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  height: 100%;
  flex-shrink: 0;
}

.mode-toggle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border: none;
  cursor: pointer;
  transition: background var(--transition-normal), box-shadow var(--transition-normal);
  letter-spacing: -0.2px;
  user-select: none;
  position: relative;
  height: 32px;
  width: 100px;
  box-sizing: border-box;
  color: var(--text-primary);
}

.mode-toggle-btn:hover {
  background: var(--bg-secondary);
}

.mode-toggle-btn:active {
  transform: scale(0.96);
}

.chat-state {
  background: var(--bg-secondary);
}

.workspace-state {
  background: var(--bg-secondary);
  flex-direction: row-reverse;
}

.mode-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  box-sizing: border-box;
}

.mode-icon svg {
  width: 16px;
  height: 16px;
}

.mode-label-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.mode-label {
  font-weight: var(--font-weight-semibold);
  white-space: nowrap;
  font-size: var(--font-size-sm);
}

.icon-fade-enter-active,
.icon-fade-leave-active {
  transition: opacity var(--transition-smooth);
}

.icon-fade-enter-from {
  opacity: 0;
}

.icon-fade-leave-to {
  opacity: 0;
}

.text-fade-enter-active,
.text-fade-leave-active {
  transition: opacity var(--transition-smooth);
}

.text-fade-enter-from {
  opacity: 0;
}

.text-fade-leave-to {
  opacity: 0;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  background: transparent;
  cursor: pointer;
  transition: all var(--transition-normal);
  box-sizing: border-box;
}

.icon-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.icon-btn:active {
  transform: scale(0.95);
  background: var(--bg-tertiary);
}
</style>
