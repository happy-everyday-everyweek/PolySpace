import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWorkspaceStore = defineStore('workspace', () => {
  const activeDocument = ref<string | null>(null)
  const activeDocumentType = ref<string | null>(null)
  const activeTab = ref('document')
  const workStartTime = ref<number>(Date.now())
  const completedTasksCount = ref(0)
  const recentActions = ref<string[]>([])

  function setActiveDocument(path: string, type: string) {
    activeDocument.value = path
    activeDocumentType.value = type
  }

  function clearActiveDocument() {
    activeDocument.value = null
    activeDocumentType.value = null
  }

  function setActiveTab(tab: string) {
    if (tab !== activeTab.value) {
      activeTab.value = tab
      workStartTime.value = Date.now()
      addRecentAction(`切换到${getTabLabel(tab)}`)
    }
  }

  function incrementCompletedTasks() {
    completedTasksCount.value++
  }

  function addRecentAction(action: string) {
    recentActions.value.push(action)
    if (recentActions.value.length > 10) {
      recentActions.value = recentActions.value.slice(-10)
    }
  }

  function getWorkDurationMinutes(): number {
    return Math.floor((Date.now() - workStartTime.value) / 60000)
  }

  function getTabLabel(tab: string): string {
    const labels: Record<string, string> = {
      document: '文档编辑',
      video: '剪辑',
      calendar: '日程管理',
      knowledge: '知识库',
      todo: '待办事项',
      email: '邮件处理',
      kanban: '看板管理',
      recorder: '屏幕录制',
      ppt: '演示文稿',
      excel: '电子表格',
      weather: '天气',
      mindmap: '思维导图',
      notes: '笔记',
      contacts: '通讯录',
      focus: '专注计时',
      image: '图片编辑',
      reader: '阅读',
      code: '代码编辑',
      finance: '财务记账',
      calculator: '计算器',
      music: '音乐',
    }
    return labels[tab] || tab
  }

  return {
    activeDocument,
    activeDocumentType,
    activeTab,
    workStartTime,
    completedTasksCount,
    recentActions,
    setActiveDocument,
    clearActiveDocument,
    setActiveTab,
    incrementCompletedTasks,
    addRecentAction,
    getWorkDurationMinutes,
    getTabLabel,
  }
}, {
  persist: {
    key: 'polyspace-workspace',
    paths: ['activeTab', 'activeDocument', 'activeDocumentType', 'completedTasksCount'],
  },
})
