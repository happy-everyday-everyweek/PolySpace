<template>
  <div class="todo-app">
    <div class="todo-sidebar">
      <div class="sidebar-header">
        <h3>任务管理</h3>
        <button class="icon-btn" @click="showSyncInfo = !showSyncInfo" title="同步状态">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
        </button>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-item" :class="{ active: currentView === 'list' }" @click="currentView = 'list'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2M9 5a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2M9 5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2"/></svg>
          <span>全部任务</span>
        </div>
        <div class="sidebar-item" :class="{ active: currentView === 'calendar' }" @click="currentView = 'calendar'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
          <span>日历视图</span>
        </div>
        <div class="sidebar-item" :class="{ active: currentView === 'quadrant' }" @click="currentView = 'quadrant'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
          <span>四象限</span>
        </div>
        <div class="sidebar-item" :class="{ active: currentView === 'habits' }" @click="currentView = 'habits'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span>习惯养成</span>
        </div>
        <div class="sidebar-item" :class="{ active: currentView === 'pomodoro' }" @click="currentView = 'pomodoro'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>番茄计时</span>
        </div>
      </div>
      <div class="sidebar-section" v-if="taskLists.length">
        <div class="sidebar-label">清单</div>
        <div
          v-for="list in taskLists" :key="list.id"
          class="sidebar-item" :class="{ active: currentListId === list.id }"
          @click="selectList(list.id)"
        >
          <span class="list-dot" :style="{ background: list.color || 'var(--ws-accent)' }"></span>
          <span>{{ list.name }}</span>
        </div>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">快捷</div>
        <div class="sidebar-item" @click="showOverdue = !showOverdue">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--ws-danger)" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/></svg>
          <span>逾期任务</span>
        </div>
      </div>
    </div>

    <div class="todo-main">
      <!-- List View -->
      <div v-if="currentView === 'list'" class="view-list">
        <div class="main-header">
          <div class="smart-input-row">
            <input
              v-model="smartInput" type="text"
              placeholder="输入任务，如：明天3点开会 #工作 紧急"
              class="smart-input"
              @keydown.enter="smartCreateTask"
            />
            <button class="primary-btn" @click="smartCreateTask" :disabled="!smartInput.trim()">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            </button>
            <button class="secondary-btn" @click="openAddDialog" title="详细添加">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
          </div>
        </div>
        <div class="filter-bar">
          <div class="filter-group">
            <button v-for="f in statusFilters" :key="f.value"
              :class="['filter-chip', { active: currentFilter === f.value }]"
              @click="currentFilter = f.value">{{ f.label }}</button>
          </div>
          <div class="sort-select">
            <select v-model="sortBy" @change="loadTasks" class="sort-dropdown">
              <option value="created_at">创建时间</option>
              <option value="due_date">截止日期</option>
              <option value="priority">优先级</option>
              <option value="title">标题</option>
              <option value="updated_at">更新时间</option>
            </select>
          </div>
        </div>
        <div class="task-list">
          <div v-for="task in filteredTasks" :key="task.id"
            :class="['task-card', task.status, { overdue: isOverdue(task), linked: task.kanban_card_id }]"
            @click="openTaskDetail(task)">
            <button class="check-btn" @click.stop="toggleTask(task)">
              <svg v-if="task.status === 'completed'" width="16" height="16" viewBox="0 0 16 16"><path d="M3 8l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
            </button>
            <div class="task-body">
              <div class="task-title-row">
                <span class="task-title">{{ task.title }}</span>
                <span v-if="task.priority !== 'none'" class="priority-tag" :class="task.priority">{{ priorityLabels[task.priority] || task.priority }}</span>
              </div>
              <div class="task-meta">
                <span v-if="task.due_date" class="meta-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>
                  {{ task.due_date }}{{ task.due_time ? ' ' + task.due_time : '' }}
                </span>
                <span v-if="task.tags?.length" class="meta-item tags">
                  <span v-for="tag in task.tags.slice(0, 3)" :key="tag" class="tag-chip">{{ tag }}</span>
                </span>
                <span v-if="task.subtasks?.length" class="meta-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                  {{ task.subtasks.filter(s => s.completed).length }}/{{ task.subtasks.length }}
                </span>
                <span v-if="task.reminders?.length" class="meta-item">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                </span>
              </div>
            </div>
            <button class="delete-btn" @click.stop="deleteTask(task.id)">
              <svg width="12" height="12" viewBox="0 0 14 14"><path d="M2 4h10M5 4V2h4v2M4 4v8h6V4" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
            </button>
          </div>
          <div v-if="!filteredTasks.length" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
            <p>暂无任务</p>
          </div>
        </div>
      </div>

      <!-- Calendar View -->
      <div v-if="currentView === 'calendar'" class="view-calendar">
        <div class="calendar-header">
          <button class="icon-btn" @click="calendarMonth--"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg></button>
          <span class="calendar-title">{{ calendarYear }}年{{ calendarMonth }}月</span>
          <button class="icon-btn" @click="calendarMonth++"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg></button>
        </div>
        <div class="calendar-grid">
          <div class="cal-weekday" v-for="d in weekdays" :key="d">{{ d }}</div>
          <div
            v-for="day in calendarDays" :key="day.date"
            :class="['cal-day', { today: day.isToday, selected: day.date === selectedDate, other: day.other }]"
            @click="selectedDate = day.date"
          >
            <span class="day-num">{{ day.day }}</span>
            <div class="day-dots">
              <span v-for="n in Math.min(day.taskCount, 3)" :key="n" class="dot"></span>
            </div>
          </div>
        </div>
        <div class="cal-tasks" v-if="selectedDateTasks.length">
          <h4>{{ selectedDate }}</h4>
          <div v-for="task in selectedDateTasks" :key="task.id" class="cal-task-item" @click="openTaskDetail(task)">
            <span class="cal-task-time">{{ task.due_time || '--:--' }}</span>
            <span class="cal-task-title">{{ task.title }}</span>
            <span class="priority-tag sm" :class="task.priority">{{ priorityLabels[task.priority] || '' }}</span>
          </div>
        </div>
      </div>

      <!-- Quadrant View -->
      <div v-if="currentView === 'quadrant'" class="view-quadrant">
        <div class="quadrant-grid">
          <div class="quadrant q1">
            <div class="q-header"><span class="q-label">紧急且重要</span><span class="q-count">{{ quadrantTasks.q1?.length || 0 }}</span></div>
            <div class="q-tasks">
              <div v-for="t in quadrantTasks.q1" :key="t.id" class="q-task" @click="openTaskDetail(t)">{{ t.title }}</div>
            </div>
          </div>
          <div class="quadrant q2">
            <div class="q-header"><span class="q-label">重要不紧急</span><span class="q-count">{{ quadrantTasks.q2?.length || 0 }}</span></div>
            <div class="q-tasks">
              <div v-for="t in quadrantTasks.q2" :key="t.id" class="q-task" @click="openTaskDetail(t)">{{ t.title }}</div>
            </div>
          </div>
          <div class="quadrant q3">
            <div class="q-header"><span class="q-label">紧急不重要</span><span class="q-count">{{ quadrantTasks.q3?.length || 0 }}</span></div>
            <div class="q-tasks">
              <div v-for="t in quadrantTasks.q3" :key="t.id" class="q-task" @click="openTaskDetail(t)">{{ t.title }}</div>
            </div>
          </div>
          <div class="quadrant q4">
            <div class="q-header"><span class="q-label">不紧急不重要</span><span class="q-count">{{ quadrantTasks.q4?.length || 0 }}</span></div>
            <div class="q-tasks">
              <div v-for="t in quadrantTasks.q4" :key="t.id" class="q-task" @click="openTaskDetail(t)">{{ t.title }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Habits View -->
      <div v-if="currentView === 'habits'" class="view-habits">
        <div class="main-header">
          <h3>习惯养成</h3>
          <button class="primary-btn" @click="showHabitDialog = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
            添加习惯
          </button>
        </div>
        <div class="habit-list">
          <div v-for="habit in habits" :key="habit.id" class="habit-card">
            <div class="habit-info">
              <span class="habit-color" :style="{ background: habit.color || 'var(--ws-accent)' }"></span>
              <div class="habit-detail">
                <span class="habit-title">{{ habit.title }}</span>
                <span class="habit-freq">{{ habit.frequency === 'daily' ? '每日' : habit.frequency === 'weekly' ? '每周' : '自定义' }}</span>
              </div>
              <span class="habit-streak">{{ habit.streak }}天连续</span>
            </div>
            <div class="habit-week">
              <button v-for="d in last7Days" :key="d.date"
                :class="['habit-day', { checked: isHabitChecked(habit, d.date) }]"
                @click="toggleHabitCheckin(habit, d.date)">
                {{ d.label }}
              </button>
            </div>
          </div>
          <div v-if="!habits.length" class="empty-state"><p>暂无习惯，点击添加</p></div>
        </div>
      </div>

      <!-- Pomodoro View -->
      <div v-if="currentView === 'pomodoro'" class="view-pomodoro">
        <div class="pomodoro-main">
          <div class="pomo-timer">
            <svg class="timer-ring" width="200" height="200" viewBox="0 0 200 200">
              <circle cx="100" cy="100" r="90" fill="none" stroke="var(--border-color)" stroke-width="6"/>
              <circle cx="100" cy="100" r="90" fill="none" stroke="var(--ws-accent)" stroke-width="6"
                :stroke-dasharray="2 * Math.PI * 90"
                :stroke-dashoffset="2 * Math.PI * 90 * (1 - pomoProgress)"
                stroke-linecap="round" transform="rotate(-90 100 100)"/>
            </svg>
            <div class="timer-display">{{ pomoTimeDisplay }}</div>
            <div class="timer-status">{{ pomoStatusText }}</div>
          </div>
          <div class="pomo-controls">
            <button v-if="!pomoRunning" class="pomo-btn start" @click="startPomodoro">开始专注</button>
            <button v-else class="pomo-btn stop" @click="stopPomodoro">停止</button>
            <button class="pomo-btn complete" @click="completePomodoro" v-if="pomoRunning">完成</button>
          </div>
          <div class="pomo-settings-row">
            <label>专注 <input type="number" v-model.number="pomoSettings.focus_duration" min="1" max="120" class="pomo-input" @change="savePomoSettings"/> 分钟</label>
            <label>休息 <input type="number" v-model.number="pomoSettings.break_duration" min="1" max="60" class="pomo-input" @change="savePomoSettings"/> 分钟</label>
            <label>长休息 <input type="number" v-model.number="pomoSettings.long_break_duration" min="1" max="60" class="pomo-input" @change="savePomoSettings"/> 分钟</label>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Task Dialog -->
    <div v-if="showAddDialog" class="dialog-overlay" @click="showAddDialog = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h4>添加新任务</h4>
          <button class="close-btn" @click="showAddDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>标题</label>
            <input v-model="newTask.title" type="text" placeholder="输入任务标题..." class="dialog-input" @keydown.enter="confirmAddTask" ref="newTaskInput" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="newTask.description" placeholder="描述..." class="dialog-input form-textarea" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>优先级</label>
              <select v-model="newTask.priority" class="dialog-input">
                <option value="none">无</option>
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
            <div class="form-group">
              <label>重要程度</label>
              <select v-model="newTask.importance" class="dialog-input">
                <option value="normal">普通</option>
                <option value="important">重要</option>
              </select>
            </div>
            <div class="form-group">
              <label>紧急程度</label>
              <select v-model="newTask.urgency" class="dialog-input">
                <option value="normal">普通</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>截止日期</label>
              <input v-model="newTask.due_date" type="date" class="dialog-input" />
            </div>
            <div class="form-group">
              <label>截止时间</label>
              <input v-model="newTask.due_time" type="time" class="dialog-input" />
            </div>
          </div>
          <div class="form-group">
            <label>清单</label>
            <select v-model="newTask.list_id" class="dialog-input">
              <option :value="null">无</option>
              <option v-for="list in taskLists" :key="list.id" :value="list.id">{{ list.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>标签 (逗号分隔)</label>
            <input v-model="newTask.tagsInput" type="text" placeholder="tag1, tag2..." class="dialog-input" />
          </div>
          <div class="form-group">
            <label>子任务 (每行一个)</label>
            <textarea v-model="newTask.subtasksInput" placeholder="子任务1&#10;子任务2" class="dialog-input form-textarea" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>提醒</label>
            <div class="reminder-row">
              <select v-model="newTask.reminderType" class="dialog-input" style="width:auto">
                <option value="none">不重复</option>
                <option value="daily">每天</option>
                <option value="weekly">每周</option>
                <option value="monthly">每月</option>
              </select>
              <input v-model="newTask.remindAt" type="datetime-local" class="dialog-input" style="flex:1" />
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showAddDialog = false">取消</button>
          <button class="dialog-btn primary" @click="confirmAddTask" :disabled="!newTask.title.trim()">添加</button>
        </div>
      </div>
    </div>

    <!-- Task Detail Dialog -->
    <div v-if="showDetailDialog" class="dialog-overlay" @click="showDetailDialog = false">
      <div class="dialog-content detail-dialog" @click.stop>
        <div class="dialog-header">
          <h4>{{ detailTask?.title }}</h4>
          <button class="close-btn" @click="showDetailDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body" v-if="detailTask">
          <div class="detail-row"><span class="detail-label">状态</span><span :class="['status-badge', detailTask.status]">{{ statusLabels[detailTask.status] }}</span></div>
          <div class="detail-row"><span class="detail-label">优先级</span><span class="priority-tag" :class="detailTask.priority">{{ priorityLabels[detailTask.priority] || '无' }}</span></div>
          <div class="detail-row" v-if="detailTask.due_date"><span class="detail-label">截止</span><span>{{ detailTask.due_date }} {{ detailTask.due_time }}</span></div>
          <div class="detail-row" v-if="detailTask.description"><span class="detail-label">描述</span><span>{{ detailTask.description }}</span></div>
          <div class="detail-row" v-if="detailTask.tags?.length"><span class="detail-label">标签</span><span><span v-for="tag in detailTask.tags" :key="tag" class="tag-chip">{{ tag }}</span></span></div>
          <div class="detail-section" v-if="detailTask.subtasks?.length">
            <h5>子任务</h5>
            <div v-for="st in detailTask.subtasks" :key="st.id" class="subtask-row">
              <button :class="['subtask-check', { done: st.completed }]" @click="toggleSubtask(st)">
                <svg v-if="st.completed" width="12" height="12" viewBox="0 0 16 16"><path d="M3 8l3 3 7-7" fill="none" stroke="currentColor" stroke-width="2"/></svg>
              </button>
              <span :class="{ done: st.completed }">{{ st.title }}</span>
            </div>
          </div>
          <div class="detail-section" v-if="detailTask.reminders?.length">
            <h5>提醒</h5>
            <div v-for="r in detailTask.reminders" :key="r.id" class="reminder-row-item">
              <span>{{ r.remind_at }}</span>
              <span v-if="r.repeat_type !== 'none'" class="repeat-badge">{{ repeatLabels[r.repeat_type] }}</span>
            </div>
          </div>
          <div class="detail-actions">
            <button v-if="detailTask.status !== 'completed'" class="dialog-btn primary" @click="completeAndRefresh(detailTask)">完成</button>
            <button v-else class="dialog-btn secondary" @click="reopenAndRefresh(detailTask)">重新打开</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Habit Dialog -->
    <div v-if="showHabitDialog" class="dialog-overlay" @click="showHabitDialog = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h4>添加习惯</h4>
          <button class="close-btn" @click="showHabitDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group"><label>名称</label><input v-model="newHabit.title" type="text" placeholder="如：跑步30分钟" class="dialog-input" /></div>
          <div class="form-group"><label>频率</label><select v-model="newHabit.frequency" class="dialog-input"><option value="daily">每日</option><option value="weekly">每周</option><option value="custom">自定义</option></select></div>
          <div class="form-group"><label>颜色</label><input v-model="newHabit.color" type="color" class="dialog-input" style="height:36px" /></div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showHabitDialog = false">取消</button>
          <button class="dialog-btn primary" @click="confirmAddHabit" :disabled="!newHabit.title.trim()">添加</button>
        </div>
      </div>
    </div>

    <!-- Overdue Panel -->
    <div v-if="showOverdue" class="dialog-overlay" @click="showOverdue = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header"><h4>逾期任务</h4><button class="close-btn" @click="showOverdue = false"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button></div>
        <div class="dialog-body">
          <div v-for="t in overdueTasks" :key="t.id" class="overdue-item" @click="openTaskDetail(t)">
            <span class="overdue-title">{{ t.title }}</span>
            <span class="overdue-date">{{ t.due_date }}</span>
          </div>
          <div v-if="!overdueTasks.length" class="empty-state"><p>没有逾期任务</p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '../../utils/api'
import type { TodoItem, HabitItem, PomodoroSettings } from '../../types/workspace'

const priorityLabels: Record<string, string> = { none: '无', low: '低', medium: '中', high: '高', urgent: '紧急' }
const statusLabels: Record<string, string> = { pending: '待办', in_progress: '进行中', completed: '已完成', cancelled: '已取消' }
const repeatLabels: Record<string, string> = { none: '不重复', daily: '每天', weekly: '每周', monthly: '每月', yearly: '每年', custom: '自定义' }
const weekdays = ['一', '二', '三', '四', '五', '六', '日']

const currentView = ref('list')
const currentFilter = ref('all')
const currentListId = ref<number | null>(null)
const sortBy = ref('created_at')
const showOverdue = ref(false)
const showSyncInfo = ref(false)

const tasks = ref<TodoItem[]>([])
const taskLists = ref<any[]>([])
const habits = ref<HabitItem[]>([])
const quadrantTasks = ref<Record<string, TodoItem[]>>({})
const overdueTasks = ref<TodoItem[]>([])

const smartInput = ref('')
const showAddDialog = ref(false)
const showDetailDialog = ref(false)
const showHabitDialog = ref(false)
const detailTask = ref<TodoItem | null>(null)

const newTask = ref({
  title: '', description: '', priority: 'none' as string,
  importance: 'normal' as string, urgency: 'normal' as string,
  due_date: '', due_time: '', list_id: null as number | null,
  tagsInput: '', subtasksInput: '', reminderType: 'none' as string, remindAt: '',
})
const newHabit = ref({ title: '', frequency: 'daily' as string, color: '#333333' })

const calendarYear = ref(new Date().getFullYear())
const calendarMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref(new Date().toISOString().slice(0, 10))

const pomoSettings = ref<PomodoroSettings>({ focus_duration: 25, break_duration: 5, long_break_duration: 15, sessions_before_long_break: 4, auto_start_break: 1, auto_start_focus: 0 })
const pomoRunning = ref(false)
const pomoSessionId = ref<number | null>(null)
const pomoStartTime = ref(0)
const pomoElapsed = ref(0)
const pomoIsBreak = ref(false)
let pomoTimer: ReturnType<typeof setInterval> | null = null

const statusFilters = [
  { label: '全部', value: 'all' },
  { label: '待办', value: 'pending' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' },
]

const filteredTasks = computed(() => {
  let list = tasks.value
  if (currentFilter.value !== 'all') list = list.filter(t => t.status === currentFilter.value)
  if (currentListId.value) list = list.filter(t => t.list_id === currentListId.value)
  return list
})

const last7Days = computed(() => {
  const days = []
  const dayLabels = ['日', '一', '二', '三', '四', '五', '六']
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    days.push({ date: d.toISOString().slice(0, 10), label: dayLabels[d.getDay()] })
  }
  return days
})

const calendarDays = computed(() => {
  const y = calendarYear.value
  const m = calendarMonth.value
  const firstDay = new Date(y, m - 1, 1)
  const lastDay = new Date(y, m, 0)
  const startWeekday = (firstDay.getDay() + 6) % 7
  const days: any[] = []
  const today = new Date().toISOString().slice(0, 10)
  const taskDateMap: Record<string, number> = {}
  for (const t of tasks.value) {
    if (t.due_date) taskDateMap[t.due_date] = (taskDateMap[t.due_date] || 0) + 1
  }
  for (let i = startWeekday - 1; i >= 0; i--) {
    const d = new Date(y, m - 1, -i)
    days.push({ date: d.toISOString().slice(0, 10), day: d.getDate(), other: true, isToday: false, taskCount: taskDateMap[d.toISOString().slice(0, 10)] || 0 })
  }
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const dateStr = `${y}-${String(m).padStart(2, '0')}-${String(i).padStart(2, '0')}`
    days.push({ date: dateStr, day: i, other: false, isToday: dateStr === today, taskCount: taskDateMap[dateStr] || 0 })
  }
  const remaining = 42 - days.length
  for (let i = 1; i <= remaining; i++) {
    const d = new Date(y, m, i)
    days.push({ date: d.toISOString().slice(0, 10), day: d.getDate(), other: true, isToday: false, taskCount: 0 })
  }
  return days
})

const selectedDateTasks = computed(() => {
  return tasks.value.filter(t => t.due_date === selectedDate.value && t.status !== 'completed')
})

const pomoProgress = computed(() => {
  if (!pomoRunning.value) return 0
  const total = (pomoIsBreak.value ? pomoSettings.value.break_duration : pomoSettings.value.focus_duration) * 60
  return Math.min(pomoElapsed.value / total, 1)
})

const pomoTimeDisplay = computed(() => {
  const total = (pomoIsBreak.value ? pomoSettings.value.break_duration : pomoSettings.value.focus_duration) * 60
  const remaining = Math.max(total - pomoElapsed.value, 0)
  const min = Math.floor(remaining / 60)
  const sec = remaining % 60
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
})

const pomoStatusText = computed(() => {
  if (!pomoRunning.value) return '准备就绪'
  return pomoIsBreak.value ? '休息中' : '专注中'
})

function isOverdue(task: TodoItem) {
  if (task.status === 'completed' || !task.due_date) return false
  return task.due_date < new Date().toISOString().slice(0, 10)
}

async function loadTasks() {
  try {
    const params: any = { sort_by: sortBy.value, sort_order: 'DESC' }
    if (currentListId.value) params.list_id = currentListId.value
    const res = await api.get('/todo/items', { params })
    tasks.value = res.data.tasks || []
  } catch (e) { console.error('Failed to load tasks:', e) }
}

async function loadLists() {
  try {
    const res = await api.get('/todo/lists')
    taskLists.value = res.data.lists || []
  } catch (e) { console.error('Failed to load lists:', e) }
}

async function loadHabits() {
  try {
    const res = await api.get('/todo/habits')
    habits.value = res.data.habits || []
  } catch (e) { console.error('Failed to load habits:', e) }
}

async function loadQuadrant() {
  try {
    const res = await api.get('/todo/quadrant')
    quadrantTasks.value = res.data || {}
  } catch (e) { console.error('Failed to load quadrant:', e) }
}

async function loadOverdue() {
  try {
    const res = await api.get('/todo/overdue')
    overdueTasks.value = res.data.tasks || []
  } catch (e) { console.error('Failed to load overdue:', e) }
}

async function loadPomoSettings() {
  try {
    const res = await api.get('/todo/pomodoro/settings')
    pomoSettings.value = res.data
  } catch (e) { console.error('Failed to load pomo settings:', e) }
}

async function smartCreateTask() {
  const text = smartInput.value.trim()
  if (!text) return
  try {
    await api.post('/todo/items/smart', { text, source: 'smart' })
    smartInput.value = ''
    await loadTasks()
  } catch (e) { console.error('Smart create failed:', e) }
}

function openAddDialog() {
  showAddDialog.value = true
  newTask.value = { title: '', description: '', priority: 'none', importance: 'normal', urgency: 'normal', due_date: '', due_time: '', list_id: null, tagsInput: '', subtasksInput: '', reminderType: 'none', remindAt: '' }
}

async function confirmAddTask() {
  const title = newTask.value.title.trim()
  if (!title) return
  try {
    const tags = newTask.value.tagsInput ? newTask.value.tagsInput.split(',').map(t => t.trim()).filter(Boolean) : []
    const subtasks = newTask.value.subtasksInput ? newTask.value.subtasksInput.split('\n').map(s => s.trim()).filter(Boolean) : []
    const reminders: any[] = []
    if (newTask.value.remindAt) {
      reminders.push({ remind_at: newTask.value.remindAt, repeat_type: newTask.value.reminderType })
    }
    await api.post('/todo/items', {
      title, description: newTask.value.description,
      priority: newTask.value.priority, importance: newTask.value.importance,
      urgency: newTask.value.urgency, due_date: newTask.value.due_date || null,
      due_time: newTask.value.due_time || null, list_id: newTask.value.list_id,
      tags, subtasks, reminders,
    })
    await loadTasks()
    showAddDialog.value = false
  } catch (e) { console.error('Failed to create task:', e) }
}

async function toggleTask(task: TodoItem) {
  try {
    if (task.status === 'completed') {
      await api.put(`/todo/items/${task.id}/reopen`)
    } else {
      await api.put(`/todo/items/${task.id}/complete`)
    }
    await loadTasks()
  } catch (e) { console.error('Failed to toggle task:', e) }
}

async function deleteTask(id: number) {
  try {
    await api.delete(`/todo/items/${id}`)
    await loadTasks()
  } catch (e) { console.error('Failed to delete task:', e) }
}

async function openTaskDetail(task: TodoItem) {
  try {
    const res = await api.get(`/todo/items/${task.id}`)
    detailTask.value = res.data
    showDetailDialog.value = true
  } catch (e) { console.error('Failed to load task detail:', e) }
}

async function toggleSubtask(subtask: any) {
  try {
    await api.put(`/todo/subtasks/${subtask.id}`, { completed: subtask.completed ? 0 : 1 })
    if (detailTask.value) await openTaskDetail(detailTask.value)
  } catch (e) { console.error('Failed to toggle subtask:', e) }
}

async function completeAndRefresh(task: TodoItem) {
  try {
    await api.put(`/todo/items/${task.id}/complete`)
    showDetailDialog.value = false
    await loadTasks()
  } catch (e) { console.error('Failed:', e) }
}

async function reopenAndRefresh(task: TodoItem) {
  try {
    await api.put(`/todo/items/${task.id}/reopen`)
    showDetailDialog.value = false
    await loadTasks()
  } catch (e) { console.error('Failed:', e) }
}

function selectList(listId: number) {
  currentListId.value = currentListId.value === listId ? null : listId
  currentView.value = 'list'
  loadTasks()
}

function isHabitChecked(habit: HabitItem, date: string) {
  return habit.checkins?.some((c: any) => c.checkin_date === date)
}

async function toggleHabitCheckin(habit: HabitItem, date: string) {
  try {
    if (isHabitChecked(habit, date)) {
      await api.delete(`/todo/habits/${habit.id}/checkin/${date}`)
    } else {
      await api.post(`/todo/habits/${habit.id}/checkin`, { date, note: '' })
    }
    await loadHabits()
  } catch (e) { console.error('Failed to toggle habit checkin:', e) }
}

async function confirmAddHabit() {
  const title = newHabit.value.title.trim()
  if (!title) return
  try {
    await api.post('/todo/habits', { title, frequency: newHabit.value.frequency, color: newHabit.value.color })
    newHabit.value = { title: '', frequency: 'daily', color: '#333333' }
    showHabitDialog.value = false
    await loadHabits()
  } catch (e) { console.error('Failed to create habit:', e) }
}

async function startPomodoro() {
  try {
    const res = await api.post('/todo/pomodoro/start', { focus_duration: pomoSettings.value.focus_duration, break_duration: pomoSettings.value.break_duration })
    pomoSessionId.value = res.data.id
    pomoRunning.value = true
    pomoIsBreak.value = false
    pomoStartTime.value = Date.now()
    pomoElapsed.value = 0
    if (pomoTimer) clearInterval(pomoTimer)
    pomoTimer = setInterval(() => {
      pomoElapsed.value = Math.floor((Date.now() - pomoStartTime.value) / 1000)
    }, 1000)
  } catch (e) { console.error('Failed to start pomodoro:', e) }
}

function stopPomodoro() {
  if (pomoTimer) { clearInterval(pomoTimer); pomoTimer = null }
  if (pomoSessionId.value) {
    api.put(`/todo/pomodoro/${pomoSessionId.value}/cancel`).catch(() => {})
  }
  pomoRunning.value = false
  pomoSessionId.value = null
}

async function completePomodoro() {
  if (pomoTimer) { clearInterval(pomoTimer); pomoTimer = null }
  if (pomoSessionId.value) {
    try { await api.put(`/todo/pomodoro/${pomoSessionId.value}/complete`) } catch (e) { console.error(e) }
  }
  pomoRunning.value = false
  pomoSessionId.value = null
}

async function savePomoSettings() {
  try {
    await api.put('/todo/pomodoro/settings', pomoSettings.value)
  } catch (e) { console.error('Failed to save pomo settings:', e) }
}

watch(currentView, (v) => {
  if (v === 'calendar') loadTasks()
  if (v === 'quadrant') loadQuadrant()
  if (v === 'habits') loadHabits()
  if (v === 'pomodoro') loadPomoSettings()
})

watch([calendarYear, calendarMonth], () => loadTasks())

onMounted(() => {
  loadTasks()
  loadLists()
  loadOverdue()
  loadPomoSettings()
})
</script>

<style scoped>
.todo-app { display: flex; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
.todo-sidebar { width: 200px; border-right: 1px solid var(--border-color); display: flex; flex-direction: column; padding: 12px 8px; flex-shrink: 0; overflow-y: auto; }
.sidebar-header { display: flex; align-items: center; justify-content: space-between; padding: 4px 8px 12px; }
.sidebar-header h3 { font-size: 15px; font-weight: 600; margin: 0; }
.sidebar-section { margin-bottom: 12px; }
.sidebar-label { font-size: 11px; color: var(--text-tertiary); padding: 4px 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.sidebar-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--text-secondary); }
.sidebar-item:hover { background: var(--bg-secondary); }
.sidebar-item.active { background: var(--ws-accent-light); color: var(--ws-accent); }
.list-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.todo-main { flex: 1; overflow-y: auto; }

.icon-btn { background: none; border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; padding: 4px 8px; cursor: pointer; display: flex; align-items: center; }
.icon-btn:hover { background: var(--bg-secondary); border-color: var(--ws-accent); color: var(--ws-accent); }
.primary-btn { padding: 6px 12px; border-radius: 6px; background: var(--ws-accent); color: #fff; font-size: 13px; border: none; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.primary-btn:hover { background: var(--ws-accent-hover); }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.secondary-btn { padding: 6px 12px; border-radius: 6px; background: none; border: 1px solid var(--border-color); color: var(--text-secondary); font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 4px; }
.secondary-btn:hover { background: var(--bg-secondary); }

.view-list, .view-calendar, .view-quadrant, .view-habits, .view-pomodoro { padding: 16px; height: 100%; overflow-y: auto; }
.main-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.main-header h3 { font-size: 16px; font-weight: 600; margin: 0; }
.smart-input-row { display: flex; gap: 6px; width: 100%; }
.smart-input { flex: 1; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 8px; background: var(--bg-secondary); color: var(--text-primary); font-size: 13px; outline: none; }
.smart-input:focus { border-color: var(--ws-accent); }

.filter-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.filter-group { display: flex; gap: 4px; }
.filter-chip { padding: 4px 12px; border-radius: 12px; font-size: 12px; color: var(--text-tertiary); background: none; border: 1px solid transparent; cursor: pointer; }
.filter-chip:hover { background: var(--bg-secondary); }
.filter-chip.active { background: var(--ws-accent); color: #fff; }
.sort-dropdown { padding: 4px 8px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 12px; outline: none; }

.task-list { display: flex; flex-direction: column; gap: 4px; }
.task-card { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; border-radius: 8px; background: var(--bg-secondary); cursor: pointer; transition: background 0.15s; }
.task-card:hover { background: var(--bg-tertiary, var(--border-color)); }
.task-card.completed .task-title { text-decoration: line-through; color: var(--text-tertiary); }
.task-card.overdue { border-left: 3px solid var(--ws-danger); }
.task-card.linked { border-left: 3px solid var(--ws-success, #34A853); }
.check-btn { color: var(--ws-accent); flex-shrink: 0; background: none; border: none; cursor: pointer; padding: 0; margin-top: 2px; }
.check-btn:hover { opacity: 0.8; }
.task-body { flex: 1; min-width: 0; }
.task-title-row { display: flex; align-items: center; gap: 6px; }
.task-title { font-size: 14px; color: var(--text-primary); }
.priority-tag { padding: 1px 6px; border-radius: 8px; font-size: 10px; font-weight: 500; white-space: nowrap; }
.priority-tag.urgent { background: var(--primary-color); color: #fff; }
.priority-tag.high { background: var(--text-secondary); color: #fff; }
.priority-tag.medium { background: var(--bg-tertiary); color: var(--text-secondary); }
.priority-tag.low { background: var(--bg-tertiary); color: var(--text-tertiary); }
.priority-tag.none { display: none; }
.priority-tag.sm { font-size: 9px; padding: 0 4px; }
.task-meta { display: flex; gap: 8px; align-items: center; margin-top: 4px; flex-wrap: wrap; }
.meta-item { display: flex; align-items: center; gap: 3px; font-size: 11px; color: var(--text-tertiary); }
.tag-chip { padding: 0 6px; border-radius: 8px; font-size: 10px; background: var(--ws-accent-light); color: var(--ws-accent); }
.delete-btn { color: var(--text-tertiary); background: none; border: none; cursor: pointer; opacity: 0; transition: opacity 0.15s; flex-shrink: 0; margin-top: 2px; }
.task-card:hover .delete-btn { opacity: 1; }
.delete-btn:hover { color: var(--ws-danger); }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 200px; color: var(--text-tertiary); font-size: 14px; gap: 8px; }

.status-badge { padding: 2px 8px; border-radius: 8px; font-size: 11px; }
.status-badge.pending { background: var(--ws-accent-light); color: var(--ws-accent); }
.status-badge.in_progress { background: var(--primary-light); color: var(--text-primary); }
.status-badge.completed { background: var(--bg-tertiary); color: var(--text-secondary); }
.status-badge.cancelled { background: var(--bg-secondary); color: var(--text-tertiary); }

/* Calendar */
.calendar-header { display: flex; align-items: center; justify-content: center; gap: 16px; margin-bottom: 16px; }
.calendar-title { font-size: 16px; font-weight: 600; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; margin-bottom: 16px; }
.cal-weekday { text-align: center; font-size: 11px; color: var(--text-tertiary); padding: 4px; }
.cal-day { text-align: center; padding: 6px 4px; border-radius: 6px; cursor: pointer; }
.cal-day:hover { background: var(--bg-secondary); }
.cal-day.today { background: var(--ws-accent-light); }
.cal-day.selected { background: var(--ws-accent); color: var(--bg-primary); }
.cal-day.other { opacity: 0.3; }
.day-num { font-size: 13px; display: block; }
.day-dots { display: flex; justify-content: center; gap: 2px; margin-top: 2px; }
.dot { width: 4px; height: 4px; border-radius: 50%; background: var(--ws-accent); }
.cal-day.selected .dot { background: #fff; }
.cal-tasks h4 { font-size: 14px; margin: 0 0 8px; }
.cal-task-item { display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; background: var(--bg-secondary); margin-bottom: 4px; cursor: pointer; }
.cal-task-item:hover { background: var(--bg-tertiary, var(--border-color)); }
.cal-task-time { font-size: 12px; color: var(--text-tertiary); min-width: 40px; }
.cal-task-title { font-size: 13px; flex: 1; }

/* Quadrant */
.quadrant-grid { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 8px; height: calc(100% - 40px); }
.quadrant { border-radius: 8px; padding: 12px; display: flex; flex-direction: column; overflow-y: auto; }
.quadrant.q1 { background: var(--bg-secondary); border: 1px solid var(--border-color); }
.quadrant.q2 { background: var(--bg-secondary); border: 1px solid var(--border-color); }
.quadrant.q3 { background: var(--bg-secondary); border: 1px solid var(--border-color); }
.quadrant.q4 { background: var(--bg-secondary); border: 1px solid var(--border-color); }
.q-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.q-label { font-size: 12px; font-weight: 600; }
.q-count { font-size: var(--font-size-xs); color: var(--text-tertiary); background: var(--primary-light); padding: 1px 6px; border-radius: var(--radius-full); }
.q-tasks { flex: 1; overflow-y: auto; }
.q-task { padding: 4px 8px; font-size: 12px; border-radius: 4px; margin-bottom: 2px; cursor: pointer; background: rgba(255,255,255,0.6); }
.q-task:hover { background: rgba(255,255,255,0.9); }

/* Habits */
.habit-list { display: flex; flex-direction: column; gap: 8px; }
.habit-card { padding: 12px; border-radius: 8px; background: var(--bg-secondary); }
.habit-info { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.habit-color { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.habit-detail { flex: 1; }
.habit-title { font-size: 14px; display: block; }
.habit-freq { font-size: 11px; color: var(--text-tertiary); }
.habit-streak { font-size: 12px; color: var(--ws-accent); font-weight: 600; }
.habit-week { display: flex; gap: 4px; }
.habit-day { width: 32px; height: 32px; border-radius: 50%; border: 1px solid var(--border-color); background: none; color: var(--text-secondary); font-size: 11px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.habit-day.checked { background: var(--ws-accent); color: #fff; border-color: var(--ws-accent); }

/* Pomodoro */
.pomodoro-main { display: flex; flex-direction: column; align-items: center; gap: 20px; padding-top: 24px; }
.pomo-timer { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.timer-ring { transform: rotate(0deg); }
.timer-display { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 36px; font-weight: 700; font-variant-numeric: tabular-nums; }
.timer-status { font-size: 13px; color: var(--text-tertiary); margin-top: 4px; }
.pomo-controls { display: flex; gap: 8px; }
.pomo-btn { padding: 8px 20px; border-radius: 8px; font-size: 14px; cursor: pointer; border: none; }
.pomo-btn.start { background: var(--ws-accent); color: #fff; }
.pomo-btn.stop { background: var(--ws-danger); color: #fff; }
.pomo-btn.complete { background: var(--ws-success, #34A853); color: #fff; }
.pomo-settings-row { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); align-items: center; }
.pomo-input { width: 50px; padding: 4px 6px; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); color: var(--text-primary); text-align: center; font-size: 13px; outline: none; }

/* Dialogs */
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-content { background: var(--card-bg); border-radius: var(--radius-lg); width: 480px; max-width: 90vw; max-height: 85vh; display: flex; flex-direction: column; box-shadow: var(--shadow-lg); }
.detail-dialog { width: 520px; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.dialog-header h4 { margin: 0; font-size: 16px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 380px; }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: #fff; }
.dialog-body { padding: 20px; overflow-y: auto; flex: 1; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 12px; padding: 16px 20px; border-top: 1px solid var(--border-color); }
.dialog-input { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-secondary); color: var(--text-primary); font-size: 13px; outline: none; }
.dialog-input:focus { border-color: var(--ws-accent); }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 12px; font-weight: 500; margin-bottom: 4px; color: var(--text-secondary); }
.form-row { display: flex; gap: 8px; }
.form-row .form-group { flex: 1; }
.form-textarea { resize: vertical; min-height: 50px; font-family: inherit; }
.dialog-btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; cursor: pointer; }
.dialog-btn.secondary { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); }
.dialog-btn.secondary:hover { background: var(--bg-secondary); }
.dialog-btn.primary { background: var(--ws-accent); border: none; color: #fff; }
.dialog-btn.primary:hover:not(:disabled) { background: var(--ws-accent-hover); }
.dialog-btn.primary:disabled { opacity: 0.5; cursor: not-allowed; }

.detail-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; font-size: 13px; }
.detail-label { color: var(--text-tertiary); min-width: 50px; }
.detail-section { margin-top: 12px; }
.detail-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; }
.subtask-row { display: flex; align-items: center; gap: 6px; padding: 4px 0; font-size: 13px; }
.subtask-check { width: 16px; height: 16px; border-radius: 50%; border: 1px solid var(--border-color); background: none; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; flex-shrink: 0; }
.subtask-check.done { background: var(--ws-accent); border-color: var(--ws-accent); color: #fff; }
.subtask-row span.done { text-decoration: line-through; color: var(--text-tertiary); }
.reminder-row { display: flex; gap: 8px; align-items: center; }
.reminder-row-item { display: flex; align-items: center; gap: 6px; padding: 4px 0; font-size: 12px; }
.repeat-badge { padding: 0 6px; border-radius: 8px; font-size: 10px; background: var(--ws-accent-light); color: var(--ws-accent); }
.detail-actions { margin-top: 16px; display: flex; gap: 8px; }
.overdue-item { display: flex; align-items: center; justify-content: space-between; padding: 8px; border-radius: 6px; background: var(--bg-secondary); margin-bottom: 4px; cursor: pointer; }
.overdue-title { font-size: 13px; }
.overdue-date { font-size: 11px; color: var(--ws-danger); }
</style>
