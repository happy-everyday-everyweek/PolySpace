import { computed, ref } from 'vue'

export type ViewMode = 'day' | 'week' | 'month'

export function useCalendar() {
  const currentDate = ref(new Date())
  const viewMode = ref<ViewMode>('month')

  const today = new Date()

  const weekDayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  const monthTitle = computed(() => {
    const d = currentDate.value
    return `${d.getFullYear()} ${d.toLocaleString('default', { month: 'long' })}`
  })

  const dayTitle = computed(() => {
    const d = currentDate.value
    return d.toLocaleString('default', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  })

  const weekTitle = computed(() => {
    const ws = startOfWeek(currentDate.value)
    const we = endOfWeek(currentDate.value)
    const wsStr = ws.toLocaleString('default', { month: 'short', day: 'numeric' })
    const weStr = we.toLocaleString('default', { month: 'short', day: 'numeric', year: 'numeric' })
    return `${wsStr} - ${weStr}`
  })

  const viewTitle = computed(() => {
    switch (viewMode.value) {
      case 'day': return dayTitle.value
      case 'week': return weekTitle.value
      case 'month': return monthTitle.value
    }
  })

  function startOfWeek(d: Date): Date {
    const r = new Date(d)
    r.setDate(r.getDate() - r.getDay())
    r.setHours(0, 0, 0, 0)
    return r
  }

  function endOfWeek(d: Date): Date {
    const r = new Date(d)
    r.setDate(r.getDate() + (6 - r.getDay()))
    r.setHours(23, 59, 59, 999)
    return r
  }

  function startOfMonth(d: Date): Date {
    return new Date(d.getFullYear(), d.getMonth(), 1)
  }

  function endOfMonth(d: Date): Date {
    return new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999)
  }

  function isSameDay(a: Date, b: Date): boolean {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  }

  function isSameMonth(a: Date, b: Date): boolean {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
  }

  function formatDateStr(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  }

  function formatTimeStr(d: Date): string {
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }

  function formatHour(hour: number): string {
    if (hour === 0) return '12 AM'
    if (hour < 12) return `${hour} AM`
    if (hour === 12) return '12 PM'
    return `${hour - 12} PM`
  }

  function getMonthDays(): Date[] {
    const year = currentDate.value.getFullYear()
    const month = currentDate.value.getMonth()
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
  }

  function getWeekDays(): Date[] {
    const ws = startOfWeek(currentDate.value)
    const days: Date[] = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(ws)
      d.setDate(d.getDate() + i)
      days.push(d)
    }
    return days
  }

  function getHours(): number[] {
    return Array.from({ length: 24 }, (_, i) => i)
  }

  function navigatePrevious() {
    const d = new Date(currentDate.value)
    switch (viewMode.value) {
      case 'day': d.setDate(d.getDate() - 1); break
      case 'week': d.setDate(d.getDate() - 7); break
      case 'month': d.setMonth(d.getMonth() - 1); break
    }
    currentDate.value = d
  }

  function navigateNext() {
    const d = new Date(currentDate.value)
    switch (viewMode.value) {
      case 'day': d.setDate(d.getDate() + 1); break
      case 'week': d.setDate(d.getDate() + 7); break
      case 'month': d.setMonth(d.getMonth() + 1); break
    }
    currentDate.value = d
  }

  function navigateToday() {
    currentDate.value = new Date()
  }

  function setView(mode: ViewMode) {
    viewMode.value = mode
  }

  function navigateToDate(d: Date) {
    currentDate.value = new Date(d)
    viewMode.value = 'day'
  }

  function eventOccursOnDate(eventStart: string, eventEnd: string, date: Date): boolean {
    const es = new Date(eventStart)
    const ee = new Date(eventEnd)
    const ds = new Date(date)
    ds.setHours(0, 0, 0, 0)
    const de = new Date(date)
    de.setHours(23, 59, 59, 999)
    return es <= de && ee >= ds
  }

  function isMultiDayEvent(eventStart: string, eventEnd: string): boolean {
    const s = new Date(eventStart)
    const e = new Date(eventEnd)
    return new Date(s.getFullYear(), s.getMonth(), s.getDate()).getTime() !==
      new Date(e.getFullYear(), e.getMonth(), e.getDate()).getTime()
  }

  function getEventSpanDays(eventStart: string, eventEnd: string, monthDays: Date[]): { startOffset: number; span: number } | null {
    const es = new Date(eventStart)
    const ee = new Date(eventEnd)
    const esDay = new Date(es.getFullYear(), es.getMonth(), es.getDate())
    const eeDay = new Date(ee.getFullYear(), ee.getMonth(), ee.getDate())
    if (monthDays.length === 0) return null
    const gridStart = new Date(monthDays[0].getFullYear(), monthDays[0].getMonth(), monthDays[0].getDate())
    const gridEnd = new Date(monthDays[monthDays.length - 1].getFullYear(), monthDays[monthDays.length - 1].getMonth(), monthDays[monthDays.length - 1].getDate())
    const clippedStart = esDay < gridStart ? gridStart : esDay
    const clippedEnd = eeDay > gridEnd ? gridEnd : eeDay
    if (clippedStart > gridEnd || clippedEnd < gridStart) return null
    const startOffset = Math.round((clippedStart.getTime() - gridStart.getTime()) / (86400000))
    const span = Math.round((clippedEnd.getTime() - clippedStart.getTime()) / (86400000)) + 1
    const rowStart = Math.floor(startOffset / 7) * 7
    const maxSpan = rowStart + 7 - startOffset
    return { startOffset, span: Math.min(span, maxSpan) }
  }

  return {
    currentDate,
    viewMode,
    today,
    weekDayLabels,
    viewTitle,
    monthTitle,
    startOfWeek,
    endOfWeek,
    startOfMonth,
    endOfMonth,
    isSameDay,
    isSameMonth,
    formatDateStr,
    formatTimeStr,
    formatHour,
    getMonthDays,
    getWeekDays,
    getHours,
    navigatePrevious,
    navigateNext,
    navigateToday,
    setView,
    navigateToDate,
    eventOccursOnDate,
    isMultiDayEvent,
    getEventSpanDays,
  }
}
