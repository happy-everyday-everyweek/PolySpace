import { createRouter, createWebHistory } from 'vue-router'
import { useModeStore } from '@/stores/mode'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'agent',
      component: () => import('@/views/AgentView.vue'),
    },
    {
      path: '/workspace',
      name: 'workspace',
      component: () => import('@/views/WorkspaceView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  const modeStore = useModeStore()
  if (to.name === 'workspace' && modeStore.currentMode !== 'workspace') {
    modeStore.switchMode('workspace')
  } else if (to.name === 'agent' && modeStore.currentMode !== 'agent') {
    modeStore.switchMode('agent')
  }
})

export default router
