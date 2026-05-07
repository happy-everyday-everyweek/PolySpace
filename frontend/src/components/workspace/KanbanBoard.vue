<template>
  <div class="kanban-board">
    <div class="kanban-header">
      <div class="header-left">
        <div class="board-selector" v-if="boards.length > 1">
          <select v-model="currentBoardId" @change="onBoardSwitch" class="board-select">
            <option v-for="b in boards" :key="b.id" :value="b.id">{{ b.name }}</option>
          </select>
        </div>
        <h3 v-else>{{ board?.name || 'Kanban Board' }}</h3>
      </div>
      <div class="header-center">
        <div class="search-box">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input v-model="searchQuery" type="text" placeholder="Search cards..." class="search-input" @input="onSearch" />
          <button v-if="searchQuery" class="search-clear" @click="clearSearch">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
      </div>
      <div class="header-right">
        <button class="ai-header-btn" @click="aiSuggestProgress" title="AI Progress">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          <span>AI Progress</span>
        </button>
        <button class="ai-header-btn" @click="aiPrioritizeCards" title="AI Prioritize">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>
          <span>AI Sort</span>
        </button>
        <button class="ai-header-btn" @click="aiEstimateCompletion" title="AI Estimate">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
          <span>AI Estimate</span>
        </button>
        <div class="header-divider"></div>
        <button class="icon-btn" @click="showArchived = !showArchived" :class="{ active: showArchived }" title="Archived">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/><path d="M10 12h4"/></svg>
        </button>
        <button class="icon-btn" @click="showAddColumnDialog = true" title="Add column">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8M8 12h8"/></svg>
        </button>
      </div>
    </div>

    <div v-if="board" class="kanban-progress-bar">
      <div class="progress-track">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <span class="progress-label">{{ doneCount }}/{{ totalCount }} completed</span>
    </div>

    <div class="kanban-content">
      <div class="kanban-columns" v-if="board && !showArchived">
        <div v-for="column in board.columns" :key="column.id" class="kanban-column"
          @dragover.prevent="onDragOver($event, column.id)"
          @dragleave="onDragLeave"
          @drop="onDrop($event, column.id)">
          <div class="column-header" :style="{ borderTopColor: column.color || 'var(--primary)' }">
            <div class="column-header-left">
              <span class="column-color-dot" :style="{ backgroundColor: column.color || 'var(--primary)' }"></span>
              <span class="column-name">{{ column.name }}</span>
              <span class="column-count" :class="{ 'wip-warning': column.wip_limit > 0 && (column.cards?.length || 0) >= column.wip_limit }">
                {{ column.cards?.length || 0 }}
                <template v-if="column.wip_limit > 0">/{{ column.wip_limit }}</template>
              </span>
            </div>
            <div class="column-header-actions">
              <button class="column-action-btn" @click="addCardToColumn(column.id)" title="Add card">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              </button>
              <button class="column-action-btn" @click="openColumnMenu(column)" title="Column options">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/></svg>
              </button>
            </div>
          </div>
          <div class="column-cards" :class="{ 'drag-over': dragOverColumnId === column.id }">
            <div
              v-for="(card, index) in column.cards"
              :key="card.id"
              class="kanban-card"
              :class="{ 'dragging': dragData?.card?.id === card.id }"
              draggable="true"
              @dragstart="onDragStart($event, card, column.id, index)"
              @dragend="onDragEnd"
            >
              <div class="card-top-row">
                <span :class="['card-priority', `priority-${card.priority}`]">{{ card.priority }}</span>
                <div class="card-actions">
                  <button class="card-action-btn bridge" @click.stop="cardToTodo(card)" title="Create as Todo">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                  </button>
                  <button class="card-action-btn" @click.stop="archiveCard(card.id)" title="Archive">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 8v13H3V8"/><path d="M1 3h22v5H1z"/></svg>
                  </button>
                  <button class="card-action-btn delete" @click.stop="deleteCard(card.id)" title="Delete">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                  </button>
                </div>
              </div>
              <div class="card-title" @click="openCardDetail(card, column)">{{ card.title }}</div>
              <div v-if="card.description" class="card-desc">{{ card.description }}</div>
              <div class="card-meta">
                <span v-if="card.assignee" class="card-assignee">{{ card.assignee }}</span>
                <span v-if="card.due_date" class="card-due" :class="{ overdue: isOverdue(card.due_date) }">{{ formatDate(card.due_date) }}</span>
                <span v-if="card._linked_todo" class="card-todo-badge" @click="goToTodo" title="Linked to Todo">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                  Todo
                </span>
              </div>
              <div v-if="card.tags" class="card-tags">
                <span v-for="tag in parseTags(card.tags)" :key="tag" class="card-tag">{{ tag }}</span>
              </div>
            </div>
            <button class="add-card-btn" @click="addCardToColumn(column.id)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
              Add card
            </button>
          </div>
        </div>
      </div>

      <div v-else class="archived-view">
        <div class="archived-header">
          <h4>Archived Cards</h4>
          <button class="icon-btn" @click="showArchived = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div v-if="archivedCards.length" class="archived-list">
          <div v-for="card in archivedCards" :key="card.id" class="archived-card">
            <div class="archived-card-info">
              <span class="archived-card-title">{{ card.title }}</span>
              <span v-if="card.column_name" class="archived-card-col">{{ card.column_name }}</span>
            </div>
            <div class="archived-card-actions">
              <button class="restore-btn" @click="unarchiveCard(card.id)">Restore</button>
              <button class="card-action-btn delete" @click="deleteCard(card.id)">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
              </button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>No archived cards</p>
        </div>
      </div>

      <div v-if="showAIPanel" class="ai-panel">
        <div class="ai-panel-header">
          <h4>AI Board Assistant</h4>
          <button class="close-btn" @click="showAIPanel = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="ai-panel-content">
          <div v-if="aiLoading" class="ai-loading">
            <div class="spinner"></div>
            <span>AI is analyzing...</span>
          </div>
          <div v-else-if="aiResult" class="ai-result">
            <div v-if="aiResult.progress_analysis" class="ai-section">
              <h5>Progress Analysis</h5>
              <p class="analysis-text">{{ aiResult.progress_analysis }}</p>
            </div>
            <div v-if="aiResult.bottlenecks" class="ai-section">
              <h5>Bottlenecks</h5>
              <p class="analysis-text">{{ aiResult.bottlenecks }}</p>
            </div>
            <div v-if="aiResult.suggestions?.length" class="ai-section">
              <h5>Suggestions</h5>
              <div v-for="(s, i) in aiResult.suggestions" :key="i" class="suggestion-item">
                <span :class="['suggestion-type', s.type]">{{ s.type }}</span>
                <span class="suggestion-desc">{{ s.description }}</span>
                <span class="suggestion-priority">{{ s.priority }}</span>
              </div>
            </div>
            <div v-if="aiResult.ordered_cards?.length" class="ai-section">
              <h5>Priority Order</h5>
              <div v-for="(c, i) in aiResult.ordered_cards" :key="i" class="priority-item">
                <span class="priority-rank">{{ i + 1 }}</span>
                <span class="priority-title">{{ c.card_id }}</span>
                <span class="priority-reason">{{ c.reason }}</span>
              </div>
              <button class="apply-btn" @click="applyPriorityOrder">Apply Order</button>
            </div>
            <div v-if="aiResult.estimated_date" class="ai-section">
              <h5>Completion Estimate</h5>
              <p class="estimate-date">{{ aiResult.estimated_date }}</p>
              <span v-if="aiResult.confidence" class="estimate-confidence">Confidence: {{ Math.round(aiResult.confidence * 100) }}%</span>
              <div v-if="aiResult.factors" class="estimate-detail">{{ aiResult.factors }}</div>
              <div v-if="aiResult.risks" class="estimate-detail">{{ aiResult.risks }}</div>
            </div>
            <div v-if="aiResult.result && !aiResult.progress_analysis && !aiResult.ordered_cards && !aiResult.estimated_date" class="ai-section">
              <p class="analysis-text">{{ aiResult.result }}</p>
            </div>
          </div>
          <div v-else class="ai-empty">
            <p>Use AI to analyze progress, prioritize cards, or estimate completion</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddCardDialog" class="dialog-overlay" @click="showAddCardDialog = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h4>Add Card</h4>
          <button class="close-btn" @click="showAddCardDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>Title</label>
            <input v-model="newCard.title" type="text" placeholder="Card title..." class="form-input" ref="cardTitleInput" @keydown.enter="confirmAddCard" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newCard.description" placeholder="Description..." class="form-input form-textarea" rows="2"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Priority</label>
              <select v-model="newCard.priority" class="form-input">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div class="form-group">
              <label>Assignee</label>
              <input v-model="newCard.assignee" type="text" placeholder="Assignee..." class="form-input" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Due Date</label>
              <input v-model="newCard.due_date" type="date" class="form-input" />
            </div>
            <div class="form-group">
              <label>Tags</label>
              <input v-model="newCard.tags" type="text" placeholder="tag1, tag2..." class="form-input" />
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showAddCardDialog = false">Cancel</button>
          <button class="dialog-btn primary" @click="confirmAddCard" :disabled="!newCard.title.trim()">Add</button>
        </div>
      </div>
    </div>

    <div v-if="showCardDetailDialog" class="dialog-overlay" @click="showCardDetailDialog = false">
      <div class="dialog-content dialog-lg" @click.stop>
        <div class="dialog-header">
          <h4>Card Detail</h4>
          <button class="close-btn" @click="showCardDetailDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>Title</label>
            <input v-model="editCard.title" type="text" class="form-input" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="editCard.description" placeholder="Add a description..." class="form-input form-textarea" rows="3"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Priority</label>
              <select v-model="editCard.priority" class="form-input">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            <div class="form-group">
              <label>Assignee</label>
              <input v-model="editCard.assignee" type="text" class="form-input" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Due Date</label>
              <input v-model="editCard.due_date" type="date" class="form-input" />
            </div>
            <div class="form-group">
              <label>Tags</label>
              <input v-model="editCard.tags" type="text" placeholder="tag1, tag2..." class="form-input" />
            </div>
          </div>
          <div class="form-group">
            <label>Column</label>
            <select v-model="editCard.column_id" class="form-input">
              <option v-for="col in board?.columns || []" :key="col.id" :value="col.id">{{ col.name }}</option>
            </select>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showCardDetailDialog = false">Cancel</button>
          <button class="dialog-btn primary" @click="confirmEditCard" :disabled="!editCard.title.trim()">Save</button>
        </div>
      </div>
    </div>

    <div v-if="showAddColumnDialog" class="dialog-overlay" @click="showAddColumnDialog = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h4>Add Column</h4>
          <button class="close-btn" @click="showAddColumnDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>Column Name</label>
            <input v-model="newColumnName" type="text" placeholder="Column name..." class="form-input" @keydown.enter="confirmAddColumn" ref="columnNameInput" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Color</label>
              <input v-model="newColumnColor" type="color" class="form-color-input" />
            </div>
            <div class="form-group">
              <label>WIP Limit (0 = no limit)</label>
              <input v-model.number="newColumnWipLimit" type="number" min="0" class="form-input" />
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showAddColumnDialog = false">Cancel</button>
          <button class="dialog-btn primary" @click="confirmAddColumn" :disabled="!newColumnName.trim()">Add</button>
        </div>
      </div>
    </div>

    <div v-if="showColumnMenuDialog" class="context-menu-overlay" @click="showColumnMenuDialog = false">
      <div class="context-menu" :style="columnMenuStyle" @click.stop>
        <button class="context-menu-item" @click="editColumn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          Rename
        </button>
        <button class="context-menu-item danger" @click="deleteColumn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
          Delete Column
        </button>
      </div>
    </div>

    <div v-if="showEditColumnDialog" class="dialog-overlay" @click="showEditColumnDialog = false">
      <div class="dialog-content" @click.stop>
        <div class="dialog-header">
          <h4>Edit Column</h4>
          <button class="close-btn" @click="showEditColumnDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="dialog-body">
          <div class="form-group">
            <label>Column Name</label>
            <input v-model="editColumnName" type="text" class="form-input" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Color</label>
              <input v-model="editColumnColor" type="color" class="form-color-input" />
            </div>
            <div class="form-group">
              <label>WIP Limit (0 = no limit)</label>
              <input v-model.number="editColumnWipLimit" type="number" min="0" class="form-input" />
            </div>
          </div>
        </div>
        <div class="dialog-footer">
          <button class="dialog-btn secondary" @click="showEditColumnDialog = false">Cancel</button>
          <button class="dialog-btn primary" @click="confirmEditColumn" :disabled="!editColumnName.trim()">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import api from '../../utils/api'

interface KanbanCard {
  id: number
  title: string
  description: string
  assignee: string
  priority: string
  tags: string
  due_date: string
  column_id: number
  position: number
  archived?: number
  column_name?: string
  _linked_todo?: boolean
}

interface KanbanColumn {
  id: number
  name: string
  color: string
  position: number
  wip_limit: number
  cards: KanbanCard[]
}

interface KanbanBoard {
  id: number
  name: string
  description: string
  columns: KanbanColumn[]
}

const board = ref<KanbanBoard | null>(null)
const boards = ref<{ id: number; name: string }[]>([])
const currentBoardId = ref<number | null>(null)
const dragData = ref<{ card: KanbanCard; sourceColumnId: number; sourceIndex: number } | null>(null)
const dragOverColumnId = ref<number | null>(null)
const showAIPanel = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const showArchived = ref(false)
const archivedCards = ref<any[]>([])
const searchQuery = ref('')
const searchResults = ref<any[] | null>(null)

const showAddCardDialog = ref(false)
const newCard = ref({ title: '', description: '', assignee: '', priority: 'medium', tags: '', due_date: '' })
const newCardColumnId = ref<number | null>(null)
const cardTitleInput = ref<HTMLInputElement | null>(null)

const showCardDetailDialog = ref(false)
const editCard = ref<KanbanCard & { column_id: number }>({ id: 0, title: '', description: '', assignee: '', priority: 'medium', tags: '', due_date: '', column_id: 0, position: 0 })

const showAddColumnDialog = ref(false)
const newColumnName = ref('')
const newColumnColor = ref('#333333')
const newColumnWipLimit = ref(0)
const columnNameInput = ref<HTMLInputElement | null>(null)

const showColumnMenuDialog = ref(false)
const columnMenuTarget = ref<KanbanColumn | null>(null)
const columnMenuStyle = ref({ top: '0px', left: '0px' })

const showEditColumnDialog = ref(false)
const editColumnName = ref('')
const editColumnColor = ref('#333333')
const editColumnWipLimit = ref(0)

const totalCount = computed(() => {
  if (!board.value) return 0
  return board.value.columns.reduce((sum, col) => sum + (col.cards?.length || 0), 0)
})

const doneCount = computed(() => {
  if (!board.value) return 0
  const doneCol = board.value.columns.find(c => c.name.toLowerCase().includes('done') || c.name.toLowerCase().includes('complete'))
  return doneCol?.cards?.length || 0
})

const progressPercent = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((doneCount.value / totalCount.value) * 100)
})

function parseTags(tags: string): string[] {
  if (!tags) return []
  return tags.split(',').map(t => t.trim()).filter(Boolean)
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

function isOverdue(dateStr: string): boolean {
  if (!dateStr) return false
  try {
    return new Date(dateStr) < new Date(new Date().toDateString())
  } catch {
    return false
  }
}

function onDragStart(event: DragEvent, card: KanbanCard, columnId: number, index: number) {
  dragData.value = { card, sourceColumnId: columnId, sourceIndex: index }
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer?.setData('text/plain', String(card.id))
  const target = event.target as HTMLElement
  setTimeout(() => target.classList.add('dragging'), 0)
}

function onDragEnd() {
  dragData.value = null
  dragOverColumnId.value = null
}

function onDragOver(event: DragEvent, columnId: number) {
  event.dataTransfer!.dropEffect = 'move'
  dragOverColumnId.value = columnId
}

function onDragLeave() {
  dragOverColumnId.value = null
}

async function onDrop(_event: DragEvent, targetColumnId: number) {
  if (!dragData.value) return
  const { card, sourceColumnId } = dragData.value
  if (sourceColumnId === targetColumnId) {
    dragData.value = null
    dragOverColumnId.value = null
    return
  }
  try {
    await api.put(`/kanban/cards/${card.id}/move`, { target_column_id: targetColumnId, target_position: 0 })
    await loadBoard()
  } catch (e) { console.error('Failed to move card:', e) }
  dragData.value = null
  dragOverColumnId.value = null
}

function addCardToColumn(columnId: number) {
  newCardColumnId.value = columnId
  newCard.value = { title: '', description: '', assignee: '', priority: 'medium', tags: '', due_date: '' }
  showAddCardDialog.value = true
  nextTick(() => cardTitleInput.value?.focus())
}

async function confirmAddCard() {
  if (!newCard.value.title.trim() || !newCardColumnId.value) return
  try {
    await api.post('/kanban/cards', {
      column_id: newCardColumnId.value,
      title: newCard.value.title.trim(),
      description: newCard.value.description,
      assignee: newCard.value.assignee,
      priority: newCard.value.priority,
      tags: newCard.value.tags,
      due_date: newCard.value.due_date,
    })
    await loadBoard()
    showAddCardDialog.value = false
  } catch (e) { console.error('Failed to add card:', e) }
}

function openCardDetail(card: KanbanCard, _column: KanbanColumn) {
  editCard.value = { ...card }
  showCardDetailDialog.value = true
}

async function confirmEditCard() {
  if (!editCard.value.title.trim()) return
  try {
    const originalCard = findCardById(editCard.value.id)
    if (originalCard && originalCard.column_id !== editCard.value.column_id) {
      await api.put(`/kanban/cards/${editCard.value.id}/move`, { target_column_id: editCard.value.column_id, target_position: 0 })
    }
    await api.put(`/kanban/cards/${editCard.value.id}`, {
      title: editCard.value.title.trim(),
      description: editCard.value.description,
      assignee: editCard.value.assignee,
      priority: editCard.value.priority,
      tags: editCard.value.tags,
      due_date: editCard.value.due_date,
    })
    await loadBoard()
    showCardDetailDialog.value = false
  } catch (e) { console.error('Failed to update card:', e) }
}

function findCardById(cardId: number): KanbanCard | null {
  if (!board.value) return null
  for (const col of board.value.columns) {
    const found = col.cards?.find(c => c.id === cardId)
    if (found) return found
  }
  return null
}

async function deleteCard(cardId: number) {
  try {
    await api.delete(`/kanban/cards/${cardId}`)
    await loadBoard()
    if (showArchived.value) await loadArchivedCards()
  } catch (e) { console.error('Failed to delete card:', e) }
}

async function archiveCard(cardId: number) {
  try {
    await api.put(`/kanban/cards/${cardId}/archive`)
    await loadBoard()
  } catch (e) { console.error('Failed to archive card:', e) }
}

async function unarchiveCard(cardId: number) {
  try {
    await api.put(`/kanban/cards/${cardId}/unarchive`)
    await loadArchivedCards()
    await loadBoard()
  } catch (e) { console.error('Failed to unarchive card:', e) }
}

async function loadArchivedCards() {
  if (!currentBoardId.value) return
  try {
    const res = await api.get(`/kanban/boards/${currentBoardId.value}/archived`)
    archivedCards.value = res.data.cards || []
  } catch (e) { console.error('Failed to load archived cards:', e) }
}

function openColumnMenu(column: KanbanColumn) {
  columnMenuTarget.value = column
  showColumnMenuDialog.value = true
}

function editColumn() {
  if (!columnMenuTarget.value) return
  editColumnName.value = columnMenuTarget.value.name
  editColumnColor.value = columnMenuTarget.value.color || '#7c6ff7'
  editColumnWipLimit.value = columnMenuTarget.value.wip_limit || 0
  showColumnMenuDialog.value = false
  showEditColumnDialog.value = true
}

async function confirmEditColumn() {
  if (!columnMenuTarget.value || !editColumnName.value.trim()) return
  try {
    await api.put(`/kanban/columns/${columnMenuTarget.value.id}`, {
      name: editColumnName.value.trim(),
      color: editColumnColor.value,
      wip_limit: editColumnWipLimit.value,
    })
    await loadBoard()
    showEditColumnDialog.value = false
  } catch (e) { console.error('Failed to update column:', e) }
}

async function deleteColumn() {
  if (!columnMenuTarget.value) return
  try {
    await api.delete(`/kanban/columns/${columnMenuTarget.value.id}`)
    await loadBoard()
    showColumnMenuDialog.value = false
  } catch (e) { console.error('Failed to delete column:', e) }
}

async function confirmAddColumn() {
  if (!newColumnName.value.trim() || !currentBoardId.value) return
  try {
    await api.post('/kanban/columns', {
      board_id: currentBoardId.value,
      name: newColumnName.value.trim(),
      color: newColumnColor.value,
      wip_limit: newColumnWipLimit.value,
    })
    await loadBoard()
    showAddColumnDialog.value = false
    newColumnName.value = ''
    newColumnColor.value = '#7c6ff7'
    newColumnWipLimit.value = 0
  } catch (e) { console.error('Failed to add column:', e) }
}

async function onSearch() {
  if (!searchQuery.value.trim() || !currentBoardId.value) {
    searchResults.value = null
    return
  }
  try {
    const res = await api.get(`/kanban/boards/${currentBoardId.value}/search`, { params: { q: searchQuery.value.trim() } })
    searchResults.value = res.data.results || []
  } catch (e) {
    console.error('Search failed:', e)
    searchResults.value = null
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = null
}

function getBoardData() {
  if (!board.value) return { columns: [], cards: [] }
  const columns = board.value.columns.map(c => ({ id: c.id, name: c.name, card_count: c.cards?.length || 0 }))
  const cards = board.value.columns.flatMap(c => (c.cards || []).map(card => ({
    id: card.id, title: card.title, priority: card.priority, assignee: card.assignee, column: c.name, due_date: card.due_date,
  })))
  return { columns, cards }
}

async function aiSuggestProgress() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/kanban/assist', { action: 'suggest_progress', params: getBoardData() })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: 'Progress analysis failed.' } }
  finally { aiLoading.value = false }
}

async function aiPrioritizeCards() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/kanban/assist', { action: 'prioritize_cards', params: getBoardData() })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: 'Prioritization failed.' } }
  finally { aiLoading.value = false }
}

async function aiEstimateCompletion() {
  aiLoading.value = true; showAIPanel.value = true; aiResult.value = null
  try {
    const res = await api.post('/ai/workspace/kanban/assist', { action: 'estimate_completion', params: getBoardData() })
    aiResult.value = res.data
  } catch (e) { aiResult.value = { result: 'Estimation failed.' } }
  finally { aiLoading.value = false }
}

function applyPriorityOrder() {
  if (!aiResult.value?.ordered_cards || !board.value) return
  const orderMap = new Map(aiResult.value.ordered_cards.map((c: any, i: number) => [String(c.card_id), i]))
  for (const col of board.value.columns) {
    col.cards.sort((a, b) => (Number(orderMap.get(String(a.id)) ?? 999)) - (Number(orderMap.get(String(b.id)) ?? 999)))
  }
  showAIPanel.value = false
}

async function onBoardSwitch() {
  if (currentBoardId.value != null) {
    await loadBoardById(currentBoardId.value)
  }
}

async function loadBoard() {
  if (currentBoardId.value != null) {
    await loadBoardById(currentBoardId.value)
  } else {
    try {
      const boardsRes = await api.get('/kanban/boards')
      boards.value = boardsRes.data.boards || []
      if (boards.value.length === 0) {
        const createRes = await api.post('/kanban/boards', { name: 'My Board', description: 'Default kanban board' })
        currentBoardId.value = createRes.data.id
        boards.value = [{ id: createRes.data.id, name: 'My Board' }]
      } else {
        currentBoardId.value = boards.value[0].id
      }
      if (currentBoardId.value != null) {
        await loadBoardById(currentBoardId.value)
      }
    } catch (e) { console.error('Failed to load board:', e) }
  }
}

async function loadBoardById(boardId: number) {
  try {
    const boardRes = await api.get(`/kanban/boards/${boardId}`)
    board.value = boardRes.data
    await loadCardTodoLinks()
  } catch (e) { console.error('Failed to load board:', e) }
}

async function loadCardTodoLinks() {
  if (!board.value) return
  const cardIds: number[] = []
  for (const col of board.value.columns) {
    for (const card of col.cards || []) {
      cardIds.push(card.id)
    }
  }
  for (const cardId of cardIds) {
    try {
      const res = await api.get(`/kanban/todo-bridge/linked/${cardId}`)
      const todos = res.data.todos || []
      if (todos.length > 0) {
        for (const col of board.value!.columns) {
          for (const card of col.cards || []) {
            if (card.id === cardId) {
              ;(card as any)._linked_todo = todos[0]
              break
            }
          }
        }
      }
    } catch {
      // ignore - card may not have linked todos
    }
  }
}

async function cardToTodo(card: KanbanCard) {
  if (!currentBoardId.value) return
  try {
    await api.post('/kanban/todo-bridge/to-todo', {
      card_id: card.id,
      board_id: currentBoardId.value,
    })
    await loadBoard()
  } catch (e) {
    console.error('Failed to create todo from card:', e)
  }
}

function goToTodo() {
  const event = new CustomEvent('workspace-switch', { detail: { app: 'todo' } })
  window.dispatchEvent(event)
}

watch(showArchived, (val) => {
  if (val) loadArchivedCards()
})

onMounted(loadBoard)
</script>

<style scoped>
.kanban-board { height: 100%; display: flex; flex-direction: column; background: var(--bg-primary); color: var(--text-primary); }

.kanban-header { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-sm) var(--spacing-lg); border-bottom: 1px solid var(--border-color); gap: var(--spacing-md); }
.header-left { display: flex; align-items: center; gap: var(--spacing-sm); min-width: 0; }
.header-left h3 { margin: 0; font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--text-primary); white-space: nowrap; }
.board-select { padding: var(--spacing-xs) var(--spacing-sm); border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--input-bg); color: var(--text-primary); font-size: var(--font-size-sm); }
.header-center { flex: 1; max-width: 320px; }
.search-box { display: flex; align-items: center; gap: var(--spacing-xs); padding: var(--spacing-xs) var(--spacing-sm); border: 1px solid var(--border-color); border-radius: var(--radius-md); background: var(--input-bg); }
.search-box svg { color: var(--text-tertiary); flex-shrink: 0; }
.search-input { border: none; background: transparent; color: var(--text-primary); font-size: var(--font-size-sm); width: 100%; outline: none; }
.search-input::placeholder { color: var(--text-tertiary); }
.search-clear { display: flex; align-items: center; color: var(--text-tertiary); background: none; border: none; cursor: pointer; padding: 0; }
.search-clear:hover { color: var(--text-secondary); }
.header-right { display: flex; align-items: center; gap: var(--spacing-xs); }
.header-divider { width: 1px; height: 20px; background: var(--border-color); margin: 0 var(--spacing-xs); }

.ai-header-btn { display: flex; align-items: center; gap: var(--spacing-xs); padding: var(--spacing-xs) var(--spacing-sm); border-radius: var(--radius-sm); font-size: var(--font-size-xs); color: var(--text-secondary); background: none; border: 1px solid var(--border-color); cursor: pointer; white-space: nowrap; }
.ai-header-btn:hover { background: var(--bg-secondary); border-color: var(--text-tertiary); }
.ai-header-btn svg { flex-shrink: 0; }

.icon-btn { display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-secondary); cursor: pointer; color: var(--text-secondary); }
.icon-btn:hover { background: var(--border-color); color: var(--text-primary); }
.icon-btn.active { background: var(--primary-light); border-color: var(--primary); color: var(--primary); }

.kanban-progress-bar { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-xs) var(--spacing-lg); background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); }
.progress-track { flex: 1; height: 4px; background: var(--border-color); border-radius: var(--radius-full); overflow: hidden; }
.progress-fill { height: 100%; background: var(--primary); border-radius: var(--radius-full); transition: width var(--transition-smooth); }
.progress-label { font-size: var(--font-size-xs); color: var(--text-tertiary); white-space: nowrap; }

.kanban-content { flex: 1; display: flex; overflow: hidden; }
.kanban-columns { display: flex; gap: var(--spacing-md); padding: var(--spacing-md); flex: 1; overflow-x: auto; overflow-y: hidden; }

.kanban-column { min-width: 280px; max-width: 320px; background: var(--bg-secondary); border-radius: var(--radius-md); display: flex; flex-direction: column; border-top: 3px solid var(--primary); flex-shrink: 0; max-height: 100%; }
.column-header { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-sm) var(--spacing-md); }
.column-header-left { display: flex; align-items: center; gap: var(--spacing-xs); min-width: 0; }
.column-color-dot { width: 8px; height: 8px; border-radius: var(--radius-full); flex-shrink: 0; }
.column-name { font-weight: var(--font-weight-semibold); font-size: var(--font-size-sm); color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.column-count { background: var(--border-color); border-radius: var(--radius-full); padding: 1px var(--spacing-sm); font-size: var(--font-size-xs); font-weight: var(--font-weight-normal); color: var(--text-secondary); white-space: nowrap; }
.column-count.wip-warning { background: var(--text-primary); color: var(--bg-primary); font-weight: var(--font-weight-bold); }
.column-header-actions { display: flex; gap: 2px; opacity: 0; transition: opacity var(--transition-fast); }
.kanban-column:hover .column-header-actions { opacity: 1; }
.column-action-btn { display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; border: none; background: none; color: var(--text-tertiary); cursor: pointer; border-radius: var(--radius-sm); }
.column-action-btn:hover { background: var(--border-color); color: var(--text-primary); }

.column-cards { padding: 0 var(--spacing-sm) var(--spacing-sm); flex: 1; overflow-y: auto; transition: background var(--transition-fast); border-radius: 0 0 var(--radius-md) var(--radius-md); }
.column-cards.drag-over { background: var(--bg-tertiary); }

.kanban-card { background: var(--card-bg); border-radius: var(--radius-md); padding: var(--spacing-sm) var(--spacing-md); margin-bottom: var(--spacing-sm); border: 1px solid var(--border-color); cursor: grab; transition: box-shadow var(--transition-fast), border-color var(--transition-fast); }
.kanban-card:active { cursor: grabbing; }
.kanban-card:hover { border-color: var(--primary-hover); box-shadow: var(--shadow); }
.kanban-card.dragging { opacity: 0.5; transform: rotate(2deg); }

.card-top-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing-xs); }
.card-priority { padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); text-transform: capitalize; font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); }
.priority-high { background: var(--text-primary); color: var(--bg-primary); }
.priority-medium { background: var(--text-secondary); color: var(--bg-primary); }
.priority-low { background: var(--border-color); color: var(--text-secondary); }
.card-actions { display: flex; gap: 2px; opacity: 0; transition: opacity var(--transition-fast); }
.kanban-card:hover .card-actions { opacity: 1; }
.card-action-btn { display: flex; align-items: center; justify-content: center; width: 22px; height: 22px; border: none; background: none; color: var(--text-tertiary); cursor: pointer; border-radius: var(--radius-sm); }
.card-action-btn:hover { background: var(--border-color); color: var(--text-secondary); }
.card-action-btn.delete:hover { color: var(--ws-danger); }
.card-action-btn.bridge { color: var(--text-secondary); }
.card-action-btn.bridge:hover { color: var(--primary-hover); }

.card-title { font-size: var(--font-size-base); font-weight: var(--font-weight-medium); color: var(--text-primary); cursor: pointer; word-break: break-word; }
.card-title:hover { color: var(--primary-hover); }
.card-desc { font-size: var(--font-size-sm); color: var(--text-tertiary); margin-top: var(--spacing-xs); margin-bottom: var(--spacing-xs); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta { display: flex; align-items: center; gap: var(--spacing-sm); font-size: var(--font-size-xs); flex-wrap: wrap; margin-top: var(--spacing-xs); }
.card-assignee { background: var(--primary-light); color: var(--primary); padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); }
.card-due { color: var(--text-tertiary); }
.card-due.overdue { color: var(--text-primary); font-weight: var(--font-weight-bold); }
.card-todo-badge { display: inline-flex; align-items: center; gap: 3px; font-size: 10px; color: var(--text-secondary); background: var(--bg-tertiary); padding: 1px 6px; border-radius: var(--radius-sm); cursor: pointer; }
.card-todo-badge:hover { background: var(--text-secondary); color: var(--bg-primary); }
.card-tags { display: flex; gap: var(--spacing-xs); margin-top: var(--spacing-xs); flex-wrap: wrap; }
.card-tag { background: var(--border-color); color: var(--text-secondary); padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); font-size: var(--font-size-xs); }

.add-card-btn { display: flex; align-items: center; gap: var(--spacing-xs); width: 100%; padding: var(--spacing-sm) var(--spacing-md); border: none; background: transparent; color: var(--text-tertiary); cursor: pointer; border-radius: var(--radius-sm); font-size: var(--font-size-sm); }
.add-card-btn:hover { background: var(--border-color); color: var(--text-primary); }

.archived-view { flex: 1; padding: var(--spacing-lg); overflow-y: auto; }
.archived-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--spacing-lg); }
.archived-header h4 { margin: 0; font-size: var(--font-size-md); color: var(--text-primary); }
.archived-list { display: flex; flex-direction: column; gap: var(--spacing-sm); }
.archived-card { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-sm) var(--spacing-md); background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); }
.archived-card-info { display: flex; align-items: center; gap: var(--spacing-sm); min-width: 0; }
.archived-card-title { font-size: var(--font-size-base); color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.archived-card-col { font-size: var(--font-size-xs); color: var(--text-tertiary); background: var(--bg-secondary); padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); }
.archived-card-actions { display: flex; gap: var(--spacing-xs); flex-shrink: 0; }
.restore-btn { padding: var(--spacing-xs) var(--spacing-sm); border: 1px solid var(--primary); background: none; color: var(--primary); border-radius: var(--radius-sm); font-size: var(--font-size-xs); cursor: pointer; }
.restore-btn:hover { background: var(--primary-light); }

.empty-state { display: flex; align-items: center; justify-content: center; height: 200px; color: var(--text-tertiary); font-size: var(--font-size-base); }

.ai-panel { width: 320px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-sm) var(--spacing-md); border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: var(--font-size-base); color: var(--text-primary); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; display: flex; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: var(--spacing-md); }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: var(--spacing-md); padding: var(--spacing-xl); color: var(--text-tertiary); }
.spinner { width: 28px; height: 28px; border: 3px solid var(--border-color); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-section { margin-bottom: var(--spacing-lg); }
.ai-section h5 { font-size: var(--font-size-xs); color: var(--text-tertiary); margin: 0 0 var(--spacing-sm); text-transform: uppercase; letter-spacing: 0.5px; }
.ai-result { color: var(--text-primary); }
.analysis-text { font-size: var(--font-size-sm); line-height: 1.6; color: var(--text-secondary); padding: var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); }
.suggestion-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-xs) var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: var(--spacing-xs); font-size: var(--font-size-sm); }
.suggestion-type { padding: 1px var(--spacing-sm); border-radius: var(--radius-sm); font-size: 10px; font-weight: var(--font-weight-semibold); }
.suggestion-type.optimization { background: var(--text-primary); color: var(--bg-primary); }
.suggestion-type.warning { background: var(--text-secondary); color: var(--bg-primary); }
.suggestion-type.action { background: var(--text-tertiary); color: var(--bg-primary); }
.suggestion-desc { flex: 1; color: var(--text-secondary); }
.suggestion-priority { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.priority-item { display: flex; align-items: center; gap: var(--spacing-sm); padding: var(--spacing-xs) var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); margin-bottom: var(--spacing-xs); font-size: var(--font-size-sm); }
.priority-rank { background: var(--text-primary); color: var(--bg-primary); width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: var(--font-size-xs); flex-shrink: 0; }
.priority-title { flex: 1; color: var(--text-secondary); }
.priority-reason { color: var(--text-tertiary); font-size: var(--font-size-xs); }
.estimate-date { font-size: var(--font-size-lg); color: var(--text-primary); font-weight: var(--font-weight-semibold); }
.estimate-confidence { font-size: var(--font-size-sm); color: var(--text-secondary); display: block; margin-top: var(--spacing-xs); }
.estimate-detail { font-size: var(--font-size-sm); color: var(--text-tertiary); margin-top: var(--spacing-xs); padding: var(--spacing-xs) var(--spacing-sm); background: var(--bg-primary); border-radius: var(--radius-sm); }
.apply-btn { width: 100%; padding: var(--spacing-sm); background: var(--primary); color: var(--bg-primary); border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: var(--font-size-sm); margin-top: var(--spacing-sm); }
.apply-btn:hover { background: var(--primary-hover); }
.ai-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: var(--text-tertiary); font-size: var(--font-size-sm); }

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--overlay-bg); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog-content { background: var(--card-bg); border-radius: var(--radius-lg); width: 440px; max-width: 90vw; box-shadow: var(--shadow-lg); }
.dialog-content.dialog-lg { width: 560px; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-md) var(--spacing-lg); border-bottom: 1px solid var(--border-color); }
.dialog-header h4 { margin: 0; font-size: var(--font-size-md); color: var(--text-primary); }
.dialog-body { padding: var(--spacing-lg); }
.dialog-footer { display: flex; justify-content: flex-end; gap: var(--spacing-md); padding: var(--spacing-md) var(--spacing-lg); border-top: 1px solid var(--border-color); }

.form-group { margin-bottom: var(--spacing-md); }
.form-group label { display: block; font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); margin-bottom: var(--spacing-xs); color: var(--text-secondary); }
.form-input { width: 100%; padding: var(--spacing-sm) var(--spacing-md); border: 1px solid var(--border-color); border-radius: var(--radius-md); background: var(--input-bg); color: var(--text-primary); font-size: var(--font-size-base); outline: none; }
.form-input:focus { border-color: var(--primary-color); }
.form-textarea { resize: vertical; min-height: 60px; font-family: inherit; }
.form-color-input { width: 48px; height: 32px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: none; cursor: pointer; padding: 2px; }
.form-row { display: flex; gap: var(--spacing-md); }
.form-row .form-group { flex: 1; }

.dialog-btn { padding: var(--spacing-sm) var(--spacing-lg); border-radius: var(--radius-sm); font-size: var(--font-size-base); cursor: pointer; transition: all var(--transition-normal); }
.dialog-btn:active:not(:disabled) { transform: scale(0.97); }
.dialog-btn.secondary { background: transparent; border: 1px solid var(--border-color); color: var(--text-secondary); }
.dialog-btn.secondary:hover { background: var(--bg-secondary); }
.dialog-btn.primary { background: var(--primary); border: none; color: #ffffff; }
.dialog-btn.primary:hover:not(:disabled) { background: var(--primary-hover); }
.dialog-btn.primary:disabled { opacity: 0.5; cursor: not-allowed; }

.context-menu-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 150; }
.context-menu { position: fixed; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: var(--radius-md); box-shadow: var(--shadow-md); padding: var(--spacing-xs); min-width: 160px; }
.context-menu-item { display: flex; align-items: center; gap: var(--spacing-sm); width: 100%; padding: var(--spacing-sm) var(--spacing-md); border: none; background: none; color: var(--text-primary); font-size: var(--font-size-sm); cursor: pointer; border-radius: var(--radius-sm); }
.context-menu-item:hover { background: var(--bg-secondary); }
.context-menu-item.danger { color: var(--ws-danger); }
.context-menu-item.danger:hover { background: var(--ws-danger); color: var(--bg-primary); }
</style>
