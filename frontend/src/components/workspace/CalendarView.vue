<template>
  <div class="calendar-view">
    <div class="cal-sidebar" v-if="showSidebar">
      <div class="sidebar-section">
        <button class="new-event-btn" @click="openCreatePanel(new Date())">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          New Event
        </button>
      </div>
      <div class="sidebar-section">
        <div class="mini-cal-header">
          <button class="mini-nav-btn" @click="miniPrev">
            <svg width="12" height="12" viewBox="0 0 16 16"><path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </button>
          <span class="mini-cal-title">{{ miniMonthTitle }}</span>
          <button class="mini-nav-btn" @click="miniNext">
            <svg width="12" height="12" viewBox="0 0 16 16"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </button>
        </div>
        <div class="mini-cal-grid">
          <div class="mini-day-label" v-for="d in ['S','M','T','W','T','F','S']" :key="d">{{ d }}</div>
          <button
            v-for="(day, i) in miniMonthDays"
            :key="i"
            :class="['mini-day-cell', { 'other-month': !isSameMonth(day, miniDate), 'today': isSameDay(day, today), 'selected': isSameDay(day, currentDate), 'has-events': getEventsForDate(day).length > 0 }]"
            @click="navigateToDate(day)"
          >{{ day.getDate() }}</button>
        </div>
      </div>
      <div class="sidebar-section">
        <h5 class="sidebar-label">Categories</h5>
        <div v-for="cat in categories" :key="cat.id" class="category-row" @click="toggleCategoryVisibility(cat.id)">
          <span class="cat-dot" :style="{ background: cat.visible ? cat.color : 'var(--text-tertiary)' }"></span>
          <span :class="['cat-name', { 'cat-hidden': !cat.visible }]">{{ cat.name }}</span>
        </div>
      </div>
    </div>

    <div class="cal-main">
      <div class="cal-header">
        <div class="header-left">
          <button class="sidebar-toggle" @click="showSidebar = !showSidebar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
          </button>
          <button class="nav-btn" @click="navigatePrevious">
            <svg width="14" height="14" viewBox="0 0 16 16"><path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </button>
          <button class="nav-btn" @click="navigateNext">
            <svg width="14" height="14" viewBox="0 0 16 16"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="2"/></svg>
          </button>
          <h3 class="view-title">{{ viewTitle }}</h3>
          <button class="today-btn" @click="navigateToday">Today</button>
        </div>
        <div class="header-center">
          <div class="search-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input v-model="searchQuery" placeholder="Search events..." class="search-input" />
            <kbd v-if="!searchQuery" class="search-kbd">/</kbd>
          </div>
        </div>
        <div class="header-right">
          <div class="view-switcher">
            <button v-for="m in (['day','week','month'] as ViewMode[])" :key="m" :class="['view-btn', { active: viewMode === m }]" @click="setView(m)">{{ m.charAt(0).toUpperCase() + m.slice(1) }}</button>
          </div>
          <button class="ai-btn" @click="openAiPanel">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            AI
          </button>
        </div>
      </div>

      <div class="cal-body">
        <div class="cal-content" :class="{ 'panel-open': rightPanel !== 'none' }">
          <div v-if="viewMode === 'month'" class="month-view">
            <div class="day-headers">
              <div class="day-header" v-for="d in weekDayLabels" :key="d">{{ d }}</div>
            </div>
            <div class="month-grid">
              <div
                v-for="(day, idx) in monthDays"
                :key="idx"
                :class="['month-cell', { 'other-month': !isSameMonth(day, currentDate), 'today': isSameDay(day, today), 'selected': selectedDate && isSameDay(day, selectedDate) }]"
                @click="selectDate(day)"
              >
                <span class="cell-date">{{ day.getDate() }}</span>
                <div class="cell-events">
                  <template v-if="getEventsForDate(day).length <= 3">
                    <button
                      v-for="ev in getEventsForDate(day)"
                      :key="ev.id"
                      :class="['cell-event', { 'conflict': ev.hasConflict }]"
                      :style="{ borderLeftColor: getCategoryColor(ev.category) }"
                      @click.stop="openEditPanel(ev)"
                    >
                      <span class="cell-event-title">{{ ev.title }}</span>
                    </button>
                  </template>
                  <template v-else>
                    <button
                      v-for="ev in getEventsForDate(day).slice(0, 2)"
                      :key="ev.id"
                      :class="['cell-event', { 'conflict': ev.hasConflict }]"
                      :style="{ borderLeftColor: getCategoryColor(ev.category) }"
                      @click.stop="openEditPanel(ev)"
                    >
                      <span class="cell-event-title">{{ ev.title }}</span>
                    </button>
                    <span class="cell-more" @click.stop="selectDate(day)">+{{ getEventsForDate(day).length - 2 }} more</span>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="viewMode === 'week'" class="week-view">
            <div class="week-header-row">
              <div class="week-time-gutter"></div>
              <div v-for="day in weekDays" :key="day.toISOString()" :class="['week-header-cell', { 'today': isSameDay(day, today) }]">
                <span class="wh-day-name">{{ day.toLocaleString('default', { weekday: 'short' }) }}</span>
                <span :class="['wh-day-num', { 'today-num': isSameDay(day, today) }]">{{ day.getDate() }}</span>
              </div>
            </div>
            <div class="week-body">
              <div class="week-time-gutter">
                <div v-for="h in hours" :key="h" class="week-time-label">{{ formatHour(h) }}</div>
              </div>
              <div v-for="day in weekDays" :key="day.toISOString()" class="week-day-col" @click="openCreatePanel(day)">
                <div v-for="h in hours" :key="h" class="week-hour-cell">
                  <template v-for="ev in getEventsForHour(day, h)" :key="ev.id">
                    <button
                      :class="['week-event', { 'conflict': ev.hasConflict }]"
                      :style="{ borderLeftColor: getCategoryColor(ev.category) }"
                      @click.stop="openEditPanel(ev)"
                    >{{ ev.title }}</button>
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="viewMode === 'day'" class="day-view">
            <div class="day-view-header">
              <span class="dv-day-name">{{ currentDate.toLocaleString('default', { weekday: 'long' }) }}</span>
              <span :class="['dv-day-num', { 'today-num': isSameDay(currentDate, today) }]">{{ currentDate.getDate() }}</span>
            </div>
            <div class="day-view-body">
              <div class="day-time-gutter">
                <div v-for="h in hours" :key="h" class="day-time-label">{{ formatHour(h) }}</div>
              </div>
              <div class="day-hour-cells" @click="openCreatePanel(currentDate)">
                <div v-for="h in hours" :key="h" class="day-hour-cell">
                  <template v-for="ev in getEventsForHour(currentDate, h)" :key="ev.id">
                    <button
                      :class="['day-event', { 'conflict': ev.hasConflict }]"
                      :style="{ borderLeftColor: getCategoryColor(ev.category) }"
                      @click.stop="openEditPanel(ev)"
                    >
                      <span class="de-title">{{ ev.title }}</span>
                      <span class="de-time">{{ formatTimeStr(new Date(ev.start)) }}</span>
                    </button>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="rightPanel === 'event'" class="right-panel">
          <div class="panel-header">
            <h4>{{ eventPanelMode === 'create' ? 'New Event' : eventPanelMode === 'edit' ? 'Edit Event' : selectedEvent?.title }}</h4>
            <button class="close-btn" @click="closePanel">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="panel-body">
            <div class="form-group">
              <label class="form-label">Title</label>
              <input v-model="eventForm.title" class="form-input" placeholder="Event title" ref="titleInput" />
            </div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">Start Date</label>
                <input v-model="eventForm.startDate" type="date" class="form-input" />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">Start Time</label>
                <input v-model="eventForm.startTime" type="time" class="form-input" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label class="form-label">End Date</label>
                <input v-model="eventForm.endDate" type="date" class="form-input" />
              </div>
              <div class="form-group flex-1">
                <label class="form-label">End Time</label>
                <input v-model="eventForm.endTime" type="time" class="form-input" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">Category</label>
              <select v-model="eventForm.category" class="form-input">
                <option value="">None</option>
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Location</label>
              <input v-model="eventForm.location" class="form-input" placeholder="Add location" />
            </div>
            <div class="form-group">
              <label class="form-label">Description</label>
              <textarea v-model="eventForm.description" class="form-textarea" placeholder="Add description" rows="3"></textarea>
            </div>
          </div>
          <div class="panel-footer">
            <template v-if="eventPanelMode === 'create'">
              <button class="btn-cancel" @click="closePanel">Cancel</button>
              <button class="btn-primary" @click="handleCreateEvent" :disabled="!eventForm.title.trim()">Create</button>
            </template>
            <template v-else-if="eventPanelMode === 'edit'">
              <button class="btn-danger" @click="handleDeleteEvent">Delete</button>
              <button class="btn-cancel" @click="closePanel">Cancel</button>
              <button class="btn-primary" @click="handleUpdateEvent" :disabled="!eventForm.title.trim()">Save</button>
            </template>
            <template v-else>
              <button class="btn-danger" @click="handleDeleteEvent">Delete</button>
              <button class="btn-secondary" @click="eventPanelMode = 'edit'">Edit</button>
              <button class="btn-cancel" @click="closePanel">Close</button>
            </template>
          </div>
        </div>

        <div v-if="rightPanel === 'ai'" class="right-panel ai-panel">
          <div class="panel-header">
            <div>
              <h4>PolySpace AI</h4>
              <p class="panel-subtitle">Calendar assistant</p>
            </div>
            <button class="close-btn" @click="closePanel">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="ai-messages" ref="aiMessagesRef">
            <div v-if="aiMessages.length === 0" class="ai-empty">
              <p class="ai-empty-title">Ask AI anything</p>
              <p class="ai-empty-desc">Create events, check schedule, find free time, or get insights.</p>
              <div class="ai-suggestions">
                <button v-for="s in aiSuggestions" :key="s" class="ai-suggestion-btn" @click="sendAiMessage(s)">{{ s }}</button>
              </div>
            </div>
            <div v-for="(msg, i) in aiMessages" :key="i" :class="['ai-msg', msg.role]">
              <div class="ai-msg-bubble">{{ msg.content }}</div>
            </div>
            <div v-if="aiStreaming" class="ai-msg assistant">
              <div class="ai-msg-bubble ai-typing">
                <span class="dot"></span><span class="dot"></span><span class="dot"></span>
              </div>
            </div>
          </div>
          <div class="ai-input-area">
            <div class="ai-input-box">
              <input v-model="aiInput" class="ai-input" placeholder="Ask AI..." @keydown.enter="sendAiMessage()" :disabled="aiStreaming" />
              <button class="ai-send-btn" @click="sendAiMessage()" :disabled="!aiInput.trim() || aiStreaming">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="toastMsg" class="toast">{{ toastMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useCalendar, type ViewMode } from '../../composables/useCalendar'
import { useCalendarEvents } from '../../composables/useCalendarEvents'
import type { CalendarEvent } from '../../types/workspace'
import api from '../../utils/api'

const {
  currentDate, viewMode, today, weekDayLabels, viewTitle,
  isSameDay, isSameMonth, formatDateStr, formatTimeStr, formatHour,
  getMonthDays, getWeekDays, getHours,
  navigatePrevious, navigateNext, navigateToday, setView, navigateToDate,
} = useCalendar()

const {
  categories, searchQuery, filteredEvents,
  fetchEvents, createEvent, updateEvent, deleteEvent,
  toggleCategoryVisibility,
  getEventsForDate, getEventsForHour, getCategoryColor,
} = useCalendarEvents()

const showSidebar = ref(true)
const rightPanel = ref<'none' | 'event' | 'ai'>('none')
const eventPanelMode = ref<'create' | 'edit' | 'view'>('create')
const selectedEvent = ref<CalendarEvent | null>(null)
const selectedDate = ref<Date | null>(null)

const titleInput = ref<HTMLInputElement | null>(null)
const aiMessagesRef = ref<HTMLElement | null>(null)

const monthDays = computed(() => getMonthDays())
const weekDays = computed(() => getWeekDays())
const hours = computed(() => getHours())

const miniDate = ref(new Date())
const miniMonthTitle = computed(() => {
  const d = miniDate.value
  return `${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`
})
const miniMonthDays = computed(() => {
  const year = miniDate.value.getFullYear()
  const month = miniDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const start = new Date(firstDay)
  start.setDate(start.getDate() - start.getDay())
  const days: Date[] = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(start)
    d.setDate(d.getDate() + i)
    days.push(d)
  }
  return days
})

function miniPrev() {
  const d = new Date(miniDate.value)
  d.setMonth(d.getMonth() - 1)
  miniDate.value = d
}
function miniNext() {
  const d = new Date(miniDate.value)
  d.setMonth(d.getMonth() + 1)
  miniDate.value = d
}

const eventForm = ref({
  title: '',
  startDate: '',
  startTime: '09:00',
  endDate: '',
  endTime: '10:00',
  category: '',
  location: '',
  description: '',
})

function resetEventForm(date?: Date) {
  const d = date || new Date()
  const ds = formatDateStr(d)
  eventForm.value = {
    title: '',
    startDate: ds,
    startTime: '09:00',
    endDate: ds,
    endTime: '10:00',
    category: '',
    location: '',
    description: '',
  }
}

function populateEventForm(event: CalendarEvent) {
  const s = new Date(event.start)
  const e = new Date(event.end)
  eventForm.value = {
    title: event.title,
    startDate: formatDateStr(s),
    startTime: formatTimeStr(s),
    endDate: formatDateStr(e),
    endTime: formatTimeStr(e),
    category: event.category || '',
    location: event.location || '',
    description: event.description || '',
  }
}

function selectDate(day: Date) {
  selectedDate.value = day
}

function openCreatePanel(date: Date) {
  resetEventForm(date)
  selectedEvent.value = null
  eventPanelMode.value = 'create'
  rightPanel.value = 'event'
  nextTick(() => titleInput.value?.focus())
}

function openEditPanel(event: CalendarEvent) {
  selectedEvent.value = event
  populateEventForm(event)
  eventPanelMode.value = 'view'
  rightPanel.value = 'event'
}

function openAiPanel() {
  rightPanel.value = 'ai'
}

function closePanel() {
  rightPanel.value = 'none'
  selectedEvent.value = null
  selectedDate.value = null
}

async function handleCreateEvent() {
  if (!eventForm.value.title.trim()) return
  const start = `${eventForm.value.startDate}T${eventForm.value.startTime}`
  const end = `${eventForm.value.endDate}T${eventForm.value.endTime}`
  const result = await createEvent({
    title: eventForm.value.title,
    start,
    end,
    description: eventForm.value.description,
    location: eventForm.value.location,
    category: eventForm.value.category,
    allDay: false,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  })
  if (result) {
    showToast('Event created')
    closePanel()
  } else {
    showToast('Failed to create event')
  }
}

async function handleUpdateEvent() {
  if (!selectedEvent.value || !eventForm.value.title.trim()) return
  const start = `${eventForm.value.startDate}T${eventForm.value.startTime}`
  const end = `${eventForm.value.endDate}T${eventForm.value.endTime}`
  const ok = await updateEvent(selectedEvent.value.id, {
    title: eventForm.value.title,
    start,
    end,
    description: eventForm.value.description,
    location: eventForm.value.location,
    category: eventForm.value.category,
  })
  if (ok) {
    showToast('Event updated')
    closePanel()
  } else {
    showToast('Failed to update event')
  }
}

async function handleDeleteEvent() {
  if (!selectedEvent.value) return
  const ok = await deleteEvent(selectedEvent.value.id)
  if (ok) {
    showToast('Event deleted')
    closePanel()
  } else {
    showToast('Failed to delete event')
  }
}

const aiMessages = ref<{ role: 'user' | 'assistant'; content: string }[]>([])
const aiInput = ref('')
const aiStreaming = ref(false)
const aiSuggestions = ["What's on today?", 'Schedule a meeting', 'Find free time']

async function sendAiMessage(text?: string) {
  const msg = (text || aiInput.value).trim()
  if (!msg || aiStreaming.value) return
  aiMessages.value.push({ role: 'user', content: msg })
  aiInput.value = ''
  aiStreaming.value = true
  try {
    const res = await api.post('/ai/workspace/calendar/assist', {
      action: 'chat',
      params: {
        message: msg,
        current_date: new Date().toISOString(),
        events: filteredEvents.value.map(e => ({ title: e.title, start: e.start, end: e.end, category: e.category })),
      },
    })
    const reply = res.data?.result || res.data?.response || JSON.stringify(res.data)
    aiMessages.value.push({ role: 'assistant', content: reply })
  } catch {
    aiMessages.value.push({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' })
  } finally {
    aiStreaming.value = false
    nextTick(() => {
      aiMessagesRef.value?.scrollTo({ top: aiMessagesRef.value.scrollHeight, behavior: 'smooth' })
    })
  }
}

const toastMsg = ref('')
const toastTimer = ref<ReturnType<typeof setTimeout> | null>(null)
function showToast(msg: string) {
  toastMsg.value = msg
  if (toastTimer.value) clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => { toastMsg.value = '' }, 3000)
}

function handleKeyDown(e: KeyboardEvent) {
  const target = e.target as HTMLElement
  const isTyping = target.isContentEditable || target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement
  if (e.key === 'Escape') {
    if (isTyping) return
    if (rightPanel.value !== 'none') { e.preventDefault(); closePanel(); return }
    return
  }
  if (isTyping) return
  if (e.key === 'n') { e.preventDefault(); openCreatePanel(new Date()) }
  else if (e.key === 't') { e.preventDefault(); navigateToday() }
  else if (e.key === 'd') { e.preventDefault(); setView('day') }
  else if (e.key === 'w') { e.preventDefault(); setView('week') }
  else if (e.key === 'm') { e.preventDefault(); setView('month') }
  else if (e.key === 'g') { e.preventDefault(); openAiPanel() }
  else if (e.key === '/') { e.preventDefault(); document.querySelector<HTMLElement>('.search-input')?.focus() }
}

onMounted(() => {
  fetchEvents()
  window.addEventListener('keydown', handleKeyDown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

watch(viewMode, () => {
  const start = viewMode.value === 'day' ? formatDateStr(currentDate.value) : undefined
  const end = viewMode.value === 'day' ? formatDateStr(currentDate.value) : undefined
  fetchEvents(start, end)
})
</script>

<style scoped>
.calendar-view { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); overflow: hidden; }

.cal-sidebar { width: 220px; flex-shrink: 0; border-right: 1px solid var(--border-color); padding: 12px; display: flex; flex-direction: column; gap: 16px; overflow-y: auto; background: var(--bg-secondary); }
.sidebar-section { display: flex; flex-direction: column; gap: 8px; }
.new-event-btn { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: 8px; background: var(--ws-accent); color: #fff; font-size: 13px; font-weight: 500; border: none; cursor: pointer; transition: background 0.15s; }
.new-event-btn:hover { background: var(--ws-accent-hover); }
.sidebar-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-tertiary); margin: 0; }
.category-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; cursor: pointer; }
.cat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; transition: background 0.15s; }
.cat-name { font-size: 12px; color: var(--text-secondary); transition: opacity 0.15s; }
.cat-hidden { opacity: 0.4; text-decoration: line-through; }

.mini-cal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.mini-cal-title { font-size: 12px; font-weight: 600; color: var(--text-primary); }
.mini-nav-btn { padding: 2px 6px; border-radius: 4px; background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.mini-nav-btn:hover { background: var(--bg-tertiary); }
.mini-cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; }
.mini-day-label { text-align: center; font-size: 10px; color: var(--text-tertiary); padding: 2px 0; }
.mini-day-cell { text-align: center; font-size: 11px; padding: 3px 0; border-radius: 4px; background: none; border: none; color: var(--text-primary); cursor: pointer; transition: background 0.1s; }
.mini-day-cell:hover { background: var(--bg-tertiary); }
.mini-day-cell.other-month { color: var(--text-tertiary); opacity: 0.4; }
.mini-day-cell.today { background: var(--ws-accent); color: #fff; font-weight: 600; }
.mini-day-cell.selected { outline: 2px solid var(--ws-accent); outline-offset: -2px; }
.mini-day-cell.has-events { font-weight: 600; }

.cal-main { flex: 1; display: flex; flex-direction: column; min-width: 0; overflow: hidden; }

.cal-header { display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 1px solid var(--border-color); flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 8px; }
.header-center { flex: 1; display: flex; justify-content: center; }
.header-right { display: flex; align-items: center; gap: 8px; }

.sidebar-toggle { padding: 4px 8px; border-radius: 4px; background: none; border: 1px solid var(--border-color); color: var(--text-tertiary); cursor: pointer; }
.sidebar-toggle:hover { background: var(--bg-secondary); }
.nav-btn { padding: 4px 8px; border-radius: 4px; background: none; border: 1px solid var(--border-color); color: var(--text-tertiary); cursor: pointer; }
.nav-btn:hover { background: var(--bg-secondary); }
.view-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 0; white-space: nowrap; }
.today-btn { padding: 4px 12px; border-radius: 6px; background: none; border: 1px solid var(--border-color); color: var(--text-secondary); font-size: 12px; cursor: pointer; }
.today-btn:hover { background: var(--bg-secondary); border-color: var(--ws-accent); color: var(--ws-accent); }

.search-box { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 8px; border: 1px solid var(--border-color); background: var(--bg-secondary); max-width: 280px; width: 100%; }
.search-box svg { color: var(--text-tertiary); flex-shrink: 0; }
.search-input { flex: 1; border: none; background: none; color: var(--text-primary); font-size: 13px; outline: none; min-width: 0; }
.search-input::placeholder { color: var(--text-tertiary); }
.search-kbd { font-size: 10px; padding: 1px 5px; border-radius: 3px; background: var(--bg-tertiary); color: var(--text-tertiary); border: 1px solid var(--border-color); }

.view-switcher { display: flex; border-radius: 8px; border: 1px solid var(--border-color); overflow: hidden; }
.view-btn { padding: 5px 14px; font-size: 12px; background: none; border: none; color: var(--text-tertiary); cursor: pointer; transition: all 0.15s; border-right: 1px solid var(--border-color); }
.view-btn:last-child { border-right: none; }
.view-btn:hover { background: var(--bg-secondary); }
.view-btn.active { background: var(--ws-accent); color: #fff; }

.ai-btn { display: flex; align-items: center; gap: 4px; padding: 5px 12px; border-radius: 8px; background: none; border: 1px solid var(--border-color); color: var(--ws-accent); font-size: 12px; cursor: pointer; transition: all 0.15s; }
.ai-btn:hover { background: var(--ws-accent-light); border-color: var(--ws-accent); }

.cal-body { flex: 1; display: flex; overflow: hidden; }
.cal-content { flex: 1; overflow: auto; transition: margin-right 0.2s; }
.cal-content.panel-open { margin-right: 0; }

.month-view { height: 100%; display: flex; flex-direction: column; }
.day-headers { display: grid; grid-template-columns: repeat(7, 1fr); border-bottom: 1px solid var(--border-color); }
.day-header { text-align: center; padding: 8px; font-size: 12px; font-weight: 600; color: var(--text-tertiary); }
.month-grid { display: grid; grid-template-columns: repeat(7, 1fr); flex: 1; }
.month-cell { min-height: 80px; padding: 4px 6px; border-right: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.1s; }
.month-cell:nth-child(7n) { border-right: none; }
.month-cell:hover { background: var(--bg-secondary); }
.month-cell.other-month { opacity: 0.35; }
.month-cell.today { background: rgba(59, 130, 246, 0.05); }
.month-cell.selected { outline: 2px solid var(--ws-accent); outline-offset: -2px; }
.cell-date { font-size: 12px; color: var(--text-primary); font-weight: 500; }
.month-cell.today .cell-date { background: var(--ws-accent); color: #fff; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; }
.cell-events { margin-top: 2px; display: flex; flex-direction: column; gap: 1px; }
.cell-event { display: block; text-align: left; padding: 1px 4px 1px 6px; border-left: 3px solid var(--ws-accent); border-radius: 2px; font-size: 11px; color: var(--text-secondary); background: none; cursor: pointer; width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; transition: background 0.1s; }
.cell-event:hover { background: var(--bg-tertiary); }
.cell-event.conflict { border-left-color: var(--ws-danger); }
.cell-event-title { overflow: hidden; text-overflow: ellipsis; }
.cell-more { font-size: 10px; color: var(--ws-accent); padding: 1px 4px; cursor: pointer; }
.cell-more:hover { text-decoration: underline; }

.week-view { height: 100%; display: flex; flex-direction: column; }
.week-header-row { display: grid; grid-template-columns: 56px repeat(7, 1fr); border-bottom: 1px solid var(--border-color); flex-shrink: 0; }
.week-time-gutter { width: 56px; flex-shrink: 0; }
.week-header-cell { text-align: center; padding: 8px 4px; border-left: 1px solid var(--border-color); }
.week-header-cell.today { background: rgba(59, 130, 246, 0.05); }
.wh-day-name { font-size: 10px; color: var(--text-tertiary); display: block; }
.wh-day-num { font-size: 14px; font-weight: 600; color: var(--text-primary); display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 8px; margin-top: 2px; }
.wh-day-num.today-num { background: var(--ws-accent); color: #fff; }
.week-body { display: grid; grid-template-columns: 56px repeat(7, 1fr); flex: 1; overflow-y: auto; }
.week-time-label { height: 44px; text-align: right; padding-right: 8px; font-size: 10px; color: var(--text-tertiary); line-height: 44px; }
.week-day-col { border-left: 1px solid var(--border-color); }
.week-hour-cell { height: 44px; border-bottom: 1px solid var(--border-color); padding: 1px 2px; position: relative; cursor: pointer; transition: background 0.1s; }
.week-hour-cell:hover { background: var(--bg-secondary); }
.week-event { display: block; text-align: left; padding: 1px 4px 1px 6px; border-left: 3px solid var(--ws-accent); border-radius: 2px; font-size: 10px; color: var(--text-secondary); background: none; cursor: pointer; width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.week-event:hover { background: var(--bg-tertiary); }
.week-event.conflict { border-left-color: var(--ws-danger); }

.day-view { height: 100%; display: flex; flex-direction: column; }
.day-view-header { padding: 12px 16px; border-bottom: 1px solid var(--border-color); display: flex; align-items: baseline; gap: 8px; }
.dv-day-name { font-size: 13px; color: var(--text-tertiary); }
.dv-day-num { font-size: 24px; font-weight: 700; color: var(--text-primary); }
.dv-day-num.today-num { background: var(--ws-accent); color: #fff; border-radius: 50%; width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center; }
.day-view-body { display: grid; grid-template-columns: 56px 1fr; flex: 1; overflow-y: auto; }
.day-time-gutter { width: 56px; flex-shrink: 0; }
.day-time-label { height: 52px; text-align: right; padding-right: 8px; font-size: 10px; color: var(--text-tertiary); line-height: 52px; }
.day-hour-cells { border-left: 1px solid var(--border-color); }
.day-hour-cell { height: 52px; border-bottom: 1px solid var(--border-color); padding: 2px 8px; cursor: pointer; transition: background 0.1s; }
.day-hour-cell:hover { background: var(--bg-secondary); }
.day-event { display: block; text-align: left; padding: 4px 8px 4px 10px; border-left: 3px solid var(--ws-accent); border-radius: 4px; font-size: 12px; color: var(--text-secondary); background: none; cursor: pointer; width: 100%; transition: background 0.1s; }
.day-event:hover { background: var(--bg-tertiary); }
.day-event.conflict { border-left-color: var(--ws-danger); }
.de-title { color: var(--text-primary); font-weight: 500; }
.de-time { color: var(--ws-accent); margin-left: 8px; font-size: 11px; }

.right-panel { width: 340px; flex-shrink: 0; border-left: 1px solid var(--border-color); display: flex; flex-direction: column; background: var(--bg-secondary); overflow: hidden; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--border-color); }
.panel-header h4 { margin: 0; font-size: 14px; font-weight: 600; color: var(--text-primary); }
.panel-subtitle { margin: 2px 0 0; font-size: 10px; color: var(--text-tertiary); }
.close-btn { padding: 4px; border-radius: 4px; background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { background: var(--bg-tertiary); color: var(--text-primary); }

.panel-body { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-row { display: flex; gap: 8px; }
.flex-1 { flex: 1; }
.form-label { font-size: 11px; font-weight: 500; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.3px; }
.form-input { padding: 7px 10px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--input-bg); color: var(--text-primary); font-size: 13px; outline: none; transition: border-color 0.15s; }
.form-input:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 2px var(--ws-accent-light); }
.form-textarea { padding: 7px 10px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--input-bg); color: var(--text-primary); font-size: 13px; outline: none; resize: vertical; transition: border-color 0.15s; }
.form-textarea:focus { border-color: var(--ws-accent); box-shadow: 0 0 0 2px var(--ws-accent-light); }

.panel-footer { padding: 12px 16px; border-top: 1px solid var(--border-color); display: flex; gap: 8px; justify-content: flex-end; }
.btn-cancel { padding: 6px 16px; border-radius: 6px; background: var(--bg-tertiary); color: var(--text-secondary); border: none; cursor: pointer; font-size: 13px; }
.btn-cancel:hover { background: var(--border-color); }
.btn-primary { padding: 6px 16px; border-radius: 6px; background: var(--ws-accent); color: #fff; border: none; cursor: pointer; font-size: 13px; }
.btn-primary:hover { background: var(--ws-accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 6px 16px; border-radius: 6px; background: var(--bg-tertiary); color: var(--ws-accent); border: 1px solid var(--border-color); cursor: pointer; font-size: 13px; }
.btn-secondary:hover { border-color: var(--ws-accent); }
.btn-danger { padding: 6px 16px; border-radius: 6px; background: none; color: var(--ws-danger); border: 1px solid var(--ws-danger); cursor: pointer; font-size: 13px; margin-right: auto; }
.btn-danger:hover { background: var(--ws-danger); color: #fff; }

.ai-panel { display: flex; flex-direction: column; }
.ai-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.ai-empty { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 32px 16px; text-align: center; }
.ai-empty-title { font-size: 14px; font-weight: 500; color: var(--text-secondary); margin: 0 0 4px; }
.ai-empty-desc { font-size: 12px; color: var(--text-tertiary); margin: 0 0 16px; max-width: 200px; line-height: 1.5; }
.ai-suggestions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
.ai-suggestion-btn { padding: 5px 10px; border-radius: 6px; border: 1px solid var(--border-color); background: var(--bg-tertiary); color: var(--text-tertiary); font-size: 11px; cursor: pointer; transition: all 0.15s; }
.ai-suggestion-btn:hover { background: var(--bg-secondary); color: var(--text-secondary); border-color: var(--ws-accent); }

.ai-msg { display: flex; }
.ai-msg.user { justify-content: flex-end; }
.ai-msg-bubble { max-width: 85%; padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.5; }
.ai-msg.user .ai-msg-bubble { background: var(--ws-accent); color: #fff; border-bottom-right-radius: 4px; }
.ai-msg.assistant .ai-msg-bubble { background: var(--bg-tertiary); color: var(--text-secondary); border-bottom-left-radius: 4px; }

.ai-typing { display: flex; gap: 4px; padding: 10px 14px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text-tertiary); animation: dotBounce 1.4s infinite ease-in-out both; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes dotBounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.ai-input-area { padding: 12px; border-top: 1px solid var(--border-color); }
.ai-input-box { display: flex; align-items: center; gap: 8px; padding: 6px 10px; border-radius: 10px; border: 1px solid var(--border-color); background: var(--bg-primary); }
.ai-input { flex: 1; border: none; background: none; color: var(--text-primary); font-size: 13px; outline: none; }
.ai-input::placeholder { color: var(--text-tertiary); }
.ai-send-btn { padding: 4px 8px; border-radius: 6px; background: var(--ws-accent); color: #fff; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.ai-send-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); background: var(--card-bg); color: var(--text-primary); padding: 10px 20px; border-radius: 8px; box-shadow: var(--shadow-lg); font-size: 13px; z-index: 300; border: 1px solid var(--border-color); }
</style>
