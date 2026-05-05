import { ref, computed } from 'vue'
import api from '../utils/api'
import type { CalendarEvent, CalendarCategory } from '../types/workspace'

const DEFAULT_CATEGORIES: CalendarCategory[] = [
  { id: 'personal', name: 'Personal', color: '#3b82f6', visible: true },
  { id: 'work', name: 'Work', color: '#10b981', visible: true },
  { id: 'family', name: 'Family', color: '#8b5cf6', visible: true },
  { id: 'meeting', name: 'Meeting', color: '#f59e0b', visible: true },
]

export function useCalendarEvents() {
  const events = ref<CalendarEvent[]>([])
  const categories = ref<CalendarCategory[]>([...DEFAULT_CATEGORIES])
  const loading = ref(false)
  const searchQuery = ref('')

  const filteredEvents = computed(() => {
    const visibleCategories = categories.value.filter(c => c.visible).map(c => c.id)
    let filtered = events.value.filter(e => !e.category || visibleCategories.includes(e.category))
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      filtered = filtered.filter(e =>
        e.title.toLowerCase().includes(q) ||
        e.description?.toLowerCase().includes(q) ||
        e.location?.toLowerCase().includes(q)
      )
    }
    return filtered
  })

  async function fetchEvents(startDate?: string, endDate?: string) {
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      const res = await api.get('/ai/coordination/calendar/events', { params })
      const raw = res.data?.events || []
      events.value = raw.map((e: any) => ({
        id: e.event_id || e.id,
        title: e.title || '',
        start: e.start_time || e.start || '',
        end: e.end_time || e.end || '',
        description: e.description || '',
        location: e.location || '',
        category: e.category || '',
        color: e.color || '',
        allDay: e.allDay || false,
        attendees: e.attendees || [],
        reminders: e.reminders || [],
        timezone: e.timezone || 'UTC',
        source: e.source || 'polyspace',
        isRecurring: e.isRecurring || false,
        hasConflict: e.hasConflict || false,
      }))
    } catch {
      events.value = []
    } finally {
      loading.value = false
    }
  }

  async function createEvent(event: Omit<CalendarEvent, 'id'>): Promise<CalendarEvent | null> {
    try {
      const res = await api.post('/ai/coordination/calendar/events', {
        title: event.title,
        description: event.description || '',
        start_time: event.start,
        end_time: event.end,
        location: event.location || '',
        category: event.category || '',
        timezone: event.timezone || 'UTC',
      })
      const raw = res.data?.event
      if (raw) {
        const newEvent: CalendarEvent = {
          id: raw.event_id || raw.id || Date.now().toString(),
          title: raw.title || event.title,
          start: raw.start_time || raw.start || event.start,
          end: raw.end_time || raw.end || event.end,
          description: raw.description || event.description || '',
          location: raw.location || event.location || '',
          category: event.category || '',
          color: event.color || '',
          allDay: event.allDay || false,
          attendees: event.attendees || [],
          reminders: event.reminders || [],
          timezone: event.timezone || 'UTC',
          source: 'polyspace',
        }
        events.value.push(newEvent)
        return newEvent
      }
      return null
    } catch {
      return null
    }
  }

  async function updateEvent(eventId: string, updates: Partial<CalendarEvent>): Promise<boolean> {
    try {
      await api.patch(`/ai/coordination/calendar/events/${eventId}`, {
        title: updates.title,
        description: updates.description,
        start_time: updates.start,
        end_time: updates.end,
        location: updates.location,
        category: updates.category,
      })
      const idx = events.value.findIndex(e => e.id === eventId)
      if (idx !== -1) {
        events.value[idx] = { ...events.value[idx], ...updates }
      }
      return true
    } catch {
      return false
    }
  }

  async function deleteEvent(eventId: string): Promise<boolean> {
    try {
      await api.delete(`/ai/coordination/calendar/events/${eventId}`)
      events.value = events.value.filter(e => e.id !== eventId)
      return true
    } catch {
      return false
    }
  }

  function getCategoryColor(category?: string): string {
    if (!category) return '#3b82f6'
    const cat = categories.value.find(c => c.id === category)
    return cat?.color || '#3b82f6'
  }

  function getCategoryName(category?: string): string {
    if (!category) return ''
    const cat = categories.value.find(c => c.id === category)
    return cat?.name || category
  }

  function toggleCategoryVisibility(categoryId: string) {
    const cat = categories.value.find(c => c.id === categoryId)
    if (cat) cat.visible = !cat.visible
  }

  function getEventsForDate(date: Date): CalendarEvent[] {
    const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    return filteredEvents.value.filter(e => {
      const eStart = e.start.substring(0, 10)
      const eEnd = e.end.substring(0, 10)
      return dateStr >= eStart && dateStr <= eEnd
    })
  }

  function getEventsForHour(date: Date, hour: number): CalendarEvent[] {
    return filteredEvents.value.filter(e => {
      const es = new Date(e.start)
      const ee = new Date(e.end)
      const ds = new Date(date)
      ds.setHours(0, 0, 0, 0)
      const de = new Date(date)
      de.setHours(23, 59, 59, 999)
      if (!(es <= de && ee >= ds)) return false
      const visibleStart = es > ds ? es : ds
      return visibleStart.getHours() === hour
    })
  }

  function detectConflicts(): Map<string, boolean> {
    const conflictIds = new Set<string>()
    const sorted = [...filteredEvents.value].sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime())
    for (let i = 0; i < sorted.length; i++) {
      for (let j = i + 1; j < sorted.length; j++) {
        const aStart = new Date(sorted[i].start)
        const aEnd = new Date(sorted[i].end)
        const bStart = new Date(sorted[j].start)
        const bEnd = new Date(sorted[j].end)
        if (bStart >= aEnd) break
        if (aStart < bEnd && aEnd > bStart) {
          conflictIds.add(sorted[i].id)
          conflictIds.add(sorted[j].id)
        }
      }
    }
    const result = new Map<string, boolean>()
    conflictIds.forEach(id => result.set(id, true))
    return result
  }

  return {
    events,
    categories,
    loading,
    searchQuery,
    filteredEvents,
    fetchEvents,
    createEvent,
    updateEvent,
    deleteEvent,
    getCategoryColor,
    getCategoryName,
    toggleCategoryVisibility,
    getEventsForDate,
    getEventsForHour,
    detectConflicts,
  }
}
