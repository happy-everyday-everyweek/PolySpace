<template>
  <div class="onlyoffice-wrapper">
    <div v-if="loading" class="oo-loading">
      <div class="oo-spinner"></div>
      <span>Loading editor...</span>
    </div>
    <div v-if="errorMsg" class="oo-error">
      <span>{{ errorMsg }}</span>
      <button class="oo-retry-btn" @click="retry">Retry</button>
      <button class="oo-fallback-btn" @click="$emit('fallback')">Use Local Editor</button>
    </div>
    <div
      :id="containerId"
      class="oo-container"
      :class="{ 'oo-hidden': loading || errorMsg }"
    ></div>
  </div>
</template>

<script>
import axios from 'axios'

const DOCS_SERVICE_BASE = '/docs-api'

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) {
      resolve()
      return
    }
    const s = document.createElement('script')
    s.src = src
    s.onload = resolve
    s.onerror = () => reject(new Error(`Failed to load script: ${src}`))
    document.head.appendChild(s)
  })
}

export default {
  name: 'OnlyOfficeEditor',
  props: {
    docId: { type: String, default: null },
    documentType: { type: String, default: 'word' },
    mode: { type: String, default: 'edit' },
    filename: { type: String, default: null },
  },
  emits: ['fallback', 'saved', 'ready'],
  data() {
    return {
      loading: true,
      errorMsg: null,
      editorInstance: null,
      currentDocId: this.docId,
      containerId: 'oo-editor-' + Math.random().toString(36).slice(2, 8),
    }
  },
  watch: {
    docId(val) {
      if (val && val !== this.currentDocId) {
        this.currentDocId = val
        this.openDocument()
      }
    },
  },
  mounted() {
    this.openDocument()
  },
  beforeUnmount() {
    this.destroyEditor()
  },
  methods: {
    async openDocument() {
      this.loading = true
      this.errorMsg = null

      try {
        if (!this.currentDocId) {
          const resp = await axios.post(`${DOCS_SERVICE_BASE}/documents/create`, null, {
            params: { document_type: this.documentType, filename: this.filename },
          })
          this.currentDocId = resp.data.id
        }

        const configResp = await axios.get(
          `${DOCS_SERVICE_BASE}/documents/${this.currentDocId}/editor-config`,
          { params: { mode: this.mode } }
        )
        const config = configResp.data

        config.width = '100%'
        config.height = '100%'

        config.events = {
          onAppReady: () => {
            this.loading = false
            this.$emit('ready')
          },
          onError: (event) => {
            this.errorMsg = `Editor error: ${event.data.errorDescription || event.data.errorCode}`
            this.loading = false
          },
          onDocumentReady: () => {
            this.loading = false
          },
        }

        const onlyofficeUrl = this.getOnlyOfficeUrl()
        await loadScript(`${onlyofficeUrl}/web-apps/apps/api/documents/api.js`)

        this.destroyEditor()
        this.editorInstance = new window.DocsAPI.DocEditor(this.containerId, config)
      } catch (e) {
        this.errorMsg = `Failed to open document: ${e.message}`
        this.loading = false
      }
    },

    destroyEditor() {
      if (this.editorInstance) {
        try {
          this.editorInstance.destroyEditor()
        } catch (e) {
          // ignore
        }
        this.editorInstance = null
      }
    },

    getOnlyOfficeUrl() {
      return window.__POLYSPACE_ONLYOFFICE_URL__ || 'http://localhost:8082'
    },

    retry() {
      this.openDocument()
    },

    getDocId() {
      return this.currentDocId
    },
  },
}
</script>

<style>
.onlyoffice-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.oo-container {
  width: 100%;
  height: 100%;
}

.oo-container.oo-hidden {
  visibility: hidden;
}

.oo-loading,
.oo-error {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: var(--bg-primary, #ffffff);
  color: var(--text-secondary, #555555);
  font-size: 14px;
  z-index: 10;
}

.oo-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border, #dddddd);
  border-top-color: var(--primary, #000000);
  border-radius: 50%;
  animation: oo-spin 0.8s linear infinite;
}

@keyframes oo-spin {
  to { transform: rotate(360deg); }
}

.oo-retry-btn,
.oo-fallback-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.oo-retry-btn {
  background: var(--primary, #000000);
  color: #ffffff;
}

.oo-fallback-btn {
  background: transparent;
  color: var(--text-secondary, #555555);
  border: 1px solid var(--border, #dddddd);
}
</style>
