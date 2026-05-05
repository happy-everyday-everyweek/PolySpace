<template>
  <div class="workspace-view">
    <div class="workspace-tabs">
      <div class="tabs-scroll">
        <div
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-item"
          :class="{ active: activeTabId === tab.id }"
          @click="switchTab(tab.id)"
        >
          <svg v-if="tab.appId === 'home'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9,22 9,12 15,12 15,22"/></svg>
          <span class="tab-title">{{ tab.title }}</span>
          <button
            v-if="tab.closable !== false"
            class="tab-close"
            @click.stop="closeTab(tab.id)"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="tabs-actions">
        <button class="tab-add-btn" @click="showAppLauncher = true" title="打开应用">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        </button>
      </div>
    </div>

    <div class="tab-content">
      <template v-for="tab in tabs" :key="tab.id">
        <div v-show="tab.id === activeTabId" class="tab-pane">
          <WorkspaceHome
            v-if="tab.appId === 'home'"
            @open-app="openApp"
          />
          <component
            v-else
            :is="getAppComponent(tab.appId!)"
            :doc-id="tab.docId"
            @open-settings="openSettingsApp"
          />
        </div>
      </template>
    </div>

    <div v-if="showAppLauncher" class="launcher-overlay" @click.self="showAppLauncher = false">
      <div class="launcher-panel">
        <div class="launcher-header">
          <span>打开应用</span>
          <button class="close-btn" @click="showAppLauncher = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="launcher-grid">
          <button
            v-for="app in availableApps"
            :key="app.id"
            class="launcher-item"
            @click="openApp(app); showAppLauncher = false"
          >
            <span class="launcher-icon" v-html="app.icon"></span>
            <span class="launcher-name">{{ app.name }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, markRaw, defineAsyncComponent } from 'vue'
import { useRouter } from 'vue-router'
import WorkspaceHome from './WorkspaceHome.vue'

const router = useRouter()

const lazyComponent = (loader: () => Promise<any>) => markRaw(defineAsyncComponent({ loader, delay: 0 }))

interface Tab {
  id: string
  title: string
  appId?: string
  docId?: string
  closable?: boolean
}

const componentMap: Record<string, any> = {
  home: markRaw(WorkspaceHome),
  document: lazyComponent(() => import('./DocumentEditor.vue')),
  ppt: lazyComponent(() => import('./PptEditor.vue')),
  excel: lazyComponent(() => import('./ExcelEditor.vue')),
  pdf: lazyComponent(() => import('./PdfEditor.vue')),
  video: lazyComponent(() => import('./VideoEditor.vue')),
  image: lazyComponent(() => import('./ImageEditor.vue')),
  music: lazyComponent(() => import('./MusicPlayer.vue')),
  calendar: lazyComponent(() => import('./CalendarView.vue')),
  knowledge: lazyComponent(() => import('./KnowledgeBase.vue')),
  todo: lazyComponent(() => import('./TodoList.vue')),

  email: lazyComponent(() => import('./EmailClient.vue')),
  kanban: lazyComponent(() => import('./KanbanBoard.vue')),
  contacts: lazyComponent(() => import('./ContactsView.vue')),
  reader: lazyComponent(() => import('./ReaderView.vue')),
  mindmap: lazyComponent(() => import('./MindMapView.vue')),
  notes: lazyComponent(() => import('./NotesEditor.vue')),
  focus: lazyComponent(() => import('./FocusTimer.vue')),
  code: lazyComponent(() => import('./CodeEditor.vue')),
  calculator: lazyComponent(() => import('./CalculatorView.vue')),
  finance: lazyComponent(() => import('./FinanceView.vue')),
  weather: lazyComponent(() => import('./WeatherView.vue')),
  map: lazyComponent(() => import('./MapView.vue')),
  wiki: lazyComponent(() => import('./WikiView.vue')),
  screen: lazyComponent(() => import('./ScreenRecorder.vue')),
}

const appNames: Record<string, string> = {
  document: '文档',
  ppt: 'PPT',
  excel: '表格',
  pdf: 'PDF',
  video: '剪辑',
  image: '图片',
  music: '音乐',
  calendar: '日历',
  knowledge: '知识库',
  todo: '待办',
  memo: '备忘录',
  email: '邮件',
  kanban: '看板',
  contacts: '联系人',
  reader: '阅读器',
  mindmap: '思维导图',
  notes: '笔记',
  focus: '专注',
  code: '代码',
  calculator: '计算器',
  finance: '财务',
  weather: '天气',
  map: '地图',
  wiki: '百科',
  screen: '录屏',
}

const availableApps = [
  { id: 'document', name: '文档', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
  { id: 'ppt', name: 'PPT', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>' },
  { id: 'excel', name: '表格', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>' },
  { id: 'pdf', name: 'PDF', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><path d="M9 15h6"/></svg>' },
  { id: 'video', name: '剪辑', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23,7 16,12 23,17"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>' },
  { id: 'image', name: '图片', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>' },
  { id: 'music', name: '音乐', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>' },
  { id: 'calendar', name: '日历', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>' },
  { id: 'knowledge', name: '知识库', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>' },
  { id: 'todo', name: '待办', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>' },
  { id: 'memo', name: '备忘录', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>' },
  { id: 'email', name: '邮件', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' },
  { id: 'kanban', name: '看板', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="12" rx="1"/><rect x="17" y="3" width="5" height="8" rx="1"/></svg>' },
  { id: 'contacts', name: '联系人', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>' },
  { id: 'reader', name: '阅读器', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>' },
  { id: 'mindmap', name: '思维导图', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>' },
  { id: 'notes', name: '笔记', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>' },
  { id: 'focus', name: '专注', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>' },
  { id: 'code', name: '代码', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16,18 22,12 16,6"/><polyline points="8,6 2,12 8,18"/></svg>' },
  { id: 'calculator', name: '计算器', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10.01"/><line x1="12" y1="10" x2="12" y2="10.01"/><line x1="16" y1="10" x2="16" y2="10.01"/><line x1="8" y1="14" x2="8" y2="14.01"/><line x1="12" y1="14" x2="12" y2="14.01"/><line x1="16" y1="14" x2="16" y2="14.01"/><line x1="8" y1="18" x2="8" y2="18.01"/><line x1="12" y1="18" x2="16" y2="18"/></svg>' },
  { id: 'finance', name: '财务', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>' },
  { id: 'weather', name: '天气', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>' },
  { id: 'map', name: '地图', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>' },
  { id: 'wiki', name: '百科', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>' },
  { id: 'screen', name: '录屏', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><circle cx="17" cy="7" r="1.5" fill="currentColor"/></svg>' },
]

const tabs = ref<Tab[]>([
  { id: 'home', title: '首页', appId: 'home', closable: false }
])
const activeTabId = ref('home')
const showAppLauncher = ref(false)

function getAppComponent(appId: string) {
  return componentMap[appId] || WorkspaceHome
}

function switchTab(tabId: string) {
  activeTabId.value = tabId
}

function closeTab(tabId: string) {
  const index = tabs.value.findIndex(t => t.id === tabId)
  if (index === -1) return
  tabs.value.splice(index, 1)
  if (activeTabId.value === tabId) {
    const newIndex = Math.min(index, tabs.value.length - 1)
    activeTabId.value = tabs.value[newIndex]?.id || 'home'
  }
}

function openApp(app: { id: string; name?: string }) {
  const tabId = `${app.id}-${Date.now()}`
  tabs.value.push({
    id: tabId,
    title: app.name || appNames[app.id] || app.id,
    appId: app.id,
    closable: true,
  })
  activeTabId.value = tabId
}

function openSettingsApp() {
  router.push({ path: '/settings', query: { tab: 'app' } })
}
</script>

<style scoped>
.workspace-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-color);
}

.workspace-tabs {
  display: flex;
  align-items: center;
  height: 34px;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  padding: 0 6px;
}

.tabs-scroll {
  display: flex;
  align-items: center;
  gap: 1px;
  overflow-x: auto;
  flex: 1;
}

.tabs-scroll::-webkit-scrollbar {
  height: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  position: relative;
}

.tab-item:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.tab-item.active {
  color: var(--text-primary);
  background: var(--bg-secondary);
  border-bottom-color: var(--primary-color);
}

.tab-item:active {
  transform: scale(0.97);
}

.tab-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  color: var(--text-tertiary);
  opacity: 0;
  transition: all var(--transition-fast);
}

.tab-item:hover .tab-close {
  opacity: 1;
}

.tab-close:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.tab-close:active {
  transform: scale(0.85);
}

.tabs-actions {
  display: flex;
  align-items: center;
  margin-left: 2px;
}

.tab-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 5px;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
}

.tab-add-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.tab-add-btn:active {
  transform: scale(0.95);
}

.tab-content {
  flex: 1;
  overflow: hidden;
}

.tab-pane {
  height: 100%;
  overflow: auto;
}

.launcher-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--overlay-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.launcher-panel {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  padding: 20px;
  min-width: 480px;
  max-width: 600px;
  box-shadow: var(--shadow-lg);
  animation: micro-bounce-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.launcher-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  background: none;
  cursor: pointer;
}

.close-btn:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.close-btn:active {
  transform: scale(0.95);
}

.launcher-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-sm);
}

.launcher-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px var(--spacing-sm);
  border-radius: var(--radius-md);
  background: none;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-smooth);
  color: var(--text-secondary);
}

.launcher-item:hover {
  background: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--text-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.launcher-item:active {
  transform: translateY(0) scale(0.97);
  box-shadow: none;
}

.launcher-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.launcher-item:hover .launcher-icon {
  background: var(--primary-light);
  color: var(--primary-color);
}

.launcher-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}
</style>
