<template>
  <div class="docs-editor-app">
    <div v-if="loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <p>Loading editor...</p>
    </div>
    <div v-if="error" class="error-overlay">
      <p>{{ error }}</p>
      <button @click="initEditor">Retry</button>
    </div>
    <div ref="editorContainer" class="editor-container" :class="{ hidden: loading || error }"></div>
  </div>
</template>

<script>
import axios from 'axios'

const DOCS_SERVICE_URL = import.meta.env.VITE_DOCS_SERVICE_URL || ''
const ONLYOFFICE_URL = import.meta.env.VITE_ONLYOFFICE_URL || 'http://localhost:8082'

function getDocType(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  const map = {
    docx: 'word', doc: 'word', odt: 'word', rtf: 'word', txt: 'word',
    xlsx: 'cell', xls: 'cell', ods: 'cell', csv: 'cell',
    pptx: 'slide', ppt: 'slide', odp: 'slide',
    pdf: 'pdf',
  }
  return map[ext] || 'word'
}

export default {
  name: 'App',
  data() {
    return {
      loading: true,
      error: null,
      editorInstance: null,
      docId: null,
    }
  },
  mounted() {
    this.initFromUrl()
  },
  beforeUnmount() {
    if (this.editorInstance) {
      try {
        this.editorInstance.destroyEditor()
      } catch (e) {
        // ignore
      }
    }
  },
  methods: {
    initFromUrl() {
      const params = new URLSearchParams(window.location.search)
      this.docId = params.get('docId')
      const docType = params.get('type') || 'word'
      const mode = params.get('mode') || 'edit'

      if (this.docId) {
        this.loadExistingDocument(this.docId, mode)
      } else {
        this.createNewDocument(docType, mode)
      }
    },

    async createNewDocument(docType, mode) {
      try {
        this.loading = true
        this.error = null
        const resp = await axios.post(`${DOCS_SERVICE_URL}/docs-api/documents/create`, null, {
          params: { document_type: docType },
        })
        this.docId = resp.data.id
        await this.loadEditor(this.docId, mode)
      } catch (e) {
        this.error = `Failed to create document: ${e.message}`
        this.loading = false
      }
    },

    async loadExistingDocument(docId, mode) {
      try {
        this.loading = true
        this.error = null
        await this.loadEditor(docId, mode)
      } catch (e) {
        this.error = `Failed to load document: ${e.message}`
        this.loading = false
      }
    },

    async loadEditor(docId, mode) {
      try {
        const resp = await axios.get(`${DOCS_SERVICE_URL}/docs-api/documents/${docId}/editor-config`, {
          params: { mode },
        })
        const config = resp.data

        config.width = '100%'
        config.height = '100%'
        config.type = 'embedded'

        if (!config.editorConfig.customization) {
          config.editorConfig.customization = {}
        }
        config.editorConfig.customization.uiTheme = this.getTheme()

        await this.loadOnlyOfficeApi()
        this.createEditor(config)
      } catch (e) {
        this.error = `Failed to load editor config: ${e.message}`
        this.loading = false
      }
    },

    loadOnlyOfficeApi() {
      return new Promise((resolve, reject) => {
        if (window.DocsAPI) {
          resolve()
          return
        }
        const script = document.createElement('script')
        script.src = `${ONLYOFFICE_URL}/web-apps/apps/api/documents/api.js`
        script.onload = resolve
        script.onerror = () => reject(new Error('Failed to load ONLYOFFICE API'))
        document.head.appendChild(script)
      })
    },

    createEditor(config) {
      try {
        this.editorInstance = new window.DocsAPI.DocEditor(this.$refs.editorContainer.id || 'editor-container-' + Date.now(), config)
        this.loading = false
      } catch (e) {
        this.error = `Failed to create editor: ${e.message}`
        this.loading = false
      }
    },

    getTheme() {
      const params = new URLSearchParams(window.location.search)
      const theme = params.get('theme')
      if (theme) return theme === 'dark' ? 'theme-dark' : 'theme-light'
      return 'theme-light'
    },

    initEditor() {
      this.error = null
      this.loading = true
      this.initFromUrl()
    },
  },
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.docs-editor-app {
  width: 100%;
  height: 100%;
  position: relative;
  background: var(--bg-primary, #ffffff);
}

.editor-container {
  width: 100%;
  height: 100%;
}

.editor-container.hidden {
  visibility: hidden;
}

.loading-overlay,
.error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1a1a1a);
  z-index: 100;
  gap: 16px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border, #dddddd);
  border-top-color: var(--primary, #000000);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-overlay button {
  padding: 8px 16px;
  background: var(--primary, #000000);
  color: var(--primary-light, #ffffff);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.error-overlay button:hover {
  opacity: 0.8;
}
</style>
