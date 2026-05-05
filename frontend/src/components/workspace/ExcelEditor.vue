<template>
  <div class="excel-editor" @keydown="handleGlobalKeydown" tabindex="0" ref="editorRef">
    <div class="lo-menubar">
      <div class="menu-item" v-for="menu in excelMenus" :key="menu.label" @click="toggleMenu(menu.label)" @mouseenter="openMenuOnHover(menu.label)">
        {{ menu.label }}
        <div v-if="activeMenu === menu.label" class="menu-dropdown">
          <div v-for="item in menu.items" :key="item.label" class="menu-dropdown-item" :class="{ disabled: item.disabled }" @click.stop="item.action && item.action(); activeMenu = ''">
            <span class="menu-item-label">{{ item.label }}</span>
            <span v-if="item.shortcut" class="menu-item-shortcut">{{ item.shortcut }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="lo-ribbon">
      <div class="ribbon-tabs">
        <button v-for="tab in excelRibbonTabs" :key="tab.id" class="ribbon-tab" :class="{ active: activeRibbonTab === tab.id }" @click="activeRibbonTab = tab.id">{{ tab.label }}</button>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'home'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" @click="engine.undo()" :disabled="engine.undoStack.value.length === 0" title="Undo (Ctrl+Z)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8l4-4v3h4a3 3 0 010 6H9v-2h2a1 1 0 000-2H7v3L3 8z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" @click="engine.redo()" :disabled="engine.redoStack.value.length === 0" title="Redo (Ctrl+Y)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M13 8l-4-4v3H5a3 3 0 000 6h2v-2H5a1 1 0 010-2h4v3l4-4z" fill="currentColor"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Edit</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" :class="{ active: currentFormat.bold }" @click="toggleBold" title="Bold (Ctrl+B)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 2h5a3.5 3.5 0 012.5 6 3.5 3.5 0 01-2 6.5H4V2zm2 2v3.5h3a1.75 1.75 0 000-3.5H6zm0 5.5V13h3.5a1.75 1.75 0 000-3.5H6z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: currentFormat.italic }" @click="toggleItalic" title="Italic (Ctrl+I)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M7 2h6v2h-2.2L9 12h2v2H5v-2h2.2L9 4H7V2z" fill="currentColor"/></svg>
            </button>
            <label class="lo-btn" title="Text Color">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 13h8l-2-6H6L4 13zm1.5-4h5L12 12H4l1.5-3zM8 2l2.5 4h-5L8 2z" fill="currentColor"/><rect x="3" y="14" width="10" height="1.5" rx="0.5" fill="currentColor"/></svg>
              <input type="color" class="hidden-color-input" :value="currentFormat.color || '#000000'" @input="setTextColor(($event.target as HTMLInputElement).value)" />
            </label>
            <label class="lo-btn" title="Background Color">
              <svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
              <input type="color" class="hidden-color-input" :value="currentFormat.bgColor || '#ffffff'" @input="setBgColor(($event.target as HTMLInputElement).value)" />
            </label>
          </div>
          <div class="ribbon-group-label">Format</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" :class="{ active: currentFormat.align === 'left' }" @click="setAlign('left')" title="Align Left">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm0 3h8v1H2V6zm0 3h12v1H2V9zm0 3h8v1H2v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: currentFormat.align === 'center' }" @click="setAlign('center')" title="Center">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm2 3h8v1H4V6zm-2 3h12v1H2V9zm2 3h8v1H4v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: currentFormat.align === 'right' }" @click="setAlign('right')" title="Align Right">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm4 3h8v1H6V6zm-4 3h12v1H2V9zm4 3h8v1H6v-1z" fill="currentColor"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Align</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <select class="lo-select" :value="currentNumFormat.type" @change="setNumFormat(($event.target as HTMLSelectElement).value)" title="Number Format">
              <option value="auto">General</option>
              <option value="number">Number</option>
              <option value="currency">Currency</option>
              <option value="percent">Percent</option>
              <option value="date">Date</option>
            </select>
          </div>
          <div class="ribbon-group-label">Number</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" @click="engine.addRow()" title="Insert Row">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
            </button>
            <button class="lo-btn" @click="engine.addColumn()" title="Insert Column">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
            </button>
            <button class="lo-btn" @click="deleteSelectedRow" :disabled="engine.activeCell.ri < 0" title="Delete Row">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8h10" stroke="currentColor" stroke-width="2" fill="none"/></svg>
            </button>
            <button class="lo-btn" @click="deleteSelectedCol" :disabled="engine.activeCell.ci < 0" title="Delete Column">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8h10" stroke="currentColor" stroke-width="2" fill="none"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Cells</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'data'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="engine.sortColumn(engine.activeCell.ci, true)" :disabled="engine.activeCell.ci < 0" title="Sort Ascending">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M3 5h10M3 8h7M3 11h4" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
              <span>Sort A-Z</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="engine.sortColumn(engine.activeCell.ci, false)" :disabled="engine.activeCell.ci < 0" title="Sort Descending">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M3 5h4M3 8h7M3 11h10" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
              <span>Sort Z-A</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="toggleFilterForCol" :disabled="engine.activeCell.ci < 0" :class="{ active: engine.filterState[engine.activeCell.ci]?.active }" title="Filter">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h12l-4.5 5.5V13l-3 1.5V7.5L2 2z" fill="currentColor"/></svg>
              <span>Filter</span>
            </button>
          </div>
          <div class="ribbon-group-label">Sort & Filter</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="triggerCSVImport" title="Import CSV">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M8 2v9M5 8l3 3 3-3M3 13h10" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
              <span>Import</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="doCSVExport" title="Export CSV">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M8 2v9M5 8l3 3 3-3M3 13h10" stroke="currentColor" stroke-width="1.2" fill="none" transform="rotate(180,8,8)"/></svg>
              <span>Export CSV</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="exportXlsx" title="Export XLSX">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
              <span>XLSX</span>
            </button>
          </div>
          <div class="ribbon-group-label">Import/Export</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="showConditionalDialog = true" title="Conditional Formatting">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="2" width="5" height="5" rx="1" fill="currentColor" opacity="0.6"/><rect x="9" y="2" width="5" height="5" rx="1" fill="currentColor" opacity="0.3"/><rect x="2" y="9" width="5" height="5" rx="1" fill="currentColor" opacity="0.3"/><rect x="9" y="9" width="5" height="5" rx="1" fill="currentColor" opacity="0.6"/></svg>
              <span>Rules</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="toggleFreeze" :class="{ active: engine.frozenRows.value > 0 }" title="Freeze Header">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h12v12H2V2zm0 4h12M2 10h12" stroke="currentColor" stroke-width="1" fill="none"/></svg>
              <span>Freeze</span>
            </button>
          </div>
          <div class="ribbon-group-label">Tools</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'ai'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner ai-tools">
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('analyze_data')" title="AI Data Analysis">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="1" y="2" width="14" height="2" rx="1" fill="currentColor"/><rect x="1" y="6" width="10" height="2" rx="1" fill="currentColor"/><rect x="1" y="10" width="12" height="2" rx="1" fill="currentColor"/></svg>
              <span>Analyze</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('suggest_formula')" title="AI Formula Suggestion">
              <svg width="18" height="18" viewBox="0 0 16 16"><text x="2" y="12" font-size="12" font-weight="bold" fill="currentColor">fx</text></svg>
              <span>Formula</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('generate_chart')" title="AI Chart Generation">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="8" width="3" height="6" fill="currentColor" opacity="0.6"/><rect x="6.5" y="4" width="3" height="10" fill="currentColor" opacity="0.8"/><rect x="11" y="2" width="3" height="12" fill="currentColor"/></svg>
              <span>Chart</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('clean_data')" title="AI Data Cleaning">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M12 1l3 3-9 9H3v-3l9-9z" fill="currentColor"/></svg>
              <span>Clean</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('forecast')" title="AI Forecast">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 12l3-4 3 2 3-5 3 3" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
              <span>Forecast</span>
            </button>
          </div>
          <div class="ribbon-group-label">AI Assistant</div>
        </div>
      </div>
    </div>

    <div class="formula-bar">
      <span class="fx-label">fx</span>
      <input
        v-model="formulaInput"
        class="formula-input"
        placeholder="输入公式 (如 =SUM(A1:A5), =IF(A1>10,1,0), =A1+B1*C1)"
        @keydown.enter="applyFormula"
      />
    </div>

    <div class="excel-content">
      <div class="table-container" ref="tableContainerRef" @scroll="onTableScroll">
        <table class="spreadsheet" @mousedown="onTableMouseDown" @mousemove="onTableMouseMove" @mouseup="onTableMouseUp">
          <thead>
            <tr>
              <th class="corner-cell" @click="selectAll"></th>
              <th
                v-for="(name, ci) in engine.colNames.value"
                :key="ci"
                :class="['col-header', { selected: isColSelected(ci), filtered: engine.filterState[ci]?.active }]"
                :style="{ width: engine.colWidths.value[ci] + 'px' }"
                @click="selectColumn(ci)"
                @contextmenu.prevent="showContextMenu($event, -1, ci)"
              >
                <span class="col-name">{{ name }}</span>
                <div class="col-resize" @mousedown.stop="startColResize(ci, $event)"></div>
                <button v-if="engine.filterState[ci]?.active" class="filter-indicator" @click.stop="openFilterDropdown(ci, $event)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in engine.rows.value" :key="ri" v-show="!engine.isRowFiltered(ri)">
              <td
                :class="['row-header', { selected: isRowSelected(ri) }]"
                :style="{ height: engine.rowHeights.value[ri] + 'px' }"
                @click="selectRow(ri)"
                @contextmenu.prevent="showContextMenu($event, ri, -1)"
              >
                <span class="row-num">{{ ri + 1 }}</span>
                <div class="row-resize" @mousedown.stop="startRowResize(ri, $event)"></div>
              </td>
              <td
                v-for="(cell, ci) in row"
                :key="ci"
                :data-ri="ri"
                :data-ci="ci"
                :class="['cell', {
                  selected: engine.isCellSelected(ri, ci),
                  'active-cell': engine.activeCell.ri === ri && engine.activeCell.ci === ci,
                  formula: String(cell).startsWith('='),
                  'find-highlight': isFindHighlight(ri, ci),
                }]"
                :style="getCellStyleObj(ri, ci)"
                @click.exact="onCellClick(ri, ci)"
                @click.shift="onCellShiftClick(ri, ci)"
                @contextmenu.prevent="showContextMenu($event, ri, ci)"
              >
                <input
                  v-if="editingCell.ri === ri && editingCell.ci === ci"
                  :value="editValue"
                  class="cell-input editing"
                  @input="editValue = ($event.target as HTMLInputElement).value"
                  @keydown.enter.prevent="commitEdit"
                  @keydown.escape.prevent="cancelEdit"
                  @keydown.tab.prevent="commitEdit(); moveAndEdit(ri, ci, 'right')"
                  @keydown.arrow-up.prevent="commitEdit(); moveAndEdit(ri, ci, 'up')"
                  @keydown.arrow-down.prevent="commitEdit(); moveAndEdit(ri, ci, 'down')"
                  @keydown.arrow-left.prevent="commitEdit(); moveAndEdit(ri, ci, 'left')"
                  @keydown.arrow-right.prevent="commitEdit(); moveAndEdit(ri, ci, 'right')"
                  ref="editingInputRef"
                />
                <span v-else class="cell-display" @dblclick="startEdit(ri, ci)">{{ engine.getDisplayValue(ri, ci) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <AiAssistantPanel
        v-if="aiPanelOpen"
        :loading="aiLoading"
        :result="aiResult"
        :action-label="aiCurrentAction"
        @close="aiPanelOpen = false"
        @apply="applyAIResult"
      />
    </div>

    <div class="excel-footer">
      <div class="footer-left">
        <span v-if="engine.activeCell.ri >= 0 && engine.activeCell.ci >= 0" class="cell-ref">
          {{ engine.colNames.value[engine.activeCell.ci] }}{{ engine.activeCell.ri + 1 }}
        </span>
        <span v-if="engine.isSelectedRange()" class="range-info">
          {{ selectionSize }}
        </span>
      </div>
      <div class="footer-center">
        <span v-if="selectionStats.count > 0" class="selection-stats">
          Sum: {{ selectionStats.sum.toFixed(2) }} | Avg: {{ selectionStats.avg.toFixed(2) }} | Count: {{ selectionStats.count }}
        </span>
      </div>
      <div class="footer-right">
        <span class="stats">{{ engine.rows.value.length }} rows x {{ engine.colNames.value.length }} cols</span>
      </div>
    </div>

    <div v-if="contextMenu.visible" class="context-menu" :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }" @click="contextMenu.visible = false">
      <button @click="contextAction('cut')">Cut</button>
      <button @click="contextAction('copy')">Copy</button>
      <button @click="contextAction('paste')">Paste</button>
      <div class="context-divider"></div>
      <button @click="contextAction('insertRowAbove')">Insert Row Above</button>
      <button @click="contextAction('insertRowBelow')">Insert Row Below</button>
      <button @click="contextAction('insertColLeft')">Insert Column Left</button>
      <button @click="contextAction('insertColRight')">Insert Column Right</button>
      <div class="context-divider"></div>
      <button @click="contextAction('deleteRow')">Delete Row</button>
      <button @click="contextAction('deleteCol')">Delete Column</button>
      <div class="context-divider"></div>
      <button @click="contextAction('clearCells')">Clear Cells</button>
      <button @click="contextAction('sortAsc')">Sort A-Z</button>
      <button @click="contextAction('sortDesc')">Sort Z-A</button>
    </div>

    <div v-if="findState.isOpen" class="find-dialog">
      <div class="find-header">
        <span>Find & Replace</span>
        <button class="close-btn" @click="findState.isOpen = false">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="find-body">
        <input v-model="findState.query" class="find-input" placeholder="Find..." @input="doFind" />
        <input v-model="findState.replaceWith" class="find-input" placeholder="Replace with..." />
        <div class="find-options">
          <label><input type="checkbox" v-model="findState.caseSensitive" @change="doFind" /> Case sensitive</label>
        </div>
        <div class="find-actions">
          <button @click="engine.findPrev()" :disabled="findState.results.length === 0">Prev</button>
          <button @click="engine.findNext()" :disabled="findState.results.length === 0">Next</button>
          <button @click="engine.replaceCurrent()" :disabled="findState.currentIndex < 0">Replace</button>
          <button @click="engine.replaceAll()" :disabled="findState.results.length === 0">All</button>
        </div>
        <span v-if="findState.query" class="find-count">{{ findState.results.length }} found</span>
      </div>
    </div>

    <div v-if="filterDropdown.visible" class="filter-dropdown" :style="{ left: filterDropdown.x + 'px', top: filterDropdown.y + 'px' }">
      <div class="filter-header">
        <span>Filter: {{ engine.colNames.value[filterDropdown.ci] }}</span>
        <button @click="filterDropdown.visible = false" class="close-btn">
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
        </button>
      </div>
      <div class="filter-list">
        <label v-for="val in filterDropdown.values" :key="val" class="filter-item">
          <input type="checkbox" :checked="!filterDropdown.excluded.includes(val)" @change="toggleFilterValue(filterDropdown.ci, val)" />
          <span>{{ val || '(empty)' }}</span>
        </label>
      </div>
      <div class="filter-actions">
        <button @click="selectAllFilterValues(filterDropdown.ci)">Select All</button>
        <button @click="clearFilter(filterDropdown.ci)">Clear Filter</button>
      </div>
    </div>

    <div v-if="showConditionalDialog" class="modal-overlay" @click.self="showConditionalDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>Conditional Formatting Rules</h4>
          <button class="close-btn" @click="showConditionalDialog = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-for="(rule, idx) in engine.conditionalRules.value" :key="rule.id" class="cond-rule">
            <span class="cond-range">{{ engine.colName(rule.range.startCI) }}{{ rule.range.startRI + 1 }}:{{ engine.colName(rule.range.endCI) }}{{ rule.range.endRI + 1 }}</span>
            <span class="cond-condition">{{ rule.condition }} {{ rule.value }}{{ rule.value2 ? ' ~ ' + rule.value2 : '' }}</span>
            <span class="cond-style-preview" :style="{ background: rule.style.bgColor, color: rule.style.color }">Aa</span>
            <button class="cond-delete" @click="engine.conditionalRules.value.splice(idx, 1)">X</button>
          </div>
          <div v-if="engine.conditionalRules.value.length === 0" class="no-rules">No rules defined</div>
          <div class="add-rule-form">
            <select v-model="newRule.condition">
              <option value="greater">Greater than</option>
              <option value="less">Less than</option>
              <option value="equal">Equal to</option>
              <option value="not_equal">Not equal</option>
              <option value="contains">Contains</option>
              <option value="between">Between</option>
            </select>
            <input v-model="newRule.value" placeholder="Value" class="rule-input" />
            <input v-if="newRule.condition === 'between'" v-model="newRule.value2" placeholder="Value 2" class="rule-input" />
            <label class="color-label">BG: <input type="color" v-model="newRule.bgColor" /></label>
            <label class="color-label">FG: <input type="color" v-model="newRule.fgColor" /></label>
            <button class="add-rule-btn" @click="addConditionalRule">Add Rule</button>
          </div>
        </div>
      </div>
    </div>

    <input type="file" ref="csvInputRef" accept=".csv" class="hidden-input" @change="handleCSVImport" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onBeforeUnmount, watch, nextTick } from 'vue'
import api from '../../utils/api'
import AiAssistantPanel from './AiAssistantPanel.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import { useSpreadsheetEngine } from '@/composables/useSpreadsheetEngine'
import type { CellFormat, NumberFormat } from '@/composables/useSpreadsheetEngine'

interface MenuItem {
  label: string
  shortcut?: string
  action?: () => void
  disabled?: boolean
}

const engine = useSpreadsheetEngine(5, 5)
const { saveDoc, loadDoc } = useDocumentPersistence('excel')

const editorRef = ref<HTMLElement | null>(null)
const tableContainerRef = ref<HTMLElement | null>(null)
const editingInputRef = ref<HTMLInputElement[]>([])
const csvInputRef = ref<HTMLInputElement | null>(null)

const formulaInput = ref('')
const editingCell = reactive({ ri: -1, ci: -1 })
const editValue = ref('')

const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')
const activeRibbonTab = ref('home')
const activeMenu = ref('')

const excelRibbonTabs = [
  { id: 'home', label: 'Home' },
  { id: 'data', label: 'Data' },
  { id: 'ai', label: 'AI' },
]

const excelMenus = computed(() => [
  {
    label: 'File',
    items: [
      { label: 'Save', shortcut: 'Ctrl+S', action: saveSpreadsheet },
      { label: 'Open', shortcut: 'Ctrl+O', action: openSpreadsheet },
      { label: 'Export CSV', action: doCSVExport },
      { label: 'Export XLSX', action: exportXlsx },
      { label: 'Import CSV', action: triggerCSVImport },
    ] as MenuItem[],
  },
  {
    label: 'Edit',
    items: [
      { label: 'Undo', shortcut: 'Ctrl+Z', action: () => engine.undo(), disabled: engine.undoStack.value.length === 0 },
      { label: 'Redo', shortcut: 'Ctrl+Y', action: () => engine.redo(), disabled: engine.redoStack.value.length === 0 },
    ] as MenuItem[],
  },
  {
    label: 'View',
    items: [
      { label: 'Freeze Header', action: toggleFreeze },
      { label: 'Conditional Formatting', action: () => { showConditionalDialog.value = true } },
    ] as MenuItem[],
  },
  {
    label: 'Insert',
    items: [
      { label: 'Insert Row', action: () => engine.addRow() },
      { label: 'Insert Column', action: () => engine.addColumn() },
    ] as MenuItem[],
  },
  {
    label: 'Data',
    items: [
      { label: 'Sort Ascending', action: () => engine.sortColumn(engine.activeCell.ci, true) },
      { label: 'Sort Descending', action: () => engine.sortColumn(engine.activeCell.ci, false) },
      { label: 'Filter', action: toggleFilterForCol },
    ] as MenuItem[],
  },
  {
    label: 'Tools',
    items: [
      { label: 'AI Assistant', action: () => { activeRibbonTab.value = 'ai' } },
    ] as MenuItem[],
  },
  {
    label: 'Help',
    items: [
      { label: 'About PolySpace Calc', disabled: true },
    ] as MenuItem[],
  },
])

function toggleMenu(label: string) {
  activeMenu.value = activeMenu.value === label ? '' : label
}

function openMenuOnHover(label: string) {
  if (activeMenu.value) {
    activeMenu.value = label
  }
}

async function exportXlsx() {
  try {
    const csvContent = engine.rows.value.map((row: any[]) => row.map((cell: any) => {
      const v = cell?.value ?? ''
      return typeof v === 'string' && (v.includes(',') || v.includes('"') || v.includes('\n')) ? `"${v.replace(/"/g, '""')}"` : String(v)
    }).join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const formData = new FormData()
    formData.append('file', blob, 'spreadsheet.csv')
    const res = await api.post('/documents/convert?output_format=xlsx', formData, { responseType: 'blob' })
    const xlsxBlob = new Blob([res.data])
    const url = URL.createObjectURL(xlsxBlob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'spreadsheet.xlsx'
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('XLSX export failed:', e)
    doCSVExport()
  }
}

const contextMenu = reactive({ visible: false, x: 0, y: 0, ri: -1, ci: -1 })
const findState = engine.findState
const filterDropdown = reactive({ visible: false, x: 0, y: 0, ci: 0, values: [] as string[], excluded: [] as string[] })
const showConditionalDialog = ref(false)

const newRule = reactive({
  condition: 'greater' as 'greater' | 'less' | 'equal' | 'not_equal' | 'contains' | 'between',
  value: '',
  value2: '',
  bgColor: '#4a1a1a',
  fgColor: 'var(--ws-danger)',
})

let resizeType: 'col' | 'row' | null = null
let resizeIndex = -1
let resizeStartPos = 0
let resizeStartSize = 0

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', {
      rows: engine.rows.value,
      colNames: engine.colNames.value,
      cellStyles: { ...engine.cellStyles },
      numberFormats: { ...engine.numberFormats },
      colWidths: engine.colWidths.value,
      rowHeights: engine.rowHeights.value,
      conditionalRules: engine.conditionalRules.value,
      frozenRows: engine.frozenRows.value,
      updatedAt: Date.now(),
    })
  }, 1500)
}

async function loadSavedData() {
  const data = await loadDoc('default')
  if (data) {
    if (data.rows) engine.rows.value = data.rows
    if (data.colNames) engine.colNames.value = data.colNames
    if (data.colWidths) engine.colWidths.value = data.colWidths
    if (data.rowHeights) engine.rowHeights.value = data.rowHeights
    if (data.cellStyles) Object.assign(engine.cellStyles, data.cellStyles)
    if (data.numberFormats) Object.assign(engine.numberFormats, data.numberFormats)
    if (data.conditionalRules) engine.conditionalRules.value = data.conditionalRules
    if (data.frozenRows !== undefined) engine.frozenRows.value = data.frozenRows
  }
}
loadSavedData()

watch([engine.rows, engine.colNames, engine.cellStyles, engine.numberFormats, engine.colWidths, engine.rowHeights], debouncedSave, { deep: true })

const currentFormat = computed<CellFormat>(() => {
  if (engine.activeCell.ri < 0) return {}
  return engine.getCellStyle(engine.activeCell.ri, engine.activeCell.ci)
})

const currentNumFormat = computed<NumberFormat>(() => {
  if (engine.activeCell.ri < 0) return { type: 'auto' }
  return engine.getNumberFormat(engine.activeCell.ri, engine.activeCell.ci)
})

const selectionStats = computed(() => engine.getSelectionStats())

const selectionSize = computed(() => {
  const s = engine.getNormalizedSelection()
  const rows = s.maxRI - s.minRI + 1
  const cols = s.maxCI - s.minCI + 1
  return `${rows}x${cols}`
})

function getCellStyleObj(ri: number, ci: number): Record<string, string> {
  const fmt = engine.getCellStyle(ri, ci)
  const condStyle = engine.evaluateConditionalRules(ri, ci)
  const merged = { ...fmt, ...condStyle }
  const style: Record<string, string> = {}
  if (merged.bold) style.fontWeight = '700'
  if (merged.italic) style.fontStyle = 'italic'
  if (merged.color) style.color = merged.color
  if (merged.bgColor) style.backgroundColor = merged.bgColor
  if (merged.align) style.textAlign = merged.align
  if (merged.fontSize) style.fontSize = merged.fontSize + 'px'
  const nf = engine.getNumberFormat(ri, ci)
  if (nf.type === 'number' || nf.type === 'currency') style.textAlign = 'right'
  return style
}

function isFindHighlight(ri: number, ci: number): boolean {
  return findState.currentIndex >= 0 &&
    findState.results[findState.currentIndex]?.ri === ri &&
    findState.results[findState.currentIndex]?.ci === ci
}

function isColSelected(ci: number): boolean {
  if (engine.selection.startRI < 0) return false
  const s = engine.getNormalizedSelection()
  return s.minCI <= ci && ci <= s.maxCI && s.minRI === 0 && s.maxRI === engine.rows.value.length - 1
}

function isRowSelected(ri: number): boolean {
  if (engine.selection.startRI < 0) return false
  const s = engine.getNormalizedSelection()
  return s.minRI <= ri && ri <= s.maxRI && s.minCI === 0 && s.maxCI === engine.colNames.value.length - 1
}

function onCellClick(ri: number, ci: number) {
  if (editingCell.ri >= 0) commitEdit()
  engine.setSelection(ri, ci)
  formulaInput.value = engine.getRawValue(ri, ci)
}

function onCellShiftClick(ri: number, ci: number) {
  engine.extendSelection(ri, ci)
}

let isSelecting = false

function onTableMouseDown(e: MouseEvent) {
  const target = (e.target as HTMLElement).closest('td')
  if (!target) return
  const ri = parseInt(target.getAttribute('data-ri') || '-1')
  const ci = parseInt(target.getAttribute('data-ci') || '-1')
  if (ri < 0 || ci < 0) return
  isSelecting = true
  if (!e.shiftKey) {
    if (editingCell.ri >= 0) commitEdit()
    engine.setSelection(ri, ci)
    formulaInput.value = engine.getRawValue(ri, ci)
  }
}

function onTableMouseMove(e: MouseEvent) {
  if (!isSelecting) return
  const target = (e.target as HTMLElement).closest('td')
  if (!target) return
  const ri = parseInt(target.getAttribute('data-ri') || '-1')
  const ci = parseInt(target.getAttribute('data-ci') || '-1')
  if (ri < 0 || ci < 0) return
  engine.extendSelection(ri, ci)
}

function onTableMouseUp() {
  isSelecting = false
}

function selectAll() {
  engine.setSelection(0, 0, engine.rows.value.length - 1, engine.colNames.value.length - 1)
}

function selectColumn(ci: number) {
  engine.setSelection(0, ci, engine.rows.value.length - 1, ci)
}

function selectRow(ri: number) {
  engine.setSelection(ri, 0, ri, engine.colNames.value.length - 1)
}

function startEdit(ri: number, ci: number) {
  editingCell.ri = ri
  editingCell.ci = ci
  editValue.value = engine.getRawValue(ri, ci)
  nextTick(() => {
    const input = editingInputRef.value?.[0] as HTMLInputElement | undefined
    input?.focus()
  })
}

function commitEdit() {
  if (editingCell.ri < 0) return
  engine.updateCell(editingCell.ri, editingCell.ci, editValue.value)
  if (engine.activeCell.ri === editingCell.ri && engine.activeCell.ci === editingCell.ci) {
    formulaInput.value = editValue.value
  }
  editingCell.ri = -1
  editingCell.ci = -1
}

function cancelEdit() {
  editingCell.ri = -1
  editingCell.ci = -1
}

function moveAndEdit(ri: number, ci: number, dir: string) {
  const pos = engine.moveCell(ri, ci, dir)
  formulaInput.value = engine.getRawValue(pos.ri, pos.ci)
}

function applyFormula() {
  if (engine.activeCell.ri >= 0 && engine.activeCell.ci >= 0) {
    engine.updateCell(engine.activeCell.ri, engine.activeCell.ci, formulaInput.value)
  }
}

function toggleBold() { engine.applyFormatToSelection({ bold: !currentFormat.value.bold }) }
function toggleItalic() { engine.applyFormatToSelection({ italic: !currentFormat.value.italic }) }
function setTextColor(color: string) { engine.applyFormatToSelection({ color }) }
function setBgColor(color: string) { engine.applyFormatToSelection({ bgColor: color }) }
function setAlign(align: 'left' | 'center' | 'right') { engine.applyFormatToSelection({ align }) }
function setNumFormat(type: string) { engine.applyNumberFormatToSelection({ type: type as NumberFormat['type'] }) }

function deleteSelectedRow() {
  if (engine.activeCell.ri >= 0) engine.deleteRow(engine.activeCell.ri)
}
function deleteSelectedCol() {
  if (engine.activeCell.ci >= 0) engine.deleteColumn(engine.activeCell.ci)
}

function showContextMenu(e: MouseEvent, ri: number, ci: number) {
  contextMenu.visible = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.ri = ri
  contextMenu.ci = ci
  if (ri >= 0 && ci >= 0) {
    engine.setSelection(ri, ci)
  }
}

function contextAction(action: string) {
  const ri = contextMenu.ri
  const ci = contextMenu.ci
  contextMenu.visible = false
  switch (action) {
    case 'cut': engine.cutSelection(); break
    case 'copy': engine.copySelection(); break
    case 'paste': engine.pasteAt(engine.activeCell.ri, engine.activeCell.ci); break
    case 'insertRowAbove': engine.addRow(ri >= 0 ? ri : engine.activeCell.ri); break
    case 'insertRowBelow': engine.addRow(ri >= 0 ? ri + 1 : engine.activeCell.ri + 1); break
    case 'insertColLeft': engine.addColumn(ci >= 0 ? ci : engine.activeCell.ci); break
    case 'insertColRight': engine.addColumn(ci >= 0 ? ci + 1 : engine.activeCell.ci + 1); break
    case 'deleteRow': if (ri >= 0 || engine.activeCell.ri >= 0) engine.deleteRow(ri >= 0 ? ri : engine.activeCell.ri); break
    case 'deleteCol': if (ci >= 0 || engine.activeCell.ci >= 0) engine.deleteColumn(ci >= 0 ? ci : engine.activeCell.ci); break
    case 'clearCells': engine.deleteSelection(); break
    case 'sortAsc': engine.sortColumn(ci >= 0 ? ci : engine.activeCell.ci, true); break
    case 'sortDesc': engine.sortColumn(ci >= 0 ? ci : engine.activeCell.ci, false); break
  }
}

function startColResize(ci: number, e: MouseEvent) {
  resizeType = 'col'
  resizeIndex = ci
  resizeStartPos = e.clientX
  resizeStartSize = engine.colWidths.value[ci]
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function startRowResize(ri: number, e: MouseEvent) {
  resizeType = 'row'
  resizeIndex = ri
  resizeStartPos = e.clientY
  resizeStartSize = engine.rowHeights.value[ri]
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', onResizeEnd)
}

function onResizeMove(e: MouseEvent) {
  if (resizeType === 'col') {
    const delta = e.clientX - resizeStartPos
    engine.colWidths.value[resizeIndex] = Math.max(40, resizeStartSize + delta)
  } else if (resizeType === 'row') {
    const delta = e.clientY - resizeStartPos
    engine.rowHeights.value[resizeIndex] = Math.max(20, resizeStartSize + delta)
  }
}

function onResizeEnd() {
  resizeType = null
  resizeIndex = -1
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
}

function toggleFilterForCol() {
  if (engine.activeCell.ci >= 0) {
    engine.toggleFilter(engine.activeCell.ci)
  }
}

function openFilterDropdown(ci: number, e: MouseEvent) {
  const values = engine.getUniqueColumnValues(ci)
  filterDropdown.visible = true
  filterDropdown.x = (e.target as HTMLElement).getBoundingClientRect().left
  filterDropdown.y = (e.target as HTMLElement).getBoundingClientRect().bottom
  filterDropdown.ci = ci
  filterDropdown.values = values
  filterDropdown.excluded = engine.filterState[ci]?.excludedValues || []
}

function toggleFilterValue(ci: number, val: string) {
  if (!engine.filterState[ci]) engine.filterState[ci] = { active: true, excludedValues: [] }
  const idx = engine.filterState[ci].excludedValues.indexOf(val)
  if (idx >= 0) engine.filterState[ci].excludedValues.splice(idx, 1)
  else engine.filterState[ci].excludedValues.push(val)
}

function selectAllFilterValues(ci: number) {
  if (engine.filterState[ci]) engine.filterState[ci].excludedValues = []
}

function clearFilter(ci: number) {
  delete engine.filterState[ci]
  filterDropdown.visible = false
}

function toggleFreeze() {
  engine.frozenRows.value = engine.frozenRows.value > 0 ? 0 : 1
}

function onTableScroll() {
  filterDropdown.visible = false
}

function addConditionalRule() {
  if (!newRule.value) return
  const s = engine.getNormalizedSelection()
  engine.conditionalRules.value.push({
    id: Date.now().toString(),
    range: { startRI: s.minRI, startCI: s.minCI, endRI: s.maxRI, endCI: s.maxCI },
    condition: newRule.condition,
    value: newRule.value,
    value2: newRule.condition === 'between' ? newRule.value2 : undefined,
    style: { bgColor: newRule.bgColor, color: newRule.fgColor, bold: true },
  })
  newRule.value = ''
  newRule.value2 = ''
}

function triggerCSVImport() {
  csvInputRef.value?.click()
}

function handleCSVImport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    engine.importCSV(reader.result as string)
  }
  reader.readAsText(file)
  ;(e.target as HTMLInputElement).value = ''
}

function doCSVExport() {
  const csv = engine.exportCSV()
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'spreadsheet.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function saveSpreadsheet() {
  try {
    const content = JSON.stringify({
      rows: engine.rows.value,
      colNames: engine.colNames.value,
      cellStyles: { ...engine.cellStyles },
      numberFormats: { ...engine.numberFormats },
      colWidths: engine.colWidths.value,
      rowHeights: engine.rowHeights.value,
      conditionalRules: engine.conditionalRules.value,
      frozenRows: engine.frozenRows.value,
    })
    await api.post('/workspace/documents', {
      title: 'Spreadsheet',
      doc_type: 'spreadsheet',
      content,
      metadata: { rows: engine.rows.value.length, cols: engine.colNames.value.length },
    })
    await api.post('/files/write', {
      path: 'spreadsheet.json',
      content,
      subdir: 'spreadsheets',
    })
  } catch (e) {
    console.error('Failed to save spreadsheet:', e)
  }
}

async function openSpreadsheet() {
  try {
    const res = await api.get('/workspace/documents', { params: { doc_type: 'spreadsheet' } })
    const docs = res.data?.documents || res.data || []
    if (!docs.length) return
    const latest = docs[0]
    if (latest?.content) {
      const data = typeof latest.content === 'string' ? JSON.parse(latest.content) : latest.content
      if (data.rows) engine.rows.value = data.rows
      if (data.colNames) engine.colNames.value = data.colNames
      if (data.colWidths) engine.colWidths.value = data.colWidths
      if (data.rowHeights) engine.rowHeights.value = data.rowHeights
      if (data.cellStyles) Object.assign(engine.cellStyles, data.cellStyles)
      if (data.numberFormats) Object.assign(engine.numberFormats, data.numberFormats)
      if (data.conditionalRules) engine.conditionalRules.value = data.conditionalRules
      if (data.frozenRows !== undefined) engine.frozenRows.value = data.frozenRows
    }
  } catch (e) {
    console.error('Failed to open spreadsheet:', e)
  }
}

function doFind() {
  engine.findCells(findState.query)
}

function handleGlobalKeydown(e: KeyboardEvent) {
  if (editingCell.ri >= 0) return

  if (e.ctrlKey || e.metaKey) {
    switch (e.key.toLowerCase()) {
      case 'z':
        e.preventDefault()
        if (e.shiftKey) engine.redo()
        else engine.undo()
        return
      case 'y':
        e.preventDefault()
        engine.redo()
        return
      case 'c':
        e.preventDefault()
        engine.copySelection()
        return
      case 'x':
        e.preventDefault()
        engine.cutSelection()
        return
      case 'v':
        e.preventDefault()
        engine.pasteAt(engine.activeCell.ri, engine.activeCell.ci)
        return
      case 'b':
        e.preventDefault()
        toggleBold()
        return
      case 'i':
        e.preventDefault()
        toggleItalic()
        return
      case 'f':
        e.preventDefault()
        findState.isOpen = !findState.isOpen
        return
      case 'h':
        e.preventDefault()
        findState.isOpen = true
        return
      case 'a':
        e.preventDefault()
        selectAll()
        return
    }
  }

  if (e.key === 'Delete' || e.key === 'Backspace') {
    if (engine.selection.startRI >= 0) {
      e.preventDefault()
      engine.deleteSelection()
    }
    return
  }

  if (e.key === 'F2' && engine.activeCell.ri >= 0) {
    e.preventDefault()
    startEdit(engine.activeCell.ri, engine.activeCell.ci)
    return
  }

  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    const dir = e.key.replace('Arrow', '').toLowerCase()
    const pos = engine.moveCell(engine.activeCell.ri, engine.activeCell.ci, dir)
    formulaInput.value = engine.getRawValue(pos.ri, pos.ci)
    return
  }

  if (e.key === 'Tab') {
    e.preventDefault()
    const dir = e.shiftKey ? 'left' : 'right'
    const pos = engine.moveCell(engine.activeCell.ri, engine.activeCell.ci, dir)
    formulaInput.value = engine.getRawValue(pos.ri, pos.ci)
    return
  }

  if (e.key === 'Enter') {
    e.preventDefault()
    if (engine.activeCell.ri >= 0) {
      const pos = engine.moveCell(engine.activeCell.ri, engine.activeCell.ci, 'down')
      formulaInput.value = engine.getRawValue(pos.ri, pos.ci)
    }
    return
  }

  if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey && engine.activeCell.ri >= 0) {
    startEdit(engine.activeCell.ri, engine.activeCell.ci)
    editValue.value = e.key
    nextTick(() => {
      const input = editingInputRef.value?.[0] as HTMLInputElement | undefined
      if (input) {
        input.selectionStart = 1
        input.selectionEnd = 1
      }
    })
  }
}

async function aiAction(action: string) {
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  aiCurrentAction.value = action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  try {
    const res = await api.post('/ai/workspace/excel/assist', {
      action,
      params: {
        data: engine.rows.value,
        columns: engine.colNames.value,
        selected_cell: engine.activeCell.ri >= 0 ? `${engine.colNames.value[engine.activeCell.ci]}${engine.activeCell.ri + 1}` : null,
      },
    })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'AI processing failed.' }
  } finally {
    aiLoading.value = false
  }
}

function applyAIResult() {
  const data = aiResult.value
  if (!data) return
  if (data.formulas?.length === 1 && engine.activeCell.ri >= 0) {
    engine.updateCell(engine.activeCell.ri, engine.activeCell.ci, data.formulas[0].formula)
  }
  aiPanelOpen.value = false
}

function closeOverlays(e: MouseEvent) {
  if (contextMenu.visible && !(e.target as HTMLElement).closest('.context-menu')) {
    contextMenu.visible = false
  }
  if (filterDropdown.visible && !(e.target as HTMLElement).closest('.filter-dropdown')) {
    filterDropdown.visible = false
  }
}

document.addEventListener('click', closeOverlays)
onBeforeUnmount(() => {
  document.removeEventListener('click', closeOverlays)
  if (saveTimer) clearTimeout(saveTimer)
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', onResizeEnd)
})
</script>

<style scoped>
.excel-editor { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); color: var(--text-primary); outline: none; position: relative; }
.lo-menubar { display: flex; align-items: center; padding: 2px 8px; background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); font-size: 13px; user-select: none; }
.menu-item { position: relative; padding: 4px 10px; color: var(--text-color); cursor: pointer; border-radius: 3px; }
.menu-item:hover { background: var(--border-color); }
.menu-dropdown { position: absolute; top: 100%; left: 0; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; box-shadow: 0 4px 16px rgba(0,0,0,0.12); min-width: 220px; z-index: 200; padding: 4px 0; }
.menu-dropdown-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 16px; cursor: pointer; color: var(--text-color); font-size: 13px; }
.menu-dropdown-item:hover:not(.disabled) { background: var(--primary-color); color: white; }
.menu-dropdown-item.disabled { opacity: 0.4; cursor: default; }
.menu-item-shortcut { font-size: 11px; color: var(--text-tertiary); margin-left: 24px; }
.menu-dropdown-item:hover:not(.disabled) .menu-item-shortcut { color: rgba(255,255,255,0.7); }
.lo-ribbon { background: var(--bg-secondary); border-bottom: 1px solid var(--border-color); }
.ribbon-tabs { display: flex; border-bottom: 1px solid var(--border-color); padding: 0 8px; }
.ribbon-tab { padding: 6px 16px; border: none; background: none; color: var(--text-secondary); font-size: 12px; font-weight: 500; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s; }
.ribbon-tab:hover { color: var(--text-color); background: var(--border-color); }
.ribbon-tab.active { color: var(--primary-color); border-bottom-color: var(--primary-color); }
.ribbon-content { display: flex; align-items: stretch; padding: 6px 12px; min-height: 72px; gap: 2px; }
.ribbon-group { display: flex; flex-direction: column; align-items: center; }
.ribbon-group-inner { display: flex; align-items: center; gap: 1px; flex: 1; padding: 2px 4px; }
.ribbon-group-label { font-size: 10px; color: var(--text-tertiary); text-align: center; padding: 2px 0 0; white-space: nowrap; }
.ribbon-separator { width: 1px; background: var(--border-color); margin: 4px 6px; align-self: stretch; }
.lo-select { padding: 3px 6px; border: 1px solid var(--border-color); border-radius: 3px; background: var(--input-bg); color: var(--text-color); font-size: 12px; cursor: pointer; outline: none; max-width: 100px; }
.lo-select:focus { border-color: var(--primary-color); }
.lo-btn { display: flex; align-items: center; justify-content: center; gap: 2px; padding: 4px 5px; border-radius: 3px; color: var(--text-secondary); cursor: pointer; background: none; border: none; transition: all 0.12s; position: relative; }
.lo-btn:hover:not(:disabled) { background: var(--border-color); color: var(--text-color); }
.lo-btn.active { background: var(--primary-light); color: var(--primary-color); }
.lo-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.lo-btn-lg { flex-direction: column; padding: 6px 10px; gap: 2px; min-width: 48px; }
.lo-btn-lg span { font-size: 10px; white-space: nowrap; }
.hidden-color-input { position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }
.ai-btn { color: var(--primary-color); }
.ai-btn:hover:not(:disabled) { background: var(--primary-light); color: var(--primary-color); }
.ai-tools { gap: 4px; }
.formula-bar { display: flex; align-items: center; padding: 4px 12px; border-bottom: 1px solid var(--border-color); background: var(--bg-secondary); gap: 8px; }
.fx-label { font-weight: 700; color: var(--ws-accent); font-style: italic; font-size: 13px; flex-shrink: 0; }
.formula-input { flex: 1; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 4px; padding: 4px 8px; color: var(--text-primary); font-size: 13px; outline: none; font-family: monospace; }
.formula-input:focus { border-color: var(--ws-accent); }
.excel-content { flex: 1; display: flex; overflow: hidden; position: relative; }
.table-container { flex: 1; overflow: auto; padding: 0; }
.spreadsheet { border-collapse: collapse; width: max-content; }
.corner-cell { padding: 6px; background: var(--bg-secondary); border: 1px solid var(--border-color); min-width: 40px; cursor: pointer; user-select: none; }
.corner-cell:hover { background: var(--ws-accent-light); }
.col-header { padding: 0; background: var(--bg-secondary); border: 1px solid var(--border-color); font-size: 12px; font-weight: 600; color: var(--ws-accent); text-align: center; cursor: pointer; user-select: none; position: relative; height: 28px; }
.col-header .col-name { display: inline-block; padding: 6px 16px 6px 8px; }
.col-header.selected { background: var(--ws-accent-light); }
.col-header.filtered { color: var(--ws-warning); }
.col-header:hover { background: var(--ws-accent-light); }
.col-resize { position: absolute; right: 0; top: 0; width: 4px; height: 100%; cursor: col-resize; z-index: 2; }
.col-resize:hover { background: var(--ws-accent); }
.filter-indicator { position: absolute; top: 2px; right: 4px; background: none; border: none; color: var(--ws-warning); cursor: pointer; padding: 0; display: flex; }
.row-header { padding: 0; background: var(--bg-secondary); border: 1px solid var(--border-color); font-size: 11px; color: var(--text-tertiary); text-align: center; min-width: 40px; user-select: none; position: relative; }
.row-header .row-num { display: inline-block; padding: 6px 8px; }
.row-header.selected { background: var(--ws-accent-light); color: var(--ws-accent-soft); }
.row-resize { position: absolute; bottom: 0; left: 0; width: 100%; height: 3px; cursor: row-resize; z-index: 2; }
.row-resize:hover { background: var(--ws-accent); }
.cell { border: 1px solid var(--border-color); padding: 0; position: relative; min-width: 40px; }
.cell.selected { background: rgba(124, 111, 247, 0.1); }
.cell.active-cell { outline: 2px solid var(--ws-accent); outline-offset: -2px; z-index: 1; }
.cell.formula { background: var(--bg-secondary); }
.cell.find-highlight { outline: 2px solid var(--ws-warning); outline-offset: -2px; z-index: 1; }
.cell-input { width: 100%; padding: 4px 6px; background: transparent; border: none; color: var(--text-primary); font-size: 13px; outline: none; font-family: inherit; }
.cell-input.editing { background: var(--bg-secondary); }
.cell.formula .cell-input { color: var(--ws-success); font-family: monospace; }
.cell-display { display: block; padding: 4px 6px; font-size: 13px; min-height: 18px; cursor: cell; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.excel-footer { display: flex; justify-content: space-between; align-items: center; padding: 4px 16px; border-top: 1px solid var(--border-color); background: var(--bg-secondary); font-size: 11px; color: var(--text-tertiary); gap: 16px; }
.footer-left, .footer-center, .footer-right { display: flex; gap: 12px; align-items: center; }
.cell-ref { color: var(--ws-accent); font-weight: 600; }
.range-info { color: var(--ws-accent-soft); }
.selection-stats { color: var(--ws-success); }
.stats { color: var(--text-tertiary); }
.context-menu { position: fixed; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 6px; padding: 4px 0; min-width: 180px; z-index: 1000; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.context-menu button { display: block; width: 100%; text-align: left; padding: 6px 16px; background: none; border: none; color: var(--text-primary); font-size: 12px; cursor: pointer; }
.context-menu button:hover { background: var(--border-color); color: var(--ws-accent-soft); }
.context-divider { height: 1px; background: var(--border-color); margin: 4px 0; }
.find-dialog { position: absolute; top: 60px; right: 16px; width: 320px; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; z-index: 100; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.find-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid var(--border-color); font-size: 13px; font-weight: 600; color: var(--ws-accent-soft); }
.find-body { padding: 10px 12px; display: flex; flex-direction: column; gap: 8px; }
.find-input { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 4px; padding: 5px 8px; color: var(--text-primary); font-size: 12px; outline: none; }
.find-input:focus { border-color: var(--ws-accent); }
.find-options { font-size: 11px; color: var(--text-tertiary); }
.find-options label { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.find-options input[type="checkbox"] { accent-color: var(--ws-accent); }
.find-actions { display: flex; gap: 4px; }
.find-actions button { flex: 1; padding: 4px 8px; background: var(--border-color); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-primary); font-size: 11px; cursor: pointer; }
.find-actions button:hover:not(:disabled) { background: var(--border-color); }
.find-actions button:disabled { opacity: 0.4; cursor: not-allowed; }
.find-count { font-size: 11px; color: var(--text-tertiary); }
.filter-dropdown { position: fixed; background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 8px; z-index: 100; min-width: 200px; max-height: 300px; box-shadow: 0 4px 16px rgba(0,0,0,0.4); display: flex; flex-direction: column; }
.filter-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid var(--border-color); font-size: 12px; font-weight: 600; color: var(--ws-accent-soft); }
.filter-list { flex: 1; overflow-y: auto; padding: 6px 8px; max-height: 200px; }
.filter-item { display: flex; align-items: center; gap: 6px; padding: 3px 4px; font-size: 12px; color: var(--text-secondary); cursor: pointer; }
.filter-item:hover { background: var(--border-color); border-radius: 3px; }
.filter-item input { accent-color: var(--ws-accent); }
.filter-actions { display: flex; gap: 4px; padding: 6px 8px; border-top: 1px solid var(--border-color); }
.filter-actions button { flex: 1; padding: 4px 8px; background: var(--border-color); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-primary); font-size: 11px; cursor: pointer; }
.filter-actions button:hover { background: var(--border-color); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 200; }
.modal-content { background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; width: 480px; max-height: 80vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--border-color); }
.modal-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; display: flex; }
.close-btn:hover { color: #fff; }
.modal-body { padding: 12px 16px; }
.cond-rule { display: flex; align-items: center; gap: 8px; padding: 6px 8px; background: var(--bg-primary); border-radius: 4px; margin-bottom: 4px; font-size: 12px; }
.cond-range { color: var(--ws-accent); font-weight: 600; min-width: 60px; }
.cond-condition { flex: 1; color: var(--text-secondary); }
.cond-style-preview { padding: 2px 8px; border-radius: 3px; font-size: 11px; }
.cond-delete { background: none; border: none; color: var(--ws-danger); cursor: pointer; font-size: 12px; }
.no-rules { color: var(--text-tertiary); font-size: 12px; text-align: center; padding: 16px; }
.add-rule-form { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; align-items: center; }
.add-rule-form select, .add-rule-form .rule-input { background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-primary); font-size: 11px; padding: 4px 6px; outline: none; }
.add-rule-form .rule-input { width: 70px; }
.add-rule-form select:focus, .add-rule-form .rule-input:focus { border-color: var(--ws-accent); }
.color-label { font-size: 11px; color: var(--text-tertiary); display: flex; align-items: center; gap: 4px; }
.color-label input[type="color"] { width: 24px; height: 20px; border: none; background: none; cursor: pointer; }
.add-rule-btn { padding: 4px 12px; background: var(--ws-accent); color: #fff; border: none; border-radius: 4px; font-size: 11px; cursor: pointer; }
.add-rule-btn:hover { background: var(--ws-accent-hover); }
.hidden-input { display: none; }
</style>
