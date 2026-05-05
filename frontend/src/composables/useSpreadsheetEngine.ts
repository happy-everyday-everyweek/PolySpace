import { ref, reactive } from 'vue'

export interface CellFormat {
  bold?: boolean
  italic?: boolean
  color?: string
  bgColor?: string
  align?: 'left' | 'center' | 'right'
  fontSize?: number
}

export interface NumberFormat {
  type: 'auto' | 'number' | 'currency' | 'percent' | 'date'
  precision?: number
  currencySymbol?: string
}

export interface ConditionalRule {
  id: string
  range: { startRI: number; startCI: number; endRI: number; endCI: number }
  condition: 'greater' | 'less' | 'equal' | 'not_equal' | 'contains' | 'between'
  value: string
  value2?: string
  style: { bgColor?: string; color?: string; bold?: boolean }
}

export interface SelectionRange {
  startRI: number
  startCI: number
  endRI: number
  endCI: number
}

export interface HistorySnapshot {
  rows: string[][]
  styles: Record<string, CellFormat>
  numberFormats: Record<string, NumberFormat>
}

function cellKey(ri: number, ci: number): string {
  return `${ri}_${ci}`
}

function colName(ci: number): string {
  let name = ''
  let n = ci
  while (n >= 0) {
    name = String.fromCharCode(65 + (n % 26)) + name
    n = Math.floor(n / 26) - 1
  }
  return name
}

function parseCellRef(ref: string): { ri: number; ci: number } | null {
  const match = ref.match(/^([A-Z]+)(\d+)$/)
  if (!match) return null
  const colStr = match[1]
  const row = parseInt(match[2]) - 1
  let ci = 0
  for (let i = 0; i < colStr.length; i++) {
    ci = ci * 26 + (colStr.charCodeAt(i) - 64)
  }
  ci -= 1
  return { ri: row, ci }
}

function cellRefStr(ri: number, ci: number): string {
  return `${colName(ci)}${ri + 1}`
}

function tokenize(expr: string): (string | number)[] {
  const tokens: (string | number)[] = []
  let i = 0
  while (i < expr.length) {
    if (expr[i] === ' ') { i++; continue }
    if ('+-*/^()=<>!'.includes(expr[i])) {
      if (expr[i] === '<' && expr[i + 1] === '=') { tokens.push('<='); i += 2; continue }
      if (expr[i] === '>' && expr[i + 1] === '=') { tokens.push('>='); i += 2; continue }
      if (expr[i] === '!' && expr[i + 1] === '=') { tokens.push('!='); i += 2; continue }
      tokens.push(expr[i]); i++; continue
    }
    if (expr[i] === '"') {
      let s = ''
      i++
      while (i < expr.length && expr[i] !== '"') { s += expr[i]; i++ }
      i++
      tokens.push(`"${s}"`)
      continue
    }
    if (/[0-9.]/.test(expr[i])) {
      let num = ''
      while (i < expr.length && /[0-9.]/.test(expr[i])) { num += expr[i]; i++ }
      tokens.push(parseFloat(num))
      continue
    }
    if (/[A-Z_]/i.test(expr[i])) {
      let name = ''
      while (i < expr.length && /[A-Z0-9_]/i.test(expr[i])) { name += expr[i]; i++ }
      tokens.push(name.toUpperCase())
      continue
    }
    i++
  }
  return tokens
}

function evaluateExpression(
  tokens: (string | number)[],
  getCellValue: (ri: number, ci: number) => number,
  _rows: string[][]
): number {
  let pos = 0

  function parseComparison(): number {
    let left = parseAddSub()
    while (pos < tokens.length && ['<', '>', '<=', '>=', '=', '!='].includes(tokens[pos] as string)) {
      const op = tokens[pos] as string
      pos++
      const right = parseAddSub()
      switch (op) {
        case '<': left = left < right ? 1 : 0; break
        case '>': left = left > right ? 1 : 0; break
        case '<=': left = left <= right ? 1 : 0; break
        case '>=': left = left >= right ? 1 : 0; break
        case '=': left = left === right ? 1 : 0; break
        case '!=': left = left !== right ? 1 : 0; break
      }
    }
    return left
  }

  function parseAddSub(): number {
    let left = parseMulDiv()
    while (pos < tokens.length && (tokens[pos] === '+' || tokens[pos] === '-')) {
      const op = tokens[pos] as string
      pos++
      const right = parseMulDiv()
      left = op === '+' ? left + right : left - right
    }
    return left
  }

  function parseMulDiv(): number {
    let left = parsePower()
    while (pos < tokens.length && (tokens[pos] === '*' || tokens[pos] === '/')) {
      const op = tokens[pos] as string
      pos++
      const right = parsePower()
      left = op === '*' ? left * right : (right !== 0 ? left / right : 0)
    }
    return left
  }

  function parsePower(): number {
    let left = parseUnary()
    if (pos < tokens.length && tokens[pos] === '^') {
      pos++
      const right = parsePower()
      left = Math.pow(left, right)
    }
    return left
  }

  function parseUnary(): number {
    if (tokens[pos] === '-') { pos++; return -parsePrimary() }
    if (tokens[pos] === '+') { pos++; return parsePrimary() }
    return parsePrimary()
  }

  function parsePrimary(): number {
    const token = tokens[pos]
    if (token === '(') {
      pos++
      const val = parseComparison()
      if (tokens[pos] === ')') pos++
      return val
    }
    if (typeof token === 'number') { pos++; return token }
    if (typeof token === 'string' && token.startsWith('"')) {
      pos++
      return 0
    }
    if (typeof token === 'string') {
      const funcName = token
      pos++
      if (tokens[pos] === '(') {
        pos++
        const args: number[] = []
        while (tokens[pos] !== ')' && pos < tokens.length) {
          if (tokens[pos] === ',') { pos++; continue }
          args.push(parseComparison())
        }
        if (tokens[pos] === ')') pos++
        return evaluateFunction(funcName, args)
      }
      const ref = parseCellRef(funcName)
      if (ref) return getCellValue(ref.ri, ref.ci)
      pos++
      return 0
    }
    pos++
    return 0
  }

  return parseComparison()
}

function evaluateFunction(name: string, args: number[]): number {
  switch (name) {
    case 'ABS': return Math.abs(args[0] || 0)
    case 'ROUND': return parseFloat((args[0] || 0).toFixed(args[1] || 0))
    case 'INT': return Math.floor(args[0] || 0)
    case 'MOD': return args[1] ? args[0] % args[1] : 0
    case 'POWER': return Math.pow(args[0] || 0, args[1] || 0)
    case 'SQRT': return Math.sqrt(args[0] || 0)
    case 'LOG': return Math.log(args[0] || 1)
    case 'LOG10': return Math.log10(args[0] || 1)
    case 'EXP': return Math.exp(args[0] || 0)
    case 'MAX': return Math.max(...args)
    case 'MIN': return Math.min(...args)
    case 'SUM': return args.reduce((a, b) => a + b, 0)
    case 'AVG':
    case 'AVERAGE': return args.length ? args.reduce((a, b) => a + b, 0) / args.length : 0
    case 'COUNT': return args.length
    case 'MEDIAN': {
      const sorted = [...args].sort((a, b) => a - b)
      const mid = Math.floor(sorted.length / 2)
      return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
    }
    case 'STDEV': {
      if (args.length < 2) return 0
      const mean = args.reduce((a, b) => a + b, 0) / args.length
      const variance = args.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / (args.length - 1)
      return Math.sqrt(variance)
    }
    case 'IF': return args[0] ? args[1] : (args.length > 2 ? args[2] : 0)
    case 'AND': return args.every(a => a) ? 1 : 0
    case 'OR': return args.some(a => a) ? 1 : 0
    case 'NOT': return args[0] ? 0 : 1
    case 'LEN': return args[0]?.toString().length || 0
    default: return 0
  }
}

export function useSpreadsheetEngine(initialRows = 5, initialCols = 5) {
  const rows = ref<string[][]>(
    Array.from({ length: initialRows }, () => new Array(initialCols).fill(''))
  )
  const colNames = ref<string[]>(
    Array.from({ length: initialCols }, (_, i) => colName(i))
  )
  const cellStyles = reactive<Record<string, CellFormat>>({})
  const numberFormats = reactive<Record<string, NumberFormat>>({})
  const conditionalRules = ref<ConditionalRule[]>([])

  const colWidths = ref<number[]>(Array(initialCols).fill(100))
  const rowHeights = ref<number[]>(Array(initialRows).fill(28))

  const selection = reactive<SelectionRange>({
    startRI: -1, startCI: -1, endRI: -1, endCI: -1
  })
  const activeCell = reactive({ ri: -1, ci: -1 })

  const undoStack = ref<HistorySnapshot[]>([])
  const redoStack = ref<HistorySnapshot[]>([])
  const MAX_HISTORY = 50

  const clipboard = reactive<{
    data: string[][] | null
    isCut: boolean
    sourceRI: number
    sourceCI: number
  }>({ data: null, isCut: false, sourceRI: -1, sourceCI: -1 })

  const findState = reactive({
    query: '',
    replaceWith: '',
    caseSensitive: false,
    results: [] as { ri: number; ci: number }[],
    currentIndex: -1,
    isOpen: false,
  })

  const filterState = reactive<Record<number, { active: boolean; excludedValues: string[] }>>({})

  const frozenRows = ref(1)
  const evaluatingCells = new Set<string>()

  function getCellStyle(ri: number, ci: number): CellFormat {
    return cellStyles[cellKey(ri, ci)] || {}
  }

  function setCellStyle(ri: number, ci: number, style: Partial<CellFormat>) {
    const key = cellKey(ri, ci)
    cellStyles[key] = { ...cellStyles[key] || {}, ...style }
  }

  function getNumberFormat(ri: number, ci: number): NumberFormat {
    return numberFormats[cellKey(ri, ci)] || { type: 'auto' }
  }

  function setNumberFormat(ri: number, ci: number, fmt: Partial<NumberFormat>) {
    const key = cellKey(ri, ci)
    numberFormats[key] = { ...numberFormats[key] || { type: 'auto' }, ...fmt }
  }

  function takeSnapshot(): HistorySnapshot {
    return {
      rows: rows.value.map(r => [...r]),
      styles: { ...cellStyles },
      numberFormats: { ...numberFormats },
    }
  }

  function pushUndo() {
    undoStack.value.push(takeSnapshot())
    if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift()
    redoStack.value = []
  }

  function undo() {
    if (undoStack.value.length === 0) return
    redoStack.value.push(takeSnapshot())
    const snapshot = undoStack.value.pop()!
    rows.value = snapshot.rows
    Object.keys(cellStyles).forEach(k => delete cellStyles[k])
    Object.assign(cellStyles, snapshot.styles)
    Object.keys(numberFormats).forEach(k => delete numberFormats[k])
    Object.assign(numberFormats, snapshot.numberFormats)
  }

  function redo() {
    if (redoStack.value.length === 0) return
    undoStack.value.push(takeSnapshot())
    const snapshot = redoStack.value.pop()!
    rows.value = snapshot.rows
    Object.keys(cellStyles).forEach(k => delete cellStyles[k])
    Object.assign(cellStyles, snapshot.styles)
    Object.keys(numberFormats).forEach(k => delete numberFormats[k])
    Object.assign(numberFormats, snapshot.numberFormats)
  }

  function getRawValue(ri: number, ci: number): string {
    return rows.value[ri]?.[ci] || ''
  }

  function resolveCellValue(ri: number, ci: number): number {
    const key = cellKey(ri, ci)
    if (evaluatingCells.has(key)) return 0
    const raw = getRawValue(ri, ci)
    if (!raw) return 0
    if (raw.startsWith('=')) {
      evaluatingCells.add(key)
      try {
        const result = evaluateFormula(raw)
        const num = parseFloat(result)
        return isNaN(num) ? 0 : num
      } finally {
        evaluatingCells.delete(key)
      }
    }
    const num = parseFloat(raw)
    return isNaN(num) ? 0 : num
  }

  function evaluateFormula(formula: string): string {
    try {
      const expr = formula.substring(1).trim()
      const expanded = expandRanges(expr)
      const tokens = tokenize(expanded)
      const result = evaluateExpression(tokens, resolveCellValue, rows.value)
      if (typeof result === 'number' && !isFinite(result)) return '#ERROR'
      return typeof result === 'number' ? formatNumberResult(result) : String(result)
    } catch {
      return '#ERROR'
    }
  }

  function expandRanges(expr: string): string {
    return expr.replace(/([A-Z]+\d+):([A-Z]+\d+)/g, (_, start, end) => {
      const s = parseCellRef(start)
      const e = parseCellRef(end)
      if (!s || !e) return '0'
      const refs: string[] = []
      for (let ri = Math.min(s.ri, e.ri); ri <= Math.max(s.ri, e.ri); ri++) {
        for (let ci = Math.min(s.ci, e.ci); ci <= Math.max(s.ci, e.ci); ci++) {
          refs.push(cellRefStr(ri, ci))
        }
      }
      return refs.join(',')
    })
  }

  function formatNumberResult(n: number): string {
    if (Number.isInteger(n)) return n.toString()
    const rounded = parseFloat(n.toFixed(8))
    return rounded.toString()
  }

  function getDisplayValue(ri: number, ci: number): string {
    const raw = getRawValue(ri, ci)
    if (!raw) return ''
    if (raw.startsWith('=')) return evaluateFormula(raw)
    const fmt = getNumberFormat(ri, ci)
    return applyNumberFormat(raw, fmt)
  }

  function applyNumberFormat(value: string, fmt: NumberFormat): string {
    if (fmt.type === 'auto' || value === '') return value
    const num = parseFloat(value)
    if (isNaN(num)) return value
    switch (fmt.type) {
      case 'number':
        return num.toFixed(fmt.precision ?? 2)
      case 'currency':
        return `${fmt.currencySymbol || '¥'}${num.toFixed(fmt.precision ?? 2)}`
      case 'percent':
        return `${(num * 100).toFixed(fmt.precision ?? 1)}%`
      case 'date': {
        const d = new Date(num > 1e12 ? num : num * 86400000)
        if (isNaN(d.getTime())) return value
        return d.toLocaleDateString()
      }
      default:
        return value
    }
  }

  function updateCell(ri: number, ci: number, value: string) {
    if (!rows.value[ri]) return
    pushUndo()
    rows.value[ri][ci] = value
  }

  function updateCellSilent(ri: number, ci: number, value: string) {
    if (!rows.value[ri]) return
    rows.value[ri][ci] = value
  }

  function addRow(atIndex?: number) {
    pushUndo()
    const newRow = new Array(colNames.value.length).fill('')
    if (atIndex !== undefined) {
      rows.value.splice(atIndex, 0, newRow)
      rowHeights.value.splice(atIndex, 0, 28)
    } else {
      rows.value.push(newRow)
      rowHeights.value.push(28)
    }
  }

  function addColumn(atIndex?: number) {
    pushUndo()
    const newColName = colName(colNames.value.length)
    colWidths.value.push(100)
    rows.value.forEach(row => row.push(''))
    if (atIndex !== undefined && atIndex < colNames.value.length) {
      colNames.value.push(newColName)
      colWidths.value.splice(colNames.value.length - 1, 1)
      colWidths.value.splice(atIndex, 0, 100)
      for (const row of rows.value) {
        const val = row.pop()
        row.splice(atIndex, 0, val || '')
      }
      colNames.value.splice(colNames.value.length - 1, 1)
      colNames.value.splice(atIndex, 0, newColName)
    } else {
      colNames.value.push(newColName)
    }
  }

  function deleteRow(ri: number) {
    if (rows.value.length <= 1) return
    pushUndo()
    rows.value.splice(ri, 1)
    rowHeights.value.splice(ri, 1)
  }

  function deleteColumn(ci: number) {
    if (colNames.value.length <= 1) return
    pushUndo()
    colNames.value.splice(ci, 1)
    colWidths.value.splice(ci, 1)
    rows.value.forEach(row => row.splice(ci, 1))
  }

  function setSelection(startRI: number, startCI: number, endRI?: number, endCI?: number) {
    selection.startRI = startRI
    selection.startCI = startCI
    selection.endRI = endRI ?? startRI
    selection.endCI = endCI ?? startCI
    activeCell.ri = startRI
    activeCell.ci = startCI
  }

  function extendSelection(ri: number, ci: number) {
    selection.endRI = ri
    selection.endCI = ci
  }

  function getNormalizedSelection(): { minRI: number; minCI: number; maxRI: number; maxCI: number } {
    return {
      minRI: Math.min(selection.startRI, selection.endRI),
      minCI: Math.min(selection.startCI, selection.endCI),
      maxRI: Math.max(selection.startRI, selection.endRI),
      maxCI: Math.max(selection.startCI, selection.endCI),
    }
  }

  function isCellSelected(ri: number, ci: number): boolean {
    if (selection.startRI < 0) return false
    const s = getNormalizedSelection()
    return ri >= s.minRI && ri <= s.maxRI && ci >= s.minCI && ci <= s.maxCI
  }

  function isSelectedRange(): boolean {
    return selection.startRI !== selection.endRI || selection.startCI !== selection.endCI
  }

  function copySelection() {
    const s = getNormalizedSelection()
    const data: string[][] = []
    for (let ri = s.minRI; ri <= s.maxRI; ri++) {
      const row: string[] = []
      for (let ci = s.minCI; ci <= s.maxCI; ci++) {
        row.push(getRawValue(ri, ci))
      }
      data.push(row)
    }
    clipboard.data = data
    clipboard.isCut = false
    clipboard.sourceRI = s.minRI
    clipboard.sourceCI = s.minCI
  }

  function cutSelection() {
    copySelection()
    clipboard.isCut = true
  }

  function pasteAt(ri: number, ci: number) {
    if (!clipboard.data) return
    pushUndo()
    for (let r = 0; r < clipboard.data.length; r++) {
      for (let c = 0; c < clipboard.data[r].length; c++) {
        const targetRI = ri + r
        const targetCI = ci + c
        if (targetRI < rows.value.length && targetCI < colNames.value.length) {
          updateCellSilent(targetRI, targetCI, clipboard.data[r][c])
        }
      }
    }
    if (clipboard.isCut) {
      for (let r = 0; r < clipboard.data.length; r++) {
        for (let c = 0; c < clipboard.data[r].length; c++) {
          const srcRI = clipboard.sourceRI + r
          const srcCI = clipboard.sourceCI + c
          if (srcRI < rows.value.length && srcCI < colNames.value.length) {
            updateCellSilent(srcRI, srcCI, '')
          }
        }
      }
      clipboard.data = null
      clipboard.isCut = false
    }
  }

  function deleteSelection() {
    if (selection.startRI < 0) return
    pushUndo()
    const s = getNormalizedSelection()
    for (let ri = s.minRI; ri <= s.maxRI; ri++) {
      for (let ci = s.minCI; ci <= s.maxCI; ci++) {
        updateCellSilent(ri, ci, '')
      }
    }
  }

  function findCells(query: string) {
    findState.results = []
    findState.currentIndex = -1
    if (!query) return
    const q = findState.caseSensitive ? query : query.toLowerCase()
    for (let ri = 0; ri < rows.value.length; ri++) {
      for (let ci = 0; ci < colNames.value.length; ci++) {
        const val = getDisplayValue(ri, ci)
        const v = findState.caseSensitive ? val : val.toLowerCase()
        if (v.includes(q)) {
          findState.results.push({ ri, ci })
        }
      }
    }
    if (findState.results.length > 0) {
      findState.currentIndex = 0
      const first = findState.results[0]
      setSelection(first.ri, first.ci)
    }
  }

  function findNext() {
    if (findState.results.length === 0) return
    findState.currentIndex = (findState.currentIndex + 1) % findState.results.length
    const cell = findState.results[findState.currentIndex]
    setSelection(cell.ri, cell.ci)
  }

  function findPrev() {
    if (findState.results.length === 0) return
    findState.currentIndex = (findState.currentIndex - 1 + findState.results.length) % findState.results.length
    const cell = findState.results[findState.currentIndex]
    setSelection(cell.ri, cell.ci)
  }

  function replaceCurrent() {
    if (findState.currentIndex < 0 || findState.currentIndex >= findState.results.length) return
    const cell = findState.results[findState.currentIndex]
    pushUndo()
    updateCellSilent(cell.ri, cell.ci, findState.replaceWith)
    findCells(findState.query)
  }

  function replaceAll() {
    if (findState.results.length === 0) return
    pushUndo()
    for (const cell of findState.results) {
      updateCellSilent(cell.ri, cell.ci, findState.replaceWith)
    }
    findCells(findState.query)
  }

  function sortColumn(ci: number, ascending: boolean) {
    pushUndo()
    rows.value.sort((a, b) => {
      const va = a[ci] || ''
      const vb = b[ci] || ''
      const na = parseFloat(va)
      const nb = parseFloat(vb)
      if (!isNaN(na) && !isNaN(nb)) return ascending ? na - nb : nb - na
      return ascending ? va.localeCompare(vb, undefined, { numeric: true }) : vb.localeCompare(va, undefined, { numeric: true })
    })
  }

  function getUniqueColumnValues(ci: number): string[] {
    const values = new Set<string>()
    for (let ri = 0; ri < rows.value.length; ri++) {
      values.add(getDisplayValue(ri, ci))
    }
    return Array.from(values).sort()
  }

  function toggleFilter(ci: number) {
    if (filterState[ci]) {
      filterState[ci].active = !filterState[ci].active
      if (!filterState[ci].active) delete filterState[ci]
    } else {
      filterState[ci] = { active: true, excludedValues: [] }
    }
  }

  function isRowFiltered(ri: number): boolean {
    for (const ciStr of Object.keys(filterState)) {
      const ci = parseInt(ciStr)
      const filter = filterState[ci]
      if (filter && filter.excludedValues.includes(getDisplayValue(ri, ci))) {
        return true
      }
    }
    return false
  }

  function evaluateConditionalRules(ri: number, ci: number): CellFormat | null {
    const cellVal = getDisplayValue(ri, ci)
    const numVal = parseFloat(cellVal)
    for (const rule of conditionalRules.value) {
      if (ri < rule.range.startRI || ri > rule.range.endRI) continue
      if (ci < rule.range.startCI || ci > rule.range.endCI) continue
      let match = false
      switch (rule.condition) {
        case 'greater': match = !isNaN(numVal) && numVal > parseFloat(rule.value); break
        case 'less': match = !isNaN(numVal) && numVal < parseFloat(rule.value); break
        case 'equal': match = cellVal === rule.value; break
        case 'not_equal': match = cellVal !== rule.value; break
        case 'contains': match = cellVal.includes(rule.value); break
        case 'between': {
          const v1 = parseFloat(rule.value)
          const v2 = parseFloat(rule.value2 || '0')
          match = !isNaN(numVal) && numVal >= Math.min(v1, v2) && numVal <= Math.max(v1, v2)
          break
        }
      }
      if (match) return rule.style
    }
    return null
  }

  function exportCSV(): string {
    const lines: string[] = []
    lines.push(colNames.value.join(','))
    for (const row of rows.value) {
      lines.push(row.map(cell => {
        if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
          return `"${cell.replace(/"/g, '""')}"`
        }
        return cell
      }).join(','))
    }
    return lines.join('\n')
  }

  function importCSV(csv: string) {
    pushUndo()
    const lines = csv.split(/\r?\n/).filter(l => l.trim())
    if (lines.length === 0) return
    const parsed = lines.map(line => {
      const cells: string[] = []
      let current = ''
      let inQuotes = false
      for (let i = 0; i < line.length; i++) {
        const ch = line[i]
        if (inQuotes) {
          if (ch === '"' && line[i + 1] === '"') { current += '"'; i++ }
          else if (ch === '"') { inQuotes = false }
          else { current += ch }
        } else {
          if (ch === '"') { inQuotes = true }
          else if (ch === ',') { cells.push(current); current = '' }
          else { current += ch }
        }
      }
      cells.push(current)
      return cells
    })
    const maxCols = Math.max(...parsed.map(r => r.length))
    colNames.value = Array.from({ length: maxCols }, (_, i) => colName(i))
    colWidths.value = Array(maxCols).fill(100)
    rows.value = parsed.map(r => {
      const row = [...r]
      while (row.length < maxCols) row.push('')
      return row
    })
    rowHeights.value = Array(rows.value.length).fill(28)
  }

  function moveCell(ri: number, ci: number, dir: string) {
    let nr = ri, nc = ci
    if (dir === 'up') nr = Math.max(0, ri - 1)
    else if (dir === 'down') nr = Math.min(rows.value.length - 1, ri + 1)
    else if (dir === 'left') nc = Math.max(0, ci - 1)
    else if (dir === 'right') nc = Math.min(colNames.value.length - 1, ci + 1)
    setSelection(nr, nc)
    return { ri: nr, ci: nc }
  }

  function applyFormatToSelection(format: Partial<CellFormat>) {
    if (selection.startRI < 0) return
    pushUndo()
    const s = getNormalizedSelection()
    for (let ri = s.minRI; ri <= s.maxRI; ri++) {
      for (let ci = s.minCI; ci <= s.maxCI; ci++) {
        setCellStyle(ri, ci, format)
      }
    }
  }

  function applyNumberFormatToSelection(fmt: Partial<NumberFormat>) {
    if (selection.startRI < 0) return
    pushUndo()
    const s = getNormalizedSelection()
    for (let ri = s.minRI; ri <= s.maxRI; ri++) {
      for (let ci = s.minCI; ci <= s.maxCI; ci++) {
        setNumberFormat(ri, ci, fmt)
      }
    }
  }

  function getSelectionStats(): { sum: number; avg: number; count: number; min: number; max: number } {
    if (selection.startRI < 0) return { sum: 0, avg: 0, count: 0, min: 0, max: 0 }
    const s = getNormalizedSelection()
    const values: number[] = []
    for (let ri = s.minRI; ri <= s.maxRI; ri++) {
      for (let ci = s.minCI; ci <= s.maxCI; ci++) {
        const val = parseFloat(getDisplayValue(ri, ci))
        if (!isNaN(val)) values.push(val)
      }
    }
    if (values.length === 0) return { sum: 0, avg: 0, count: 0, min: 0, max: 0 }
    return {
      sum: values.reduce((a, b) => a + b, 0),
      avg: values.reduce((a, b) => a + b, 0) / values.length,
      count: values.length,
      min: Math.min(...values),
      max: Math.max(...values),
    }
  }

  return {
    rows,
    colNames,
    cellStyles,
    numberFormats,
    conditionalRules,
    colWidths,
    rowHeights,
    selection,
    activeCell,
    undoStack,
    redoStack,
    clipboard,
    findState,
    filterState,
    frozenRows,
    getCellStyle,
    setCellStyle,
    getNumberFormat,
    setNumberFormat,
    takeSnapshot,
    pushUndo,
    undo,
    redo,
    getRawValue,
    getDisplayValue,
    evaluateFormula,
    updateCell,
    updateCellSilent,
    addRow,
    addColumn,
    deleteRow,
    deleteColumn,
    setSelection,
    extendSelection,
    getNormalizedSelection,
    isCellSelected,
    isSelectedRange,
    copySelection,
    cutSelection,
    pasteAt,
    deleteSelection,
    findCells,
    findNext,
    findPrev,
    replaceCurrent,
    replaceAll,
    sortColumn,
    getUniqueColumnValues,
    toggleFilter,
    isRowFiltered,
    evaluateConditionalRules,
    exportCSV,
    importCSV,
    moveCell,
    applyFormatToSelection,
    applyNumberFormatToSelection,
    getSelectionStats,
    cellKey,
    colName,
    cellRefStr,
  }
}
