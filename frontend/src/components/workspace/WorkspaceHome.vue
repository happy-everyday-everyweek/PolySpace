<template>
  <div class="workspace-home">
    <div class="home-header">
      <h2 class="home-title">工作台</h2>
      <div class="view-toggle">
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'grid' }"
          @click="viewMode = 'grid'"
          title="网格视图"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
          </svg>
        </button>
        <button
          class="toggle-btn"
          :class="{ active: viewMode === 'category' }"
          @click="viewMode = 'category'"
          title="分类视图"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="8" y1="6" x2="21" y2="6"/>
            <line x1="8" y1="12" x2="21" y2="12"/>
            <line x1="8" y1="18" x2="21" y2="18"/>
            <line x1="3" y1="6" x2="3.01" y2="6"/>
            <line x1="3" y1="12" x2="3.01" y2="12"/>
            <line x1="3" y1="18" x2="3.01" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <div v-if="viewMode === 'grid'" class="apps-grid">
      <div
        v-for="app in apps"
        :key="app.id"
        class="app-card"
        @click="openApp(app)"
      >
        <div class="app-icon" v-html="app.icon"></div>
        <span class="app-name">{{ app.name }}</span>
        <span class="app-desc">{{ app.description }}</span>
      </div>
    </div>

    <div v-else class="apps-category">
      <div v-for="category in categories" :key="category.name" class="category-section">
        <h3 class="category-title">{{ category.name }}</h3>
        <div class="category-apps">
          <div
            v-for="app in category.apps"
            :key="app.id"
            class="app-card small"
            @click="openApp(app)"
          >
            <div class="app-icon" v-html="app.icon"></div>
            <span class="app-name">{{ app.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export interface App {
  id: string
  name: string
  description: string
  icon: string
  category: string
}

const emit = defineEmits<{
  openApp: [app: App]
}>()

const viewMode = ref<'grid' | 'category'>('grid')

const apps: App[] = [
  { id: 'document', name: '文档', description: 'Word文档编辑', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>', category: '文档' },
  { id: 'ppt', name: 'PPT', description: '演示文稿', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>', category: '文档' },
  { id: 'excel', name: '表格', description: 'Excel电子表格', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>', category: '文档' },
  { id: 'pdf', name: 'PDF', description: 'PDF阅读与编辑', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><path d="M9 15h6"/></svg>', category: '文档' },
  { id: 'video', name: '剪辑', description: '视频剪辑', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23,7 16,12 23,17"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>', category: '多媒体' },
  { id: 'image', name: '图片', description: '图片编辑', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>', category: '多媒体' },
  { id: 'music', name: '音乐', description: '音乐播放', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>', category: '多媒体' },
  { id: 'calendar', name: '日历', description: '日程管理', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>', category: '信息' },
  { id: 'knowledge', name: '知识库', description: '知识管理', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>', category: '信息' },
  { id: 'todo', name: '待办', description: '任务管理', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>', category: '信息' },

  { id: 'email', name: '邮件', description: '邮件客户端', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>', category: '信息' },
  { id: 'kanban', name: '看板', description: '项目管理', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="5" height="18" rx="1"/><rect x="10" y="3" width="5" height="12" rx="1"/><rect x="17" y="3" width="5" height="8" rx="1"/></svg>', category: '信息' },
  { id: 'contacts', name: '联系人', description: '通讯录', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>', category: '信息' },
  { id: 'reader', name: '阅读器', description: 'RSS阅读', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>', category: '信息' },
  { id: 'mindmap', name: '思维导图', description: '思维导图', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>', category: '视觉' },
  { id: 'notes', name: '笔记', description: 'AI 智能笔记', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><path d="M12 18v-6"/><path d="M9 15h6"/></svg>', category: '信息' },
  { id: 'focus', name: '专注', description: '番茄钟', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>', category: '时间' },
  { id: 'code', name: '代码', description: '代码编辑器', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="16,18 22,12 16,6"/><polyline points="8,6 2,12 8,18"/></svg>', category: '开发' },
  { id: 'calculator', name: '计算器', description: '科学计算', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="8" y2="10.01"/><line x1="12" y1="10" x2="12" y2="10.01"/><line x1="16" y1="10" x2="16" y2="10.01"/><line x1="8" y1="14" x2="8" y2="14.01"/><line x1="12" y1="14" x2="12" y2="14.01"/><line x1="16" y1="14" x2="16" y2="14.01"/><line x1="8" y1="18" x2="8" y2="18.01"/><line x1="12" y1="18" x2="16" y2="18"/></svg>', category: '开发' },
  { id: 'finance', name: '财务', description: '财务管理', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>', category: '生活' },
  { id: 'weather', name: '天气', description: '天气预报', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>', category: '生活' },
  { id: 'map', name: '地图', description: '地图与导航', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>', category: '生活' },
  { id: 'wiki', name: '百科', description: '百科知识', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/><path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>', category: '生活' },
  { id: 'screen', name: '录屏', description: '屏幕录制', icon: '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><circle cx="17" cy="7" r="1.5" fill="currentColor"/></svg>', category: '系统' },
]

const categories = [
  { name: '文档编辑', apps: apps.filter(a => a.category === '文档') },
  { name: '多媒体', apps: apps.filter(a => a.category === '多媒体') },
  { name: '信息管理', apps: apps.filter(a => a.category === '信息') },
  { name: '时间管理', apps: apps.filter(a => a.category === '时间') },
  { name: '开发工具', apps: apps.filter(a => a.category === '开发') },
  { name: '生活助手', apps: apps.filter(a => a.category === '生活') },
  { name: '系统工具', apps: apps.filter(a => a.category === '系统') },
]

function openApp(app: App) {
  emit('openApp', app)
}
</script>

<style scoped>
.workspace-home {
  padding: var(--spacing-lg);
  overflow-y: auto;
  height: 100%;
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

.home-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.view-toggle {
  display: flex;
  gap: 2px;
  background: var(--bg-secondary);
  padding: 3px;
  border-radius: var(--radius-sm);
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 5px;
  color: var(--text-secondary);
  transition: all var(--transition-normal);
}

.toggle-btn:hover {
  color: var(--text-primary);
}

.toggle-btn.active {
  background: var(--bg-color);
  color: var(--text-primary);
  box-shadow: var(--shadow);
}

.toggle-btn:active {
  transform: scale(0.95);
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: var(--spacing-sm);
}

.app-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  padding: var(--spacing-md) var(--spacing-sm);
  border-radius: var(--radius-md);
  background: var(--card-bg);
  cursor: pointer;
  transition: all var(--transition-smooth);
  text-align: center;
  border: 1px solid transparent;
}

.app-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.app-card:active {
  transform: translateY(0) scale(0.97);
  box-shadow: none;
}

.app-card.small {
  padding: 10px var(--spacing-sm);
}

.app-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.app-card.small .app-icon {
  width: 36px;
  height: 36px;
}

.app-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  line-height: 1.3;
}

.app-desc {
  font-size: 10px;
  color: var(--text-tertiary);
  line-height: 1.2;
}

.apps-category {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.category-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.category-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-secondary);
}

.category-apps {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: var(--spacing-sm);
}
</style>
