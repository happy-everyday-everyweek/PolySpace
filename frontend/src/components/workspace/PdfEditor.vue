<template>
  <div class="pdf-editor">
    <OnlyOfficeEditor
      v-if="useOnlyOffice"
      document-type="pdf"
      mode="view"
      :doc-id="ooDocId"
      @fallback="useOnlyOffice = false"
      @ready="onOnlyOfficeReady"
      @saved="onOnlyOfficeSaved"
    />
    <template v-else>
    <div class="pdf-toolbar">
      <div class="toolbar-left">
        <button class="tool-btn" @click="triggerUpload" title="Open PDF">
          <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h4l2 2h6a1 1 0 011 1v7a1 1 0 01-1 1H2a1 1 0 01-1-1V4a1 1 0 011-1z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M6 9h4M8 7v4" stroke="currentColor" stroke-width="1.2"/></svg>
          <span>Open</span>
        </button>
        <input ref="fileInput" type="file" accept=".pdf" class="hidden-input" @change="handleFileUpload" />
        <div v-if="pdfInfo" class="file-info">
          <span class="file-name">{{ pdfInfo.filename || 'PDF Document' }}</span>
          <span class="file-pages">{{ pdfInfo.page_count }} pages</span>
        </div>
      </div>
      <div class="toolbar-center" v-if="pdfInfo">
        <button class="nav-btn" @click="prevPage" :disabled="currentPage <= 0">
          <svg width="14" height="14" viewBox="0 0 16 16"><path d="M10 3L5 8l5 5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
        <span class="page-indicator">{{ currentPage + 1 }} / {{ pdfInfo.page_count }}</span>
        <button class="nav-btn" @click="nextPage" :disabled="currentPage >= pdfInfo.page_count - 1">
          <svg width="14" height="14" viewBox="0 0 16 16"><path d="M6 3l5 5-5 5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
        </button>
        <div class="zoom-controls">
          <button class="nav-btn" @click="zoomOut" :disabled="zoom <= 50">
            <svg width="14" height="14" viewBox="0 0 16 16"><circle cx="7" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M10 10l4 4" stroke="currentColor" stroke-width="1.2"/><path d="M5 7h4" stroke="currentColor" stroke-width="1.2"/></svg>
          </button>
          <span class="zoom-label">{{ zoom }}%</span>
          <button class="nav-btn" @click="zoomIn" :disabled="zoom >= 300">
            <svg width="14" height="14" viewBox="0 0 16 16"><circle cx="7" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M10 10l4 4" stroke="currentColor" stroke-width="1.2"/><path d="M5 7h4M7 5v4" stroke="currentColor" stroke-width="1.2"/></svg>
          </button>
          <button class="nav-btn" @click="zoomFit" title="Fit Width">
            <svg width="14" height="14" viewBox="0 0 16 16"><rect x="1" y="4" width="14" height="8" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M4 7h2M10 7h2M5 6v2M11 6v2" stroke="currentColor" stroke-width="1"/></svg>
          </button>
        </div>
      </div>
      <div class="toolbar-right" v-if="pdfInfo">
        <button class="tool-btn" :class="{ active: activePanel === 'watermark' }" @click="togglePanel('watermark')" title="Watermark">
          <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 2h12v12H2V2z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M4 12L8 4l4 8" fill="none" stroke="currentColor" stroke-width="1" opacity="0.5"/><path d="M5.5 9h5" stroke="currentColor" stroke-width="0.8" opacity="0.5"/></svg>
          <span>Watermark</span>
        </button>
        <button class="tool-btn" :class="{ active: activePanel === 'encrypt' }" @click="togglePanel('encrypt')" title="Encrypt/Decrypt">
          <svg width="16" height="16" viewBox="0 0 16 16"><rect x="3" y="7" width="10" height="7" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M5 7V5a3 3 0 016 0v2" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="8" cy="10.5" r="1" fill="currentColor"/></svg>
          <span>Encrypt</span>
        </button>
        <button class="tool-btn" :class="{ active: activePanel === 'pages' }" @click="togglePanel('pages')" title="Page Operations">
          <svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="5" height="5" rx="0.5" fill="none" stroke="currentColor" stroke-width="1"/><rect x="9" y="2" width="5" height="5" rx="0.5" fill="none" stroke="currentColor" stroke-width="1"/><rect x="2" y="9" width="5" height="5" rx="0.5" fill="none" stroke="currentColor" stroke-width="1"/><rect x="9" y="9" width="5" height="5" rx="0.5" fill="none" stroke="currentColor" stroke-width="1"/></svg>
          <span>Pages</span>
        </button>
        <button class="tool-btn" :class="{ active: activePanel === 'annotate' }" @click="togglePanel('annotate')" title="Annotate">
          <svg width="16" height="16" viewBox="0 0 16 16"><path d="M12 2l2 2-8 8H4v-2l8-8z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2 14h12" stroke="currentColor" stroke-width="1"/></svg>
          <span>Annotate</span>
        </button>
        <button class="tool-btn" :class="{ active: activePanel === 'tools' }" @click="togglePanel('tools')" title="More Tools">
          <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="4" cy="4" r="1.5" fill="currentColor"/><circle cx="12" cy="4" r="1.5" fill="currentColor"/><circle cx="4" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/></svg>
          <span>Tools</span>
        </button>
      </div>
    </div>

    <div class="pdf-body">
      <div class="pdf-viewer" ref="viewerContainer" @wheel="handleWheel">
        <div v-if="!pdfInfo" class="pdf-empty">
          <svg width="64" height="64" viewBox="0 0 64 64"><path d="M12 8h24l16 16v32a4 4 0 01-4 4H12a4 4 0 01-4-4V12a4 4 0 014-4z" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/><path d="M36 8v16h16" fill="none" stroke="currentColor" stroke-width="2" opacity="0.3"/><path d="M20 36h24M20 42h18M20 48h12" stroke="currentColor" stroke-width="1.5" opacity="0.2"/></svg>
          <p>Drop a PDF file here or click Open</p>
          <button class="open-btn" @click="triggerUpload">Open PDF</button>
        </div>
        <div v-else class="pdf-page-container" :style="{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }">
          <img v-if="currentPageImage" :src="currentPageImage" class="pdf-page-image" alt="PDF Page" />
          <div v-else class="pdf-loading">
            <div class="spinner"></div>
            <span>Loading page...</span>
          </div>
        </div>
      </div>

      <div v-if="activePanel" class="pdf-panel">
        <div class="panel-header">
          <h4>{{ panelTitle }}</h4>
          <button class="close-btn" @click="activePanel = ''">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="panel-content">
          <div v-if="activePanel === 'watermark'" class="panel-section">
            <div class="form-group">
              <label>Watermark Text</label>
              <input v-model="watermark.text" type="text" placeholder="Enter watermark text" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Font Size</label>
                <input v-model.number="watermark.fontSize" type="number" min="8" max="120" />
              </div>
              <div class="form-group">
                <label>Opacity</label>
                <input v-model.number="watermark.opacity" type="number" min="0" max="1" step="0.05" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Color</label>
                <input v-model="watermark.color" type="color" />
              </div>
              <div class="form-group">
                <label>Angle</label>
                <input v-model.number="watermark.angle" type="number" min="-180" max="180" />
              </div>
            </div>
            <div class="form-group">
              <label>Position</label>
              <select v-model="watermark.position">
                <option value="center">Center</option>
                <option value="tile">Tile (Repeat)</option>
                <option value="top-left">Top Left</option>
                <option value="top-right">Top Right</option>
                <option value="bottom-left">Bottom Left</option>
                <option value="bottom-right">Bottom Right</option>
              </select>
            </div>
            <button class="action-btn primary" @click="applyWatermark" :disabled="processing">
              {{ processing ? 'Applying...' : 'Apply Watermark' }}
            </button>
          </div>

          <div v-if="activePanel === 'encrypt'" class="panel-section">
            <div class="encrypt-tabs">
              <button :class="['tab-btn', { active: encryptTab === 'encrypt' }]" @click="encryptTab = 'encrypt'">Encrypt</button>
              <button :class="['tab-btn', { active: encryptTab === 'decrypt' }]" @click="encryptTab = 'decrypt'">Decrypt</button>
            </div>
            <div v-if="encryptTab === 'encrypt'">
              <div class="form-group">
                <label>User Password</label>
                <input v-model="encrypt.userPassword" type="password" placeholder="Password to open" />
              </div>
              <div class="form-group">
                <label>Owner Password</label>
                <input v-model="encrypt.ownerPassword" type="password" placeholder="Password for permissions (optional)" />
              </div>
              <div class="form-group">
                <label class="checkbox-label"><input type="checkbox" v-model="encrypt.allowPrint" /> Allow Printing</label>
              </div>
              <div class="form-group">
                <label class="checkbox-label"><input type="checkbox" v-model="encrypt.allowCopy" /> Allow Copying</label>
              </div>
              <div class="form-group">
                <label class="checkbox-label"><input type="checkbox" v-model="encrypt.allowModify" /> Allow Modifying</label>
              </div>
              <div class="form-group">
                <label class="checkbox-label"><input type="checkbox" v-model="encrypt.allowAnnotate" /> Allow Annotations</label>
              </div>
              <button class="action-btn primary" @click="applyEncrypt" :disabled="processing">
                {{ processing ? 'Encrypting...' : 'Encrypt PDF (AES-256)' }}
              </button>
            </div>
            <div v-if="encryptTab === 'decrypt'">
              <div class="form-group">
                <label>Password</label>
                <input v-model="decrypt.password" type="password" placeholder="Enter password" />
              </div>
              <button class="action-btn primary" @click="applyDecrypt" :disabled="processing">
                {{ processing ? 'Decrypting...' : 'Decrypt PDF' }}
              </button>
            </div>
          </div>

          <div v-if="activePanel === 'pages'" class="panel-section">
            <div class="page-ops-grid">
              <button class="op-btn" @click="rotatePages(90)">Rotate 90</button>
              <button class="op-btn" @click="rotatePages(180)">Rotate 180</button>
              <button class="op-btn" @click="rotatePages(270)">Rotate 270</button>
              <button class="op-btn" @click="deletePages">Delete Pages</button>
            </div>
            <div class="form-group">
              <label>Page Range (e.g., 1-3, 5, 7-9)</label>
              <input v-model="pageOps.range" type="text" placeholder="Leave empty for all pages" />
            </div>
            <hr class="divider" />
            <h5>Split PDF</h5>
            <div class="form-group">
              <label>Pages to Extract</label>
              <input v-model="pageOps.splitRange" type="text" placeholder="e.g., 1-3, 5" />
            </div>
            <button class="action-btn" @click="splitPdf" :disabled="processing">Split</button>
            <hr class="divider" />
            <h5>Merge PDFs</h5>
            <p class="hint">Open another PDF and it will be added to merge list</p>
            <div v-if="mergeList.length" class="merge-list">
              <div v-for="(item, i) in mergeList" :key="i" class="merge-item">
                <span>{{ item.name }}</span>
                <button class="remove-btn" @click="mergeList.splice(i, 1)">x</button>
              </div>
            </div>
            <button class="action-btn" @click="mergePdfs" :disabled="processing || mergeList.length < 2">Merge All</button>
            <hr class="divider" />
            <h5>Page Numbers</h5>
            <div class="form-row">
              <div class="form-group">
                <label>Format</label>
                <select v-model="pageOps.numberFormat">
                  <option value="1/N">1/N</option>
                  <option value="- 1 -">- 1 -</option>
                  <option value="Page 1">Page 1</option>
                  <option value="Page 1 of N">Page 1 of N</option>
                </select>
              </div>
              <div class="form-group">
                <label>Position</label>
                <select v-model="pageOps.numberPosition">
                  <option value="bottom-center">Bottom Center</option>
                  <option value="bottom-right">Bottom Right</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="top-center">Top Center</option>
                </select>
              </div>
            </div>
            <button class="action-btn" @click="addPageNumbers" :disabled="processing">Add Page Numbers</button>
            <hr class="divider" />
            <h5>Header & Footer</h5>
            <div class="form-group">
              <label>Header (supports {'{page}'}, {'{total}'}, {'{date}'})</label>
              <input v-model="pageOps.header" type="text" placeholder="e.g., Confidential - {date}" />
            </div>
            <div class="form-group">
              <label>Footer</label>
              <input v-model="pageOps.footer" type="text" placeholder="e.g., Page {page} of {total}" />
            </div>
            <button class="action-btn" @click="addHeaderFooter" :disabled="processing">Apply Header/Footer</button>
          </div>

          <div v-if="activePanel === 'annotate'" class="panel-section">
            <div class="annot-type-grid">
              <button :class="['op-btn', { active: annotType === 'highlight' }]" @click="annotType = 'highlight'">Highlight</button>
              <button :class="['op-btn', { active: annotType === 'text' }]" @click="annotType = 'text'">Text Note</button>
              <button :class="['op-btn', { active: annotType === 'stamp' }]" @click="annotType = 'stamp'">Stamp</button>
            </div>
            <div v-if="annotType === 'highlight'" class="form-group">
              <label>Color</label>
              <input v-model="annotation.color" type="color" />
            </div>
            <div v-if="annotType === 'highlight'" class="form-group">
              <label>Area (x0, y0, x1, y1)</label>
              <input v-model="annotation.rect" type="text" placeholder="50,600,300,620" />
            </div>
            <div v-if="annotType === 'text'" class="form-group">
              <label>Note Content</label>
              <textarea v-model="annotation.content" rows="3" placeholder="Enter note text"></textarea>
            </div>
            <div v-if="annotType === 'text'" class="form-group">
              <label>Position (x, y)</label>
              <input v-model="annotation.rect" type="text" placeholder="100,700" />
            </div>
            <div v-if="annotType === 'stamp'" class="form-group">
              <label>Stamp Icon</label>
              <select v-model="annotation.icon">
                <option value="Note">Note</option>
                <option value="Comment">Comment</option>
                <option value="Help">Help</option>
                <option value="Insert">Insert</option>
                <option value="Key">Key</option>
                <option value="NewParagraph">New Paragraph</option>
                <option value="Paragraph">Paragraph</option>
              </select>
            </div>
            <div v-if="annotType === 'stamp'" class="form-group">
              <label>Area (x0, y0, x1, y1)</label>
              <input v-model="annotation.rect" type="text" placeholder="350,50,450,100" />
            </div>
            <button class="action-btn primary" @click="addAnnotation" :disabled="processing">
              {{ processing ? 'Adding...' : 'Add Annotation' }}
            </button>
          </div>

          <div v-if="activePanel === 'tools'" class="panel-section">
            <div class="tools-grid">
              <button class="tool-card" @click="compressPdf" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><path d="M2 4l6 4 6-4" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2 8l6 4 6-4" fill="none" stroke="currentColor" stroke-width="1.2" opacity="0.5"/></svg>
                <span>Compress</span>
              </button>
              <button class="tool-card" @click="convertPdf('images')" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="5.5" r="1.5" fill="none" stroke="currentColor" stroke-width="1"/><path d="M2 11l3-3 2 2 3-4 4 5" fill="none" stroke="currentColor" stroke-width="1"/></svg>
                <span>To Images</span>
              </button>
              <button class="tool-card" @click="convertPdf('txt')" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><path d="M3 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M5 7h6M5 9h6M5 11h4" stroke="currentColor" stroke-width="1"/></svg>
                <span>To Text</span>
              </button>
              <button class="tool-card" @click="convertPdf('html')" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><path d="M5 4L1 8l4 4M11 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
                <span>To HTML</span>
              </button>
              <button class="tool-card" @click="extractText" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><path d="M4 2h8v12H4V2z" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M6 5h4M6 7h4M6 9h3" stroke="currentColor" stroke-width="1"/></svg>
                <span>Extract Text</span>
              </button>
              <button class="tool-card" @click="redactText" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><rect x="2" y="3" width="12" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><rect x="4" y="5" width="8" height="2" fill="currentColor" opacity="0.6"/><rect x="4" y="9" width="5" height="2" fill="currentColor" opacity="0.6"/></svg>
                <span>Redact Text</span>
              </button>
              <button class="tool-card" @click="togglePanel('metadata')" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M8 5v3M8 10.5v.5" stroke="currentColor" stroke-width="1.5"/></svg>
                <span>Metadata</span>
              </button>
              <button class="tool-card" @click="togglePanel('bookmarks')" :disabled="processing">
                <svg width="20" height="20" viewBox="0 0 16 16"><path d="M3 2h10v12l-5-3-5 3V2z" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
                <span>Bookmarks</span>
              </button>
            </div>
            <div v-if="showExtractedText" class="text-output">
              <div class="text-output-header">
                <h5>Extracted Text</h5>
                <button class="copy-btn" @click="copyText">Copy</button>
              </div>
              <pre class="text-content">{{ extractedText }}</pre>
            </div>
            <div v-if="activePanel === 'tools' && showRedactForm" class="redact-form">
              <div class="form-group">
                <label>Text to Redact (one per line)</label>
                <textarea v-model="redact.texts" rows="3" placeholder="Enter text patterns to redact"></textarea>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Redact Color</label>
                  <input v-model="redact.color" type="color" />
                </div>
              </div>
              <button class="action-btn primary" @click="applyRedact" :disabled="processing">Apply Redaction</button>
            </div>
          </div>

          <div v-if="activePanel === 'metadata'" class="panel-section">
            <div v-if="pdfInfo" class="metadata-form">
              <div class="form-group">
                <label>Title</label>
                <input v-model="metadata.title" type="text" />
              </div>
              <div class="form-group">
                <label>Author</label>
                <input v-model="metadata.author" type="text" />
              </div>
              <div class="form-group">
                <label>Subject</label>
                <input v-model="metadata.subject" type="text" />
              </div>
              <div class="form-group">
                <label>Keywords</label>
                <input v-model="metadata.keywords" type="text" />
              </div>
              <div v-if="pdfInfo.metadata" class="meta-readonly">
                <div class="meta-item"><span class="meta-label">Creator:</span><span>{{ pdfInfo.metadata.creator || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">Producer:</span><span>{{ pdfInfo.metadata.producer || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">Created:</span><span>{{ pdfInfo.metadata.creationDate || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">Modified:</span><span>{{ pdfInfo.metadata.modDate || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">Encrypted:</span><span>{{ pdfInfo.is_encrypted ? 'Yes' : 'No' }}</span></div>
              </div>
              <button class="action-btn primary" @click="updateMetadata" :disabled="processing">Update Metadata</button>
            </div>
          </div>

          <div v-if="activePanel === 'bookmarks'" class="panel-section">
            <div v-if="pdfInfo && pdfInfo.bookmarks && pdfInfo.bookmarks.length" class="bookmark-list">
              <div v-for="(bm, i) in pdfInfo.bookmarks" :key="i" class="bookmark-item" :style="{ paddingLeft: (bm.level * 16 + 8) + 'px' }">
                <span class="bm-title">{{ bm.title }}</span>
                <span class="bm-page">p.{{ bm.page + 1 }}</span>
                <button class="remove-btn" @click="removeBookmark(i)">x</button>
              </div>
            </div>
            <p v-else class="hint">No bookmarks found</p>
            <hr class="divider" />
            <h5>Add Bookmark</h5>
            <div class="form-group">
              <label>Title</label>
              <input v-model="bookmark.title" type="text" placeholder="Bookmark title" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Page</label>
                <input v-model.number="bookmark.page" type="number" min="0" />
              </div>
              <div class="form-group">
                <label>Level</label>
                <input v-model.number="bookmark.level" type="number" min="0" max="5" />
              </div>
            </div>
            <button class="action-btn primary" @click="addBookmark" :disabled="processing">Add Bookmark</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="statusMessage" :class="['status-bar', statusType]">{{ statusMessage }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import api from '../../utils/api'
import OnlyOfficeEditor from './OnlyOfficeEditor.vue'
import { useAppSettings } from '@/composables/useAppSettings'

const pdfDefaults = useAppSettings('pdf').settings.value

const useOnlyOffice = ref(true)
const ooDocId = ref<string | null>(null)

function onOnlyOfficeReady() {}
function onOnlyOfficeSaved() {}

const fileInput = ref<HTMLInputElement | null>(null)
const viewerContainer = ref<HTMLElement | null>(null)

const pdfInfo = ref<any>(null)
const currentFileId = ref('')
const currentPage = ref(0)
const currentPageImage = ref('')
const zoom = ref(100)
const activePanel = ref('')
const processing = ref(false)
const statusMessage = ref('')
const statusType = ref('info')
const showExtractedText = ref(false)
const extractedText = ref('')
const showRedactForm = ref(false)

const watermark = ref({
  text: pdfDefaults.watermarkText || 'CONFIDENTIAL',
  fontSize: pdfDefaults.watermarkFontSize,
  opacity: pdfDefaults.watermarkOpacity,
  color: '#808080',
  angle: pdfDefaults.watermarkAngle,
  position: pdfDefaults.watermarkPosition,
})

const encrypt = ref({
  userPassword: '',
  ownerPassword: '',
  allowPrint: true,
  allowCopy: true,
  allowModify: false,
  allowAnnotate: true,
})

const decrypt = ref({ password: '' })
const encryptTab = ref('encrypt')

const pageOps = ref({
  range: '',
  splitRange: '',
  numberFormat: '1/N',
  numberPosition: 'bottom-center',
  header: '',
  footer: '',
})

const annotation = ref({
  color: '#FFFF00',
  rect: '',
  content: '',
  icon: 'Note',
})
const annotType = ref('highlight')

const metadata = ref({ title: '', author: '', subject: '', keywords: '' })
const bookmark = ref({ title: '', page: 0, level: 0 })

const mergeList = ref<{ id: string; name: string }[]>([])

const panelTitle = computed(() => {
  const titles: Record<string, string> = {
    watermark: 'Watermark',
    encrypt: 'Encrypt / Decrypt',
    pages: 'Page Operations',
    annotate: 'Annotations',
    tools: 'Tools',
    metadata: 'Metadata',
    bookmarks: 'Bookmarks',
  }
  return titles[activePanel.value] || ''
})

function showStatus(msg: string, type = 'info') {
  statusMessage.value = msg
  statusType.value = type
  setTimeout(() => { statusMessage.value = '' }, 4000)
}

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    processing.value = true
    const res = await api.post('/pdf/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    currentFileId.value = res.data.path || res.data.file_id
    await loadPdfInfo()
    if (mergeList.value.length === 0) {
      mergeList.value.push({ id: currentFileId.value, name: file.name })
    }
    showStatus('PDF loaded successfully', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Upload failed', 'error')
  } finally {
    processing.value = false
    target.value = ''
  }
}

async function loadPdfInfo() {
  if (!currentFileId.value) return
  try {
    const res = await api.get(`/pdf/info/${currentFileId.value}`)
    pdfInfo.value = res.data
    if (pdfInfo.value.metadata) {
      metadata.value.title = pdfInfo.value.metadata.title || ''
      metadata.value.author = pdfInfo.value.metadata.author || ''
      metadata.value.subject = pdfInfo.value.metadata.subject || ''
      metadata.value.keywords = pdfInfo.value.metadata.keywords || ''
    }
    currentPage.value = 0
    await loadPageImage()
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Failed to load PDF info', 'error')
  }
}

async function loadPageImage() {
  if (!currentFileId.value) return
  try {
    const res = await api.get(`/pdf/page/${currentFileId.value}/${currentPage.value}`, { params: { dpi: 150 } })
    currentPageImage.value = `data:image/png;base64,${res.data.image_base64}`
  } catch (err: any) {
    currentPageImage.value = ''
  }
}

function prevPage() {
  if (currentPage.value > 0) {
    currentPage.value--
    loadPageImage()
  }
}

function nextPage() {
  if (pdfInfo.value && currentPage.value < pdfInfo.value.page_count - 1) {
    currentPage.value++
    loadPageImage()
  }
}

function zoomIn() { if (zoom.value < 300) zoom.value += 25 }
function zoomOut() { if (zoom.value > 50) zoom.value -= 25 }
function zoomFit() { zoom.value = 100 }

function handleWheel(e: WheelEvent) {
  if (e.ctrlKey) {
    e.preventDefault()
    if (e.deltaY < 0) zoomIn()
    else zoomOut()
  }
}

function togglePanel(panel: string) {
  activePanel.value = activePanel.value === panel ? '' : panel
  if (panel === 'tools') {
    showRedactForm.value = false
    showExtractedText.value = false
  }
}

async function applyWatermark() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/watermark', null, {
      params: {
        file_id: currentFileId.value,
        text: watermark.value.text,
        opacity: watermark.value.opacity,
        font_size: watermark.value.fontSize,
        color: watermark.value.color,
        angle: watermark.value.angle,
        position: watermark.value.position,
      },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Watermark applied', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Watermark failed', 'error')
  } finally {
    processing.value = false
  }
}

async function applyEncrypt() {
  if (!currentFileId.value || !encrypt.value.userPassword) {
    showStatus('Password required', 'error')
    return
  }
  processing.value = true
  try {
    const res = await api.post('/pdf/encrypt', null, {
      params: {
        file_id: currentFileId.value,
        password: encrypt.value.userPassword,
        owner_password: encrypt.value.ownerPassword || undefined,
        allow_print: encrypt.value.allowPrint,
        allow_copy: encrypt.value.allowCopy,
        allow_modify: encrypt.value.allowModify,
        allow_annotate: encrypt.value.allowAnnotate,
      },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('PDF encrypted with AES-256', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Encryption failed', 'error')
  } finally {
    processing.value = false
  }
}

async function applyDecrypt() {
  if (!currentFileId.value || !decrypt.value.password) {
    showStatus('Password required', 'error')
    return
  }
  processing.value = true
  try {
    const res = await api.post('/pdf/decrypt', null, {
      params: { file_id: currentFileId.value, password: decrypt.value.password },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('PDF decrypted', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Decryption failed', 'error')
  } finally {
    processing.value = false
  }
}

async function rotatePages(angle: number) {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const params: any = { file_id: currentFileId.value, angle }
    if (pageOps.value.range) params.pages = pageOps.value.range
    const res = await api.post('/pdf/rotate', null, { params })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus(`Pages rotated ${angle} degrees`, 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Rotation failed', 'error')
  } finally {
    processing.value = false
  }
}

async function deletePages() {
  if (!currentFileId.value || !pageOps.value.range) {
    showStatus('Page range required for delete', 'error')
    return
  }
  if (!confirm(`Delete pages ${pageOps.value.range}?`)) return
  processing.value = true
  try {
    await api.post('/pdf/split', null, {
      params: { file_id: currentFileId.value, pages: pageOps.value.range },
    })
    showStatus('Pages extracted (split operation)', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Delete failed', 'error')
  } finally {
    processing.value = false
  }
}

async function splitPdf() {
  if (!currentFileId.value || !pageOps.value.splitRange) {
    showStatus('Page range required', 'error')
    return
  }
  processing.value = true
  try {
    await api.post('/pdf/split', null, {
      params: { file_id: currentFileId.value, pages: pageOps.value.splitRange },
    })
    showStatus('PDF split successfully', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Split failed', 'error')
  } finally {
    processing.value = false
  }
}

async function mergePdfs() {
  if (mergeList.value.length < 2) {
    showStatus('At least 2 PDFs needed for merge', 'error')
    return
  }
  processing.value = true
  try {
    const ids = mergeList.value.map(m => m.id)
    const res = await api.post('/pdf/merge', null, { params: { file_ids: ids } })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus(`${ids.length} PDFs merged`, 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Merge failed', 'error')
  } finally {
    processing.value = false
  }
}

async function addPageNumbers() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/page-numbers', null, {
      params: {
        file_id: currentFileId.value,
        format: pageOps.value.numberFormat,
        position: pageOps.value.numberPosition,
      },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Page numbers added', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Failed', 'error')
  } finally {
    processing.value = false
  }
}

async function addHeaderFooter() {
  if (!currentFileId.value) return
  if (!pageOps.value.header && !pageOps.value.footer) {
    showStatus('Header or footer text required', 'error')
    return
  }
  processing.value = true
  try {
    const res = await api.post('/pdf/header-footer', null, {
      params: {
        file_id: currentFileId.value,
        header: pageOps.value.header,
        footer: pageOps.value.footer,
      },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Header/Footer added', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Failed', 'error')
  } finally {
    processing.value = false
  }
}

async function addAnnotation() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const params: any = {
      file_id: currentFileId.value,
      page_num: currentPage.value,
      annotation_type: annotType.value,
      color: annotation.value.color,
    }
    if (annotation.value.rect) params.rect = annotation.value.rect
    if (annotation.value.content) params.content = annotation.value.content
    if (annotType.value === 'stamp') params.icon = annotation.value.icon
    const res = await api.post('/pdf/annotate', null, { params })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Annotation added', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Annotation failed', 'error')
  } finally {
    processing.value = false
  }
}

async function compressPdf() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/compress', null, { params: { file_id: currentFileId.value } })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus(`Compressed: ${res.data.compression_ratio} reduction`, 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Compress failed', 'error')
  } finally {
    processing.value = false
  }
}

async function convertPdf(format: string) {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/convert', null, {
      params: { file_id: currentFileId.value, format, dpi: 150 },
    })
    if (format === 'txt' && res.data.results?.[0]?.text) {
      extractedText.value = res.data.results[0].text
      showExtractedText.value = true
    } else if (format === 'images' && res.data.results?.length) {
      showStatus(`Converted to ${res.data.results.length} images`, 'success')
    } else {
      showStatus(`Converted to ${format}`, 'success')
    }
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Convert failed', 'error')
  } finally {
    processing.value = false
  }
}

async function extractText() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.get(`/pdf/text/${currentFileId.value}`)
    extractedText.value = res.data.text
    showExtractedText.value = true
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Extract failed', 'error')
  } finally {
    processing.value = false
  }
}

function copyText() {
  navigator.clipboard.writeText(extractedText.value)
  showStatus('Text copied to clipboard', 'success')
}

function redactText() {
  showRedactForm.value = true
}

const redact = ref({ texts: '', color: '#000000' })

async function applyRedact() {
  if (!currentFileId.value || !redact.value.texts) return
  processing.value = true
  try {
    const texts = redact.value.texts.split('\n').filter(t => t.trim())
    const res = await api.post('/pdf/redact', null, {
      params: { file_id: currentFileId.value, texts, color: redact.value.color },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus(`${res.data.redactions} redactions applied`, 'success')
    showRedactForm.value = false
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Redact failed', 'error')
  } finally {
    processing.value = false
  }
}

async function updateMetadata() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const params: any = { file_id: currentFileId.value }
    if (metadata.value.title) params.title = metadata.value.title
    if (metadata.value.author) params.author = metadata.value.author
    if (metadata.value.subject) params.subject = metadata.value.subject
    if (metadata.value.keywords) params.keywords = metadata.value.keywords
    const res = await api.post('/pdf/metadata', null, { params })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Metadata updated', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Update failed', 'error')
  } finally {
    processing.value = false
  }
}

async function addBookmark() {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/bookmark', null, {
      params: {
        file_id: currentFileId.value,
        action: 'add',
        title: bookmark.value.title,
        page: bookmark.value.page,
        level: bookmark.value.level,
      },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Bookmark added', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Failed', 'error')
  } finally {
    processing.value = false
  }
}

async function removeBookmark(index: number) {
  if (!currentFileId.value) return
  processing.value = true
  try {
    const res = await api.post('/pdf/bookmark', null, {
      params: { file_id: currentFileId.value, action: 'remove', index },
    })
    currentFileId.value = res.data.output_file_id
    await loadPdfInfo()
    showStatus('Bookmark removed', 'success')
  } catch (err: any) {
    showStatus(err.response?.data?.detail || 'Failed', 'error')
  } finally {
    processing.value = false
  }
}
</script>

<style scoped>
.pdf-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-color);
  background: #141428;
  gap: 12px;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #b0b0c0;
  background: none;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.tool-btn:hover {
  background: var(--ws-accent-light);
  color: var(--text-primary);
  border-color: var(--ws-accent);
}

.tool-btn.active {
  background: var(--ws-accent);
  color: var(--bg-primary);
  border-color: var(--ws-accent);
}

.tool-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.file-info {
  display: flex;
  flex-direction: column;
  margin-left: 8px;
}

.file-name {
  font-size: 12px;
  color: var(--text-primary);
  font-weight: 500;
}

.file-pages {
  font-size: 10px;
  color: var(--text-tertiary);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  background: none;
  border: 1px solid var(--border-color);
  color: #b0b0c0;
  cursor: pointer;
  transition: all 0.15s;
}

.nav-btn:hover:not(:disabled) {
  background: var(--ws-accent-light);
  color: var(--text-primary);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-indicator {
  font-size: 12px;
  color: #b0b0c0;
  min-width: 60px;
  text-align: center;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.zoom-label {
  font-size: 11px;
  color: var(--text-tertiary);
  min-width: 36px;
  text-align: center;
}

.hidden-input {
  display: none;
}

.pdf-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.pdf-viewer {
  flex: 1;
  overflow: auto;
  display: flex;
  justify-content: center;
  padding: 24px;
}

.pdf-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--text-tertiary);
}

.pdf-empty p {
  font-size: 14px;
}

.open-btn {
  padding: 8px 20px;
  border-radius: 6px;
  background: var(--ws-accent);
  color: #fff;
  font-size: 13px;
  border: none;
  cursor: pointer;
}

.open-btn:hover {
  background: var(--ws-accent-hover);
}

.pdf-page-container {
  transition: transform 0.2s;
}

.pdf-page-image {
  max-width: 100%;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
}

.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px;
  color: var(--text-tertiary);
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--border-color);
  border-top-color: var(--ws-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.pdf-panel {
  width: 300px;
  border-left: 1px solid var(--border-color);
  background: #141428;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  color: var(--ws-accent-soft);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
}

.close-btn:hover {
  color: #fff;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 11px;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 12px;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--ws-accent);
}

.form-group textarea {
  resize: vertical;
  font-family: inherit;
}

.form-group input[type="color"] {
  height: 30px;
  padding: 2px;
  cursor: pointer;
}

.form-row {
  display: flex;
  gap: 8px;
}

.form-row .form-group {
  flex: 1;
}

.checkbox-label {
  display: flex !important;
  flex-direction: row !important;
  align-items: center;
  gap: 6px;
  font-size: 12px !important;
  text-transform: none !important;
  color: var(--text-secondary) !important;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: var(--ws-accent);
}

.action-btn {
  padding: 7px 14px;
  border-radius: 6px;
  background: var(--border-color);
  color: #b0b0c0;
  font-size: 12px;
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover:not(:disabled) {
  background: var(--border-color);
  color: var(--text-primary);
}

.action-btn.primary {
  background: var(--ws-accent);
  color: var(--bg-primary);
  border-color: var(--ws-accent);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--ws-accent-hover);
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.encrypt-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.tab-btn {
  flex: 1;
  padding: 6px;
  border-radius: 4px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-tertiary);
  font-size: 12px;
  cursor: pointer;
}

.tab-btn.active {
  background: var(--ws-accent);
  color: #fff;
  border-color: var(--ws-accent);
}

.page-ops-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.op-btn {
  padding: 6px 8px;
  border-radius: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: #b0b0c0;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.op-btn:hover {
  background: var(--ws-accent-light);
  border-color: var(--ws-accent);
  color: var(--text-primary);
}

.op-btn.active {
  background: var(--ws-accent);
  color: var(--bg-primary);
  border-color: var(--ws-accent);
}

.divider {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 8px 0;
}

.hint {
  font-size: 11px;
  color: var(--text-tertiary);
  margin: 0;
}

.tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.tool-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  border-radius: 6px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: #b0b0c0;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.tool-card:hover:not(:disabled) {
  background: var(--ws-accent-light);
  border-color: var(--ws-accent);
  color: var(--text-primary);
}

.tool-card:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.annot-type-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 4px;
}

.merge-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.merge-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 12px;
}

.remove-btn {
  background: none;
  border: none;
  color: #ff5555;
  cursor: pointer;
  font-size: 12px;
}

.text-output {
  margin-top: 10px;
}

.text-output-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.text-output-header h5 {
  margin: 0;
  font-size: 12px;
  color: var(--ws-accent-soft);
}

.copy-btn {
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--border-color);
  border: none;
  color: #b0b0c0;
  font-size: 11px;
  cursor: pointer;
}

.copy-btn:hover {
  background: var(--border-color);
  color: var(--text-primary);
}

.text-content {
  max-height: 200px;
  overflow: auto;
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.redact-form {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metadata-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-readonly {
  padding: 8px;
  background: var(--bg-secondary);
  border-radius: 4px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  font-size: 11px;
}

.meta-label {
  color: var(--text-tertiary);
}

.meta-item span:last-child {
  color: var(--text-secondary);
}

.bookmark-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bookmark-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.bookmark-item:hover {
  background: var(--bg-secondary);
}

.bm-title {
  flex: 1;
  color: var(--text-secondary);
}

.bm-page {
  font-size: 10px;
  color: var(--text-tertiary);
}

.status-bar {
  padding: 6px 16px;
  font-size: 12px;
  text-align: center;
  flex-shrink: 0;
}

.status-bar.info {
  background: var(--bg-tertiary);
  color: var(--ws-accent);
}

.status-bar.success {
  background: var(--bg-tertiary);
  color: var(--ws-success);
}

.status-bar.error {
  background: var(--bg-tertiary);
  color: var(--ws-danger);
}
</style>
