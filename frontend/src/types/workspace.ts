export interface WorkspaceDocument {
  id: string
  name: string
  type: 'document' | 'presentation' | 'spreadsheet' | 'video' | 'pdf'
  path: string
  content?: string
  lastModified?: number
}

export interface CalendarEventAttendee {
  email: string
  name?: string
  status?: 'accepted' | 'declined' | 'tentative' | 'needs-action'
}

export interface CalendarEventReminder {
  minutes: number
  method: 'email' | 'popup'
}

export interface CalendarEvent {
  id: string
  title: string
  start: string
  end: string
  description?: string
  location?: string
  category?: string
  color?: string
  allDay?: boolean
  attendees?: CalendarEventAttendee[]
  reminders?: CalendarEventReminder[]
  timezone?: string
  source?: string
  isRecurring?: boolean
  hasConflict?: boolean
}

export interface CalendarCategory {
  id: string
  name: string
  color: string
  visible: boolean
}

export interface TaskList {
  id: number
  name: string
  parent_id: number | null
  color: string
  icon: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface TaskSubtask {
  id: number
  task_id: number
  title: string
  completed: number
  sort_order: number
  created_at: string
}

export interface TaskReminder {
  id: number
  task_id: number
  remind_at: string
  repeat_type: 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom'
  repeat_interval: number
  repeat_days: string
  repeat_end_date: string | null
  is_triggered: number
  created_at: string
}

export interface TaskAttachment {
  id: number
  task_id: number
  file_name: string
  file_path: string
  file_type: string
  file_size: number
  created_at: string
}

export interface TodoItem {
  id: number
  title: string
  description: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  priority: 'none' | 'low' | 'medium' | 'high' | 'urgent'
  importance: 'normal' | 'important' | 'high'
  urgency: 'normal' | 'urgent' | 'high'
  due_date: string | null
  due_time: string | null
  start_date: string | null
  start_time: string | null
  recurrence: Record<string, any> | null
  list_id: number | null
  tags: string[]
  notes: string
  sort_order: number
  kanban_card_id: number | null
  kanban_board_id: number | null
  calendar_event_id: string | null
  source: string
  subtasks: TaskSubtask[]
  reminders: TaskReminder[]
  attachments: TaskAttachment[]
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface HabitItem {
  id: number
  title: string
  description: string
  frequency: 'daily' | 'weekly' | 'custom'
  target_days: string
  color: string
  icon: string
  reminder_time: string
  sort_order: number
  checkins: HabitCheckin[]
  streak: number
  created_at: string
  updated_at: string
}

export interface HabitCheckin {
  id: number
  habit_id: number
  checkin_date: string
  note: string
  created_at: string
}

export interface PomodoroSession {
  id: number
  task_id: number | null
  habit_id: number | null
  focus_duration: number
  break_duration: number
  long_break_duration: number
  sessions_before_long_break: number
  status: 'pending' | 'focusing' | 'break' | 'completed' | 'cancelled'
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface PomodoroSettings {
  focus_duration: number
  break_duration: number
  long_break_duration: number
  sessions_before_long_break: number
  auto_start_break: number
  auto_start_focus: number
}

export interface KnowledgeEntry {
  id: string
  title: string
  content: string
  tags: string[]
  source?: string
}

export interface WeatherCurrent {
  time: string
  temperature: number
  feels_like: number
  humidity: number
  precipitation: number
  weather_code: number
  weather_label: string
  weather_label_en: string
  weather_icon: string
  wind_speed: number
  wind_direction: number
  wind_direction_label: string
  pressure: number
  cloud_cover: number
  is_day: number
}

export interface WeatherDaily {
  date: string
  weather_code: number
  weather_label: string
  weather_label_en: string
  weather_icon: string
  temp_max: number
  temp_min: number
  feels_like_max: number
  feels_like_min: number
  sunrise: string
  sunset: string
  uv_index: number
  precipitation_sum: number
  precipitation_probability: number
  wind_speed_max: number
}

export interface WeatherHourly {
  time: string
  temperature: number
  precipitation_probability: number
  weather_code: number
  weather_label: string
  weather_icon: string
  wind_speed: number
  uv_index: number
}

export interface WeatherForecast {
  latitude: number
  longitude: number
  timezone: string
  current: WeatherCurrent
  daily: WeatherDaily[]
  hourly: WeatherHourly[]
}

export interface WeatherCity {
  id: number
  name: string
  latitude: number
  longitude: number
  country: string
  country_code: string
  admin1: string
  timezone: string
}

export interface AirQuality {
  pm2_5: number
  pm10: number
  us_aqi: number
}

export interface MindMapNode {
  id: string
  text: string
  children: MindMapNode[]
  collapsed?: boolean
}

export interface NoteItem {
  id: string
  title: string
  content: string
  tags: string[]
  links: string[]
  createdAt: number
  updatedAt: number
}

export interface ContactItem {
  id: string
  name: string
  email?: string
  phone?: string
  company?: string
  role?: string
  avatar?: string
  tags: string[]
  notes?: string
  birthday?: string
  lastContact?: number
}

export interface FocusSession {
  id: string
  task: string
  duration: number
  completedAt: number
  type: 'pomodoro' | 'deep' | 'custom'
}

export interface ImageProject {
  id: string
  name: string
  url?: string
  width: number
  height: number
  filters: Record<string, number>
}

export interface ReaderArticle {
  id: string
  title: string
  url: string
  summary?: string
  content?: string
  source: string
  category: string
  readAt?: number
  savedAt: number
  readProgress: number
}

export interface CodeProject {
  id: string
  name: string
  language: string
  content: string
  lastModified: number
}

export interface FinanceTransaction {
  id: string
  type: 'income' | 'expense'
  amount: number
  category: string
  description: string
  date: string
  tags: string[]
}

export interface MusicTrack {
  id: string
  title: string
  artist: string
  genre: string
  duration: number
  url?: string
}
