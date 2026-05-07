<template>
  <div class="ai-panel">
    <div class="ai-panel-header">
      <h4>AI: {{ actionLabel }}</h4>
      <button class="close-btn" @click="$emit('close')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    </div>
    <div class="ai-panel-content">
      <div v-if="loading" class="ai-loading">
        <div class="spinner"></div>
        <span>AI is processing...</span>
      </div>
      <div v-else-if="result" class="ai-result">
        <div v-if="result.result && !result.corrected && !result.slides && !result.improved_title && !result.formulas && !result.issues && !result.tags && !result.summary && !result.suggestions && !result.insights && !result.code && !result.explanation && !result.refactored_code && !result.notes && !result.forecast_values && !result.operations && !result.chart_type && !result.translated && !result.adjusted && !result.continuation && !result.answer && !result.outline" class="ai-section">
          <pre class="text-result">{{ result.result }}</pre>
        </div>
        <div v-if="result.corrected" class="ai-section">
          <h5>Corrected Text</h5>
          <div class="corrected-text">{{ result.corrected }}</div>
          <div v-if="result.issues?.length" class="issues-list">
            <div v-for="(issue, i) in result.issues" :key="i" class="issue-item">
              <span class="issue-original">{{ issue.original }}</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              <span class="issue-corrected">{{ issue.corrected }}</span>
              <span class="issue-type">{{ issue.type }}</span>
            </div>
          </div>
        </div>
        <div v-if="result.translated" class="ai-section">
          <h5>Translation</h5>
          <div class="translated-text">{{ result.translated }}</div>
          <div v-if="result.source_lang || result.target_lang" class="translation-meta">
            <span v-if="result.source_lang" class="lang-badge">{{ result.source_lang }}</span>
            <svg width="12" height="12" viewBox="0 0 16 16"><path d="M3 8h10M8 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
            <span v-if="result.target_lang" class="lang-badge">{{ result.target_lang }}</span>
          </div>
        </div>
        <div v-if="result.adjusted" class="ai-section">
          <h5>Tone Adjusted</h5>
          <div class="adjusted-text">{{ result.adjusted }}</div>
          <div v-if="result.tone_description" class="tone-badge">{{ result.tone_description }}</div>
        </div>
        <div v-if="result.continuation" class="ai-section">
          <h5>Continuation</h5>
          <div class="continuation-text">{{ result.continuation }}</div>
        </div>
        <div v-if="result.answer" class="ai-section">
          <h5>Answer</h5>
          <div class="answer-text">{{ result.answer }}</div>
          <div v-if="result.sources?.length" class="sources-list">
            <span class="sources-label">Sources:</span>
            <span v-for="(s, i) in result.sources" :key="i" class="source-item">{{ s }}</span>
          </div>
        </div>
        <div v-if="result.outline?.length" class="ai-section">
          <h5>Outline</h5>
          <div v-for="(item, i) in result.outline" :key="i" :class="['outline-item', `level-${item.level || 1}`]">
            {{ item.text }}
          </div>
        </div>
        <div v-if="result.slides?.length" class="ai-section">
          <h5>Generated Slides</h5>
          <div v-for="(s, i) in result.slides" :key="i" class="slide-item">
            <strong>{{ i + 1 }}. {{ s.title }}</strong>
            <ul v-if="s.bullets"><li v-for="(b, j) in s.bullets" :key="j">{{ b }}</li></ul>
          </div>
        </div>
        <div v-if="result.improved_title" class="ai-section">
          <h5>Improved Content</h5>
          <div class="improved-content">
            <p><strong>Title:</strong> {{ result.improved_title }}</p>
            <div v-if="result.improved_bullets?.length">
              <strong>Bullets:</strong>
              <ul><li v-for="(b, i) in result.improved_bullets" :key="i">{{ b }}</li></ul>
            </div>
          </div>
        </div>
        <div v-if="result.notes" class="ai-section">
          <h5>Speaker Notes</h5>
          <p class="notes-text">{{ result.notes }}</p>
        </div>
        <div v-if="result.color_scheme || result.font_suggestions || result.layout_tips" class="ai-section">
          <h5>Design Suggestions</h5>
          <div v-if="result.color_scheme" class="design-item"><strong>Colors:</strong> {{ result.color_scheme }}</div>
          <div v-if="result.font_suggestions" class="design-item"><strong>Fonts:</strong> {{ result.font_suggestions }}</div>
          <div v-if="result.layout_tips" class="design-item"><strong>Layout:</strong> {{ result.layout_tips }}</div>
        </div>
        <div v-if="result.insights" class="ai-section"><h5>Insights</h5><p class="result-text">{{ result.insights }}</p></div>
        <div v-if="result.trends" class="ai-section"><h5>Trends</h5><p class="result-text">{{ result.trends }}</p></div>
        <div v-if="result.anomalies" class="ai-section"><h5>Anomalies</h5><p class="result-text">{{ result.anomalies }}</p></div>
        <div v-if="result.recommendations" class="ai-section"><h5>Recommendations</h5><p class="result-text">{{ result.recommendations }}</p></div>
        <div v-if="result.formulas?.length" class="ai-section">
          <h5>Suggested Formulas</h5>
          <div v-for="(f, i) in result.formulas" :key="i" class="formula-item">
            <code class="formula-code">{{ f.formula }}</code>
            <p class="formula-desc">{{ f.description }}</p>
          </div>
        </div>
        <div v-if="result.chart_type" class="ai-section">
          <h5>Chart Suggestion</h5>
          <div class="chart-suggestion">
            <span class="chart-type-badge">{{ result.chart_type }}</span>
            <p v-if="result.title_suggestion">{{ result.title_suggestion }}</p>
          </div>
        </div>
        <div v-if="result.operations?.length" class="ai-section">
          <h5>Cleaning Operations</h5>
          <div v-for="(op, i) in result.operations" :key="i" class="clean-op">
            <span class="op-type">{{ op.type }}</span>
            <span class="op-desc">{{ op.description }}</span>
          </div>
        </div>
        <div v-if="result.forecast_values" class="ai-section">
          <h5>Forecast</h5>
          <p class="result-text">{{ result.forecast_values }}</p>
        </div>
        <div v-if="result.tags?.length" class="ai-section">
          <h5>Suggested Tags</h5>
          <div class="tag-list"><span v-for="t in result.tags" :key="t.name" class="tag clickable" @click="$emit('apply', { tags: [t.name] })">{{ t.name }} ({{ (t.confidence * 100).toFixed(0) }}%)</span></div>
        </div>
        <div v-if="result.summary" class="ai-section"><h5>Summary</h5><p class="result-text">{{ result.summary }}</p></div>
        <div v-if="result.suggestions?.length" class="ai-section">
          <h5>Related Notes</h5>
          <div v-for="s in result.suggestions" :key="s.title" class="link-item">{{ s.title }} - {{ s.reason }}</div>
        </div>
        <div v-if="result.explanation" class="ai-section"><h5>Explanation</h5><p class="result-text">{{ result.explanation }}</p></div>
        <div v-if="result.refactored_code" class="ai-section"><h5>Refactored Code</h5><pre class="code-block">{{ result.refactored_code }}</pre></div>
        <div v-if="result.code" class="ai-section"><h5>Generated Code</h5><pre class="code-block">{{ result.code }}</pre></div>
        <div v-if="result.issues?.length && !result.corrected" class="ai-section">
          <h5>Code Review</h5>
          <div v-for="(iss, i) in result.issues" :key="i" :class="['issue-item', iss.severity]">
            <span class="issue-sev">{{ iss.severity }}</span>
            <span class="issue-desc">{{ iss.description }}</span>
          </div>
          <div v-if="result.score != null" class="review-score">Score: {{ result.score }}/10</div>
        </div>
        <div class="ai-actions">
          <button class="apply-btn" @click="$emit('apply')">Apply</button>
          <button class="discard-btn" @click="$emit('close')">Discard</button>
        </div>
      </div>
      <div v-else class="ai-empty">
        <p>Use AI tools to assist your work</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  loading: boolean
  result: any
  actionLabel: string
}>()

defineEmits<{
  close: []
  apply: [data?: any]
}>()
</script>

<style scoped>
.ai-panel {
  width: 360px;
  border-left: 1px solid var(--border-color);
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--border-color);
}

.ai-panel-header h4 {
  margin: 0;
  font-size: var(--font-size-base);
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: var(--spacing-xs);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.close-btn:active {
  transform: scale(0.97);
}

.ai-panel-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-xl);
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--border-color);
  border-top-color: var(--text-primary);
  border-radius: var(--radius-full);
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.ai-result {
  color: var(--text-primary);
}

.ai-section {
  margin-bottom: var(--spacing-lg);
}

.ai-section h5 {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin: 0 0 var(--spacing-sm);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.text-result {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: var(--font-size-sm);
  line-height: 1.5;
  margin: 0;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-lg);
}

.result-text {
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 0;
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.corrected-text,
.translated-text,
.adjusted-text,
.continuation-text,
.answer-text {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
  color: var(--text-primary);
}

.translation-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.lang-badge {
  font-size: var(--font-size-xs);
  padding: 2px var(--spacing-sm);
  background: var(--primary-light);
  color: var(--text-primary);
  border-radius: var(--radius-full);
  font-weight: var(--font-weight-medium);
}

.tone-badge {
  display: inline-block;
  font-size: var(--font-size-xs);
  padding: 2px var(--spacing-sm);
  background: var(--primary-light);
  color: var(--text-primary);
  border-radius: var(--radius-full);
  font-weight: var(--font-weight-medium);
  margin-top: var(--spacing-xs);
}

.outline-item {
  padding: var(--spacing-xs) 0;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.outline-item.level-1 {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  padding-left: 0;
}

.outline-item.level-2 {
  padding-left: var(--spacing-lg);
}

.outline-item.level-3 {
  padding-left: var(--spacing-2xl);
  font-size: var(--font-size-sm);
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-sm);
  align-items: center;
}

.sources-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.source-item {
  font-size: var(--font-size-xs);
  padding: 1px var(--spacing-sm);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
}

.issues-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.issue-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
}

.issue-original {
  color: var(--ws-danger);
  text-decoration: line-through;
}

.issue-corrected {
  color: var(--ws-success);
}

.issue-type {
  background: var(--text-primary);
  color: var(--bg-primary);
  padding: 1px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  margin-left: auto;
}

.slide-item {
  margin-bottom: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.slide-item strong {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.slide-item ul {
  margin: var(--spacing-xs) 0 0;
  padding-left: var(--spacing-lg);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.improved-content {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
}

.improved-content p {
  margin: 0 0 var(--spacing-sm);
}

.notes-text {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--text-secondary);
}

.design-item {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-xs);
}

.design-item strong {
  color: var(--text-primary);
}

.formula-item {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-sm);
}

.formula-code {
  display: block;
  color: var(--ws-success);
  font-family: var(--font-code);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-xs);
}

.formula-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin: 0;
}

.chart-suggestion {
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  border-radius: var(--radius-lg);
}

.chart-type-badge {
  display: inline-block;
  padding: var(--spacing-xs) var(--spacing-md);
  background: var(--text-primary);
  color: var(--bg-primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-sm);
}

.clean-op {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xs);
  font-size: var(--font-size-sm);
}

.op-type {
  background: var(--ws-warning);
  color: var(--bg-primary);
  padding: 1px var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
}

.op-desc {
  flex: 1;
  color: var(--text-secondary);
}

.tag-list {
  display: flex;
  gap: var(--spacing-xs);
  flex-wrap: wrap;
}

.tag {
  font-size: var(--font-size-xs);
  padding: 1px var(--spacing-sm);
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-radius: var(--radius-sm);
}

.tag.clickable {
  cursor: pointer;
}

.tag.clickable:hover {
  background: var(--primary-light);
}

.link-item {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  margin-bottom: var(--spacing-xs);
}

.code-block {
  font-size: var(--font-size-sm);
  line-height: 1.5;
  color: var(--text-primary);
  background: var(--bg-tertiary);
  padding: var(--spacing-sm);
  border-radius: var(--radius-lg);
  overflow-x: auto;
  font-family: var(--font-code);
  white-space: pre-wrap;
  margin: 0;
}

.issue-sev {
  font-size: var(--font-size-xs);
  padding: 1px var(--spacing-sm);
  border-radius: var(--radius-sm);
}

.issue-sev.error {
  background: rgba(239, 68, 68, 0.15);
  color: var(--ws-danger);
}

.issue-sev.warning {
  background: rgba(255, 152, 0, 0.15);
  color: var(--ws-warning);
}

.issue-sev.info {
  background: rgba(59, 130, 246, 0.15);
  color: var(--ws-info);
}

.issue-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.review-score {
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  text-align: center;
}

.ai-actions {
  display: flex;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-md);
}

.apply-btn {
  flex: 1;
  padding: var(--spacing-sm);
  background: var(--text-primary);
  color: var(--bg-primary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-fast);
}

.apply-btn:hover {
  background: var(--primary-hover);
}

.apply-btn:active {
  transform: scale(0.97);
}

.discard-btn {
  flex: 1;
  padding: var(--spacing-sm);
  background: var(--bg-tertiary);
  color: var(--text-tertiary);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--font-size-sm);
  transition: all var(--transition-fast);
}

.discard-btn:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.discard-btn:active {
  transform: scale(0.97);
}

.ai-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}
</style>
