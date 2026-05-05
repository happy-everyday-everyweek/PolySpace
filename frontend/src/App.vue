<template>
  <div class="app-container" :class="{ 'dark-mode': isDark }">
    <AppHeader :current-mode="currentMode" />
    <div class="app-body">
      <main class="app-main">
        <router-view v-slot="{ Component, route }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useModeStore } from './stores/mode'
import { useSettingsStore } from './stores/settings'
import AppHeader from './components/common/AppHeader.vue'

const modeStore = useModeStore()
const settingsStore = useSettingsStore()

const currentMode = computed(() => modeStore.currentMode)

const systemPrefersDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

let mediaQuery: MediaQueryList | null = null
function onMediaChange(e: MediaQueryListEvent) {
  systemPrefersDark.value = e.matches
}

const isDark = computed(() => {
  const theme = settingsStore.settings.general.theme
  if (theme === 'dark') return true
  if (theme === 'light') return false
  return systemPrefersDark.value
})

onMounted(() => {
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  systemPrefersDark.value = mediaQuery.matches
  mediaQuery.addEventListener('change', onMediaChange)
})

onUnmounted(() => {
  mediaQuery?.removeEventListener('change', onMediaChange)
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--bg-color);
  color: var(--text-color);
  transition: background-color var(--transition-normal), color var(--transition-normal);
}

.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.app-main {
  flex: 1;
  overflow: auto;
  min-width: 0;
}

.page-fade-enter-active {
  transition: opacity var(--transition-smooth);
}

.page-fade-leave-active {
  transition: opacity var(--transition-fast);
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}
</style>
