import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AITask {
  id: string
  name: string
  status: 'running' | 'completed' | 'failed'
  progress?: number
  result?: any
  error?: string
  createdAt: Date
  updatedAt: Date
}

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<AITask[]>([])

  const activeTasks = computed(() => tasks.value.filter(t => t.status === 'running'))
  const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed'))
  const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed'))

  function addTask(name: string): string {
    const id = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    tasks.value.push({
      id,
      name,
      status: 'running',
      progress: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
    return id
  }

  function updateTask(id: string, updates: Partial<AITask>) {
    const task = tasks.value.find(t => t.id === id)
    if (task) {
      Object.assign(task, updates, { updatedAt: new Date() })
    }
  }

  function completeTask(id: string, result?: any) {
    updateTask(id, { status: 'completed', progress: 100, result })
    // 3秒后自动移除已完成的任务
    setTimeout(() => {
      removeTask(id)
    }, 3000)
  }

  function failTask(id: string, error?: string) {
    updateTask(id, { status: 'failed', error })
    // 5秒后自动移除失败的任务
    setTimeout(() => {
      removeTask(id)
    }, 5000)
  }

  function removeTask(id: string) {
    const index = tasks.value.findIndex(t => t.id === id)
    if (index > -1) {
      tasks.value.splice(index, 1)
    }
  }

  function clearCompleted() {
    tasks.value = tasks.value.filter(t => t.status !== 'completed')
  }

  return {
    tasks,
    activeTasks,
    completedTasks,
    failedTasks,
    addTask,
    updateTask,
    completeTask,
    failTask,
    removeTask,
    clearCompleted,
  }
})
