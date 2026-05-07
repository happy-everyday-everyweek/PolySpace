<template>
  <div class="ppt-editor">
    <OnlyOfficeEditor
      v-if="useOnlyOffice"
      document-type="slide"
      :mode="editorMode"
      :doc-id="ooDocId"
      @fallback="useOnlyOffice = false"
      @ready="onOnlyOfficeReady"
      @saved="onOnlyOfficeSaved"
    />
    <template v-else>
    <div class="lo-menubar">
      <div class="menu-item" v-for="menu in pptMenus" :key="menu.label" @click="toggleMenu(menu.label)" @mouseenter="openMenuOnHover(menu.label)">
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
        <button v-for="tab in pptRibbonTabs" :key="tab.id" class="ribbon-tab" :class="{ active: activeRibbonTab === tab.id }" @click="activeRibbonTab = tab.id">{{ tab.label }}</button>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'home'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" @click="addSlide" title="New Slide">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
            </button>
            <button class="lo-btn" @click="duplicateSlide" title="Duplicate Slide">
              <svg width="16" height="16" viewBox="0 0 16 16"><rect x="4" y="4" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><rect x="2" y="2" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
            </button>
            <button class="lo-btn" @click="deleteSlide" :disabled="slides.length <= 1" title="Delete Slide">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8h10" stroke="currentColor" stroke-width="2" fill="none"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Slide</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" @click="undo" :disabled="!canUndo" title="Undo (Ctrl+Z)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8l4-4v3h4a3 3 0 010 6H9v-2h2a1 1 0 000-2H7v3L3 8z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" @click="redo" :disabled="!canRedo" title="Redo (Ctrl+Y)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M13 8l-4-4v3H5a3 3 0 000 6h2v-2H5a1 1 0 010-2h4v3l4-4z" fill="currentColor"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Edit</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <div class="dropdown-wrap">
              <button class="lo-btn" @click="showLayoutMenu = !showLayoutMenu" title="Layout">
                <svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2 6h12" stroke="currentColor" stroke-width="1"/></svg>
              </button>
              <div v-if="showLayoutMenu" class="dropdown-menu" @click.stop>
                <button v-for="lo in layouts" :key="lo.key" :class="['dropdown-item', { active: currentSlide?.layout === lo.key }]" @click="setLayout(lo.key); showLayoutMenu = false">
                  <span>{{ lo.label }}</span>
                </button>
              </div>
            </div>
            <div class="dropdown-wrap">
              <button class="lo-btn" @click="showThemeMenu = !showThemeMenu" title="Theme">
                <svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="5" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="8" cy="8" r="2" fill="currentColor"/></svg>
              </button>
              <div v-if="showThemeMenu" class="dropdown-menu theme-menu" @click.stop>
                <button v-for="th in themes" :key="th.key" :class="['dropdown-item theme-item', { active: currentTheme === th.key }]" @click="applyTheme(th.key as PptTheme); showThemeMenu = false">
                  <span class="theme-preview" :style="{ background: th.previewBg }">
                    <span class="theme-dot" :style="{ background: th.colors[0] }"></span>
                    <span class="theme-dot" :style="{ background: th.colors[1] }"></span>
                    <span class="theme-dot" :style="{ background: th.colors[2] }"></span>
                  </span>
                  <span>{{ th.label }}</span>
                </button>
              </div>
            </div>
          </div>
          <div class="ribbon-group-label">Layout</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="startSlideshow" title="Start Slideshow (F5)">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="9" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><polygon points="7,5 7,9 10,7" fill="currentColor"/><path d="M5 13h6" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Present</span>
            </button>
          </div>
          <div class="ribbon-group-label">Slideshow</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'insert'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="addTextBox" title="Text Box">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M4 7V4h8v3M7 12h2M8 4v8" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
              <span>Text</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="addImageElement" title="Image">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="5.5" r="1.5" fill="none" stroke="currentColor" stroke-width="1"/><path d="M2 11l3-3 2 2 3-4 4 5" fill="none" stroke="currentColor" stroke-width="1"/></svg>
              <span>Image</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="addShapeElement" title="Shape">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="3" y="3" width="10" height="10" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Shape</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="addTableElement" title="Table">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2 6h12M2 10h12M6 2v12" stroke="currentColor" stroke-width="1"/></svg>
              <span>Table</span>
            </button>
          </div>
          <div class="ribbon-group-label">Insert</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="importFromDocument" title="From Document">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M8 2v9M5 8l3 3 3-3" stroke="currentColor" stroke-width="1.2" fill="none"/><path d="M3 13h10" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Doc</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="importFromMindMap" title="From MindMap">
              <svg width="18" height="18" viewBox="0 0 16 16"><circle cx="8" cy="4" r="2" fill="none" stroke="currentColor" stroke-width="1"/><circle cx="4" cy="12" r="2" fill="none" stroke="currentColor" stroke-width="1"/><circle cx="12" cy="12" r="2" fill="none" stroke="currentColor" stroke-width="1"/><path d="M8 6L4 10M8 6l4 6" stroke="currentColor" stroke-width="1"/></svg>
              <span>MindMap</span>
            </button>
          </div>
          <div class="ribbon-group-label">Import</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'export'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="exportPresentation('pptx')" title="Export PPTX">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
              <span>PPTX</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="exportPresentation('pdf')" title="Export PDF">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
              <span>PDF</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="exportPresentation('html')" title="Export HTML">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z" fill="currentColor"/></svg>
              <span>HTML</span>
            </button>
          </div>
          <div class="ribbon-group-label">Export</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="savePresentation" title="Save">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17,21 17,13 7,13 7,21"/><polyline points="7,3 7,8 15,8"/></svg>
              <span>Save</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="openPresentation" title="Open">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
              <span>Open</span>
            </button>
          </div>
          <div class="ribbon-group-label">File</div>
        </div>
        <div class="ribbon-separator"></div>
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="sendToEmail" title="Send via Email">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 3h12a1 1 0 011 1v8a1 1 0 01-1 1H2a1 1 0 01-1-1V4a1 1 0 011-1zm0 1l6 4 6-4" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Email</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="sendToKnowledge" title="Save to Knowledge">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h5v5H2V2zm7 0h5v5H9V2zM2 9h5v5H2V9zm7 0h5v5H9V9z" fill="currentColor" opacity="0.7"/></svg>
              <span>Knowledge</span>
            </button>
          </div>
          <div class="ribbon-group-label">Send To</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'ai'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner ai-tools">
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('generate')" title="AI Generate Slides">
              <svg width="18" height="18" viewBox="0 0 16 16"><polygon points="8,1 10,6 15,6 11,9 12,14 8,11 4,14 5,9 1,6 6,6" fill="currentColor"/></svg>
              <span>Create</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('outline_to_slides')" title="AI Outline to Slides">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h3v3H2V2zm5 1h7v1H7V3zM2 7h3v3H2V7zm5 1h7v1H7V8zM2 12h3v3H2v-3zm5 1h7v1H7v-1z" fill="currentColor"/></svg>
              <span>Outline</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('improve')" title="AI Improve">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M12 1l3 3-9 9H3v-3l9-9z" fill="currentColor"/></svg>
              <span>Improve</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('design')" title="AI Design">
              <svg width="18" height="18" viewBox="0 0 16 16"><circle cx="8" cy="8" r="5" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="8" cy="8" r="2" fill="currentColor"/></svg>
              <span>Design</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('speaker_notes')" title="AI Speaker Notes">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="9" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M5 14h6" stroke="currentColor" stroke-width="1.2"/><path d="M8 11v3" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Notes</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('translate')" title="AI Translate">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M4 3h8v2H4V3zM2 7h5v1.5H2V7zm7 0h5v1.5H9V7z" fill="currentColor"/><path d="M6 2l4 12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
              <span>Translate</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="openAiPanel('more')" title="More AI Features">
              <svg width="18" height="18" viewBox="0 0 16 16"><circle cx="4" cy="8" r="1.5" fill="currentColor"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="12" cy="8" r="1.5" fill="currentColor"/></svg>
              <span>More</span>
            </button>
          </div>
          <div class="ribbon-group-label">AI Assistant</div>
        </div>
      </div>
    </div>

    <div class="ppt-content">
      <div class="slide-sidebar">
        <div
          v-for="(slide, index) in slides"
          :key="slide.id"
          :class="['slide-thumb', { active: currentSlideIndex === index }]"
          @click="currentSlideIndex = index"
          draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent
          @drop="onDrop($event, index)"
        >
          <span class="slide-number">{{ index + 1 }}</span>
          <div class="slide-thumb-preview" :style="thumbStyle(slide)">
            <h5>{{ slide.title || 'Untitled' }}</h5>
            <p v-if="slide.bullets?.length">{{ slide.bullets[0] }}</p>
          </div>
        </div>
      </div>

      <div class="slide-canvas-area">
        <div v-if="!slideshowMode" class="slide-canvas" :style="canvasStyle" @click="deselectElement">
          <template v-if="currentSlide?.layout === 'title'">
            <div class="layout-title-center">
              <h1 contenteditable="true" @input="onTitleEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.title }}</h1>
              <p v-if="currentSlide.bullets?.length" contenteditable="true" @input="onSubtitleEdit" class="editable-subtitle editable-element" @click.stop>{{ currentSlide.bullets[0] }}</p>
            </div>
          </template>
          <template v-else-if="currentSlide?.layout === 'title_content'">
            <h2 contenteditable="true" @input="onTitleEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.title }}</h2>
            <div class="slide-bullets-area">
              <div v-for="(bullet, bi) in currentSlide.bullets" :key="bi" class="bullet-item">
                <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                <span contenteditable="true" @input="onBulletEdit($event, bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
              </div>
            </div>
          </template>
          <template v-else-if="currentSlide?.layout === 'two_content'">
            <h2 contenteditable="true" @input="onTitleEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.title }}</h2>
            <div class="two-col-layout">
              <div class="col">
                <div v-for="(bullet, bi) in leftBullets" :key="'l'+bi" class="bullet-item">
                  <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                  <span contenteditable="true" @input="onBulletEdit($event, bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
                </div>
              </div>
              <div class="col">
                <div v-for="(bullet, bi) in rightBullets" :key="'r'+bi" class="bullet-item">
                  <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                  <span contenteditable="true" @input="onBulletEdit($event, leftBullets.length + bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="currentSlide?.layout === 'comparison'">
            <div class="comparison-layout">
              <div class="comparison-col">
                <h3 contenteditable="true" @input="onTitleEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.title }}</h3>
                <div v-for="(bullet, bi) in leftBullets" :key="'cl'+bi" class="bullet-item">
                  <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                  <span contenteditable="true" @input="onBulletEdit($event, bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
                </div>
              </div>
              <div class="comparison-divider"></div>
              <div class="comparison-col">
                <h3 v-if="currentSlide.titleRight" contenteditable="true" @input="onTitleRightEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.titleRight }}</h3>
                <div v-for="(bullet, bi) in rightBullets" :key="'cr'+bi" class="bullet-item">
                  <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                  <span contenteditable="true" @input="onBulletEdit($event, leftBullets.length + bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
                </div>
              </div>
            </div>
          </template>
          <template v-else-if="currentSlide?.layout === 'image'">
            <h2 contenteditable="true" @input="onTitleEdit" class="editable-title editable-element" @click.stop>{{ currentSlide.title }}</h2>
            <div class="image-placeholder" @click.stop>
              <div v-if="currentSlide.imageUrl" class="slide-image">
                <img :src="currentSlide.imageUrl" alt="slide image" />
              </div>
              <div v-else class="image-drop-zone" @click="triggerImageUpload">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                <span>Click to add image</span>
              </div>
            </div>
            <p v-if="currentSlide.bullets?.length" contenteditable="true" @input="onBulletEdit($event, 0)" class="editable-subtitle editable-element image-caption" @click.stop>{{ currentSlide.bullets[0] }}</p>
          </template>
          <template v-else-if="currentSlide?.layout === 'blank'">
            <div class="blank-layout">
              <div v-for="(bullet, bi) in currentSlide.bullets" :key="bi" class="bullet-item">
                <svg width="8" height="8" viewBox="0 0 8 8"><circle cx="4" cy="4" r="3" fill="currentColor"/></svg>
                <span contenteditable="true" @input="onBulletEdit($event, bi)" class="editable-bullet editable-element" @click.stop>{{ bullet }}</span>
              </div>
            </div>
          </template>
          <div v-for="el in currentSlide?.elements" :key="el.id" :class="['slide-element', { selected: selectedElementId === el.id }]" :style="elementStyle(el)" @click.stop="selectedElementId = el.id">
            <div v-if="el.type === 'text'" contenteditable="true" @input="onElementEdit($event, el.id)" class="element-text editable-element" @click.stop="selectedElementId = el.id">{{ el.content }}</div>
            <div v-else-if="el.type === 'image'" class="element-image">
              <img v-if="el.src" :src="el.src" alt="" />
              <div v-else class="element-image-placeholder">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
              </div>
            </div>
            <div v-else-if="el.type === 'shape'" class="element-shape" :style="shapeStyle(el)"></div>
            <div v-else-if="el.type === 'table'" class="element-table">
              <table>
                <tr v-for="(row, ri) in el.rows" :key="ri">
                  <td v-for="(cell, ci) in row" :key="ci" contenteditable="true" @input="onTableCellEdit($event, el.id, ri, ci)" @click.stop="selectedElementId = el.id">{{ cell }}</td>
                </tr>
              </table>
            </div>
          </div>
          <div class="slide-notes-area" v-if="currentSlide?.notes">
            <p class="speaker-note">{{ currentSlide.notes }}</p>
          </div>
        </div>
        <div v-else class="slideshow-view" :style="slideshowStyle" @click="nextSlide" @keydown.right="nextSlide" @keydown.left="prevSlide">
          <h1 class="slideshow-title">{{ currentSlide?.title }}</h1>
          <div class="slideshow-bullets" v-if="currentSlide?.bullets?.length && currentSlide?.layout !== 'title'">
            <div v-for="(bullet, bi) in currentSlide.bullets" :key="bi" class="slideshow-bullet">{{ bullet }}</div>
          </div>
          <div class="slideshow-counter">{{ currentSlideIndex + 1 }} / {{ slides.length }}</div>
          <button class="slideshow-exit" @click.stop="slideshowMode = false">ESC</button>
        </div>
      </div>

      <div v-if="aiPanelOpen" class="ai-panel">
        <div class="ai-panel-header">
          <h4>AI Assistant</h4>
          <button class="close-btn" @click="aiPanelOpen = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="ai-panel-tabs">
          <button v-for="tab in aiTabs" :key="tab.key" :class="['ai-tab', { active: aiActiveTab === tab.key }]" @click="aiActiveTab = tab.key">{{ tab.label }}</button>
        </div>
        <div class="ai-panel-content">
          <div v-if="aiActiveTab === 'create'" class="ai-section-content">
            <div class="ai-action-grid">
              <button class="ai-action-card" @click="aiAction('generate_slides')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12,2 15,9 22,9 16,14 18,21 12,17 6,21 8,14 2,9 9,9"/></svg>
                <span>Generate Slides</span>
                <small>Create from topic</small>
              </button>
              <button class="ai-action-card" @click="aiAction('outline_to_slides')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/></svg>
                <span>Outline to Slides</span>
                <small>Convert outline</small>
              </button>
              <button class="ai-action-card" @click="aiAction('expand_content')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/></svg>
                <span>Expand Content</span>
                <small>Add more detail</small>
              </button>
              <button class="ai-action-card" @click="aiAction('condense_content')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14h16M4 10h16"/></svg>
                <span>Condense</span>
                <small>Make concise</small>
              </button>
            </div>
          </div>
          <div v-if="aiActiveTab === 'improve'" class="ai-section-content">
            <div class="ai-action-grid">
              <button class="ai-action-card" @click="aiAction('improve_slide')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                <span>Improve Slide</span>
                <small>Better wording</small>
              </button>
              <button class="ai-action-card" @click="aiAction('add_speaker_notes')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2"/></svg>
                <span>Speaker Notes</span>
                <small>Auto generate</small>
              </button>
              <button class="ai-action-card" @click="aiAction('translate')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 8l6 6M4 14l6-6 2-3M2 5h12M7 2h1"/><path d="M22 22l-5-10-5 10M14 18h6"/></svg>
                <span>Translate</span>
                <small>Multi-language</small>
              </button>
              <button class="ai-action-card" @click="aiAction('tone_adjust')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3v18M3 12h18"/></svg>
                <span>Tone Adjust</span>
                <small>Formal/Casual</small>
              </button>
            </div>
          </div>
          <div v-if="aiActiveTab === 'design'" class="ai-section-content">
            <div class="ai-action-grid">
              <button class="ai-action-card" @click="aiAction('suggest_design')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3" fill="currentColor"/></svg>
                <span>Design Suggest</span>
                <small>Colors & fonts</small>
              </button>
              <button class="ai-action-card" @click="aiAction('smart_layout')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
                <span>Smart Layout</span>
                <small>Auto arrange</small>
              </button>
              <button class="ai-action-card" @click="aiAction('image_suggest')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                <span>Image Suggest</span>
                <small>Visual ideas</small>
              </button>
              <button class="ai-action-card" @click="aiAction('coaching')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <span>Present Coach</span>
                <small>Delivery tips</small>
              </button>
            </div>
          </div>
          <div v-if="aiActiveTab === 'analysis'" class="ai-section-content">
            <div class="ai-action-grid">
              <button class="ai-action-card" @click="aiAction('summarize_presentation')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span>Summarize</span>
                <small>Full summary</small>
              </button>
              <button class="ai-action-card" @click="aiAction('check_consistency')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                <span>Consistency</span>
                <small>Check style</small>
              </button>
              <button class="ai-action-card" @click="aiAction('audience_analysis')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
                <span>Audience</span>
                <small>Target analysis</small>
              </button>
              <button class="ai-action-card" @click="aiAction('timing_estimate')">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>
                <span>Time Estimate</span>
                <small>Duration calc</small>
              </button>
            </div>
          </div>
          <div v-if="aiLoading" class="ai-loading">
            <div class="spinner"></div>
            <span>AI is processing...</span>
          </div>
          <div v-else-if="aiResult" class="ai-result">
            <div v-if="aiResult.slides?.length" class="ai-section">
              <h5>Generated Slides</h5>
              <div v-for="(s, i) in aiResult.slides" :key="i" class="slide-item">
                <strong>{{ i + 1 }}. {{ s.title }}</strong>
                <ul v-if="s.bullets"><li v-for="(b, j) in s.bullets" :key="j">{{ b }}</li></ul>
              </div>
            </div>
            <div v-if="aiResult.improved_title" class="ai-section">
              <h5>Improved Content</h5>
              <div class="improved-content">
                <p><strong>Title:</strong> {{ aiResult.improved_title }}</p>
                <div v-if="aiResult.improved_bullets?.length">
                  <strong>Bullets:</strong>
                  <ul><li v-for="(b, i) in aiResult.improved_bullets" :key="i">{{ b }}</li></ul>
                </div>
                <div v-if="aiResult.suggestions?.length" class="ai-suggestions">
                  <strong>Suggestions:</strong>
                  <ul><li v-for="(s, i) in aiResult.suggestions" :key="i">{{ s }}</li></ul>
                </div>
              </div>
            </div>
            <div v-if="aiResult.notes" class="ai-section">
              <h5>Speaker Notes</h5>
              <p class="notes-text">{{ aiResult.notes }}</p>
            </div>
            <div v-if="aiResult.color_scheme || aiResult.font_suggestions || aiResult.layout_tips" class="ai-section">
              <h5>Design Suggestions</h5>
              <div v-if="aiResult.color_scheme" class="design-item"><strong>Colors:</strong> {{ aiResult.color_scheme }}</div>
              <div v-if="aiResult.font_suggestions" class="design-item"><strong>Fonts:</strong> {{ aiResult.font_suggestions }}</div>
              <div v-if="aiResult.layout_tips" class="design-item"><strong>Layout:</strong> {{ aiResult.layout_tips }}</div>
              <div v-if="aiResult.image_suggestions" class="design-item"><strong>Images:</strong> {{ aiResult.image_suggestions }}</div>
            </div>
            <div v-if="aiResult.summary" class="ai-section">
              <h5>Summary</h5>
              <p class="result-text">{{ aiResult.summary }}</p>
              <div v-if="aiResult.key_points?.length" class="key-points">
                <strong>Key Points:</strong>
                <ul><li v-for="(p, i) in aiResult.key_points" :key="i">{{ p }}</li></ul>
              </div>
              <div v-if="aiResult.duration_estimate" class="duration-est">
                <strong>Estimated Duration:</strong> {{ aiResult.duration_estimate }}
              </div>
            </div>
            <div v-if="aiResult.translated" class="ai-section">
              <h5>Translation</h5>
              <p class="result-text">{{ aiResult.translated }}</p>
            </div>
            <div v-if="aiResult.adjusted" class="ai-section">
              <h5>Tone Adjusted</h5>
              <p class="result-text">{{ aiResult.adjusted }}</p>
              <div v-if="aiResult.tone_description" class="tone-desc">{{ aiResult.tone_description }}</div>
            </div>
            <div v-if="aiResult.coaching_tips" class="ai-section">
              <h5>Presentation Coaching</h5>
              <ul class="coaching-list"><li v-for="(tip, i) in aiResult.coaching_tips" :key="i">{{ tip }}</li></ul>
            </div>
            <div v-if="aiResult.consistency_issues" class="ai-section">
              <h5>Consistency Check</h5>
              <ul class="consistency-list"><li v-for="(issue, i) in aiResult.consistency_issues" :key="i" :class="issue.severity">{{ issue.description }}</li></ul>
            </div>
            <div v-if="aiResult.audience_insights" class="ai-section">
              <h5>Audience Analysis</h5>
              <p class="result-text">{{ aiResult.audience_insights }}</p>
            </div>
            <div v-if="aiResult.result && !aiResult.slides && !aiResult.improved_title && !aiResult.notes && !aiResult.summary && !aiResult.translated && !aiResult.adjusted && !aiResult.coaching_tips && !aiResult.consistency_issues && !aiResult.audience_insights" class="ai-section">
              <pre class="text-result">{{ aiResult.result }}</pre>
            </div>
            <div class="ai-actions">
              <button class="apply-btn" @click="applyAIResult">Apply</button>
              <button class="discard-btn" @click="aiResult = null">Discard</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="ppt-footer">
      <span>Slide {{ currentSlideIndex + 1 }} / {{ slides.length }}</span>
      <div class="footer-info" v-if="currentSlide?.layout">
        <span class="layout-badge">{{ currentSlide.layout.replace('_', ' ') }}</span>
      </div>
      <div class="footer-actions">
        <button class="footer-btn" @click="prevSlide" :disabled="currentSlideIndex === 0">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        </button>
        <button class="footer-btn" @click="nextSlide" :disabled="currentSlideIndex === slides.length - 1">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
        </button>
      </div>
    </div>

    <input type="file" ref="imageInput" accept="image/*" style="display:none" @change="onImageSelected" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import api from '../../utils/api'
import OnlyOfficeEditor from './OnlyOfficeEditor.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import { useAppSettings } from '@/composables/useAppSettings'

interface MenuItem {
  label: string
  shortcut?: string
  action?: () => void
  disabled?: boolean
}

type PptTheme = 'dark' | 'light' | 'blue' | 'green' | 'warm' | 'purple' | 'red'

interface SlideElement {
  id: string
  type: 'text' | 'image' | 'shape' | 'table'
  x: number
  y: number
  width: number
  height: number
  content?: string
  src?: string
  shapeType?: 'rect' | 'circle' | 'arrow'
  fillColor?: string
  strokeColor?: string
  rows?: string[][]
  fontSize?: number
  fontWeight?: string
  color?: string
  textAlign?: string
}

interface Slide {
  id: string
  title: string
  titleRight?: string
  bullets: string[]
  notes: string
  layout: string
  background: string
  imageUrl?: string
  elements: SlideElement[]
  transition?: string
}

const layouts = [
  { key: 'title', label: 'Title Slide' },
  { key: 'title_content', label: 'Title + Content' },
  { key: 'two_content', label: 'Two Content' },
  { key: 'comparison', label: 'Comparison' },
  { key: 'image', label: 'Image' },
  { key: 'blank', label: 'Blank' },
]

const themes = [
  { key: 'dark', label: 'Dark', previewBg: 'var(--bg-secondary)', colors: ['var(--ws-accent)', 'var(--ws-accent-soft)', 'var(--border-color)'] },
  { key: 'light', label: 'Light', previewBg: '#f5f5f5', colors: ['#333333', 'var(--text-tertiary)666', 'var(--text-primary)'] },
  { key: 'blue', label: 'Ocean Blue', previewBg: '#0a1628', colors: ['#2196F3', '#64B5F6', '#0D47A1'] },
  { key: 'green', label: 'Forest', previewBg: '#0a1f0a', colors: ['var(--ws-success)', '#81C784', '#1B5E20'] },
  { key: 'warm', label: 'Warm', previewBg: '#2a1a0a', colors: ['var(--ws-warning)', '#FFB74D', '#E65100'] },
  { key: 'purple', label: 'Elegant', previewBg: '#1a0a2a', colors: ['#9C27B0', '#CE93D8', '#4A148C'] },
  { key: 'red', label: 'Bold', previewBg: '#2a0a0a', colors: ['#F44336', '#EF9A9A', '#B71C1C'] },
]

const themeMap: Record<string, { bg: string; titleColor: string; textColor: string; accentColor: string }> = {
  dark: { bg: 'var(--bg-secondary)', titleColor: '#ffffff', textColor: 'var(--text-secondary)', accentColor: 'var(--ws-accent)' },
  light: { bg: '#f5f5f5', titleColor: '#1a1a1a', textColor: '#444444', accentColor: '#2196F3' },
  blue: { bg: '#0a1628', titleColor: '#e3f2fd', textColor: '#bbdefb', accentColor: '#2196F3' },
  green: { bg: '#0a1f0a', titleColor: '#e8f5e9', textColor: '#c8e6c9', accentColor: 'var(--ws-success)' },
  warm: { bg: '#2a1a0a', titleColor: '#fff3e0', textColor: '#ffe0b2', accentColor: 'var(--ws-warning)' },
  purple: { bg: '#1a0a2a', titleColor: '#f3e5f5', textColor: '#e1bee7', accentColor: '#9C27B0' },
  red: { bg: '#2a0a0a', titleColor: '#ffebee', textColor: '#ffcdd2', accentColor: '#F44336' },
}

const aiTabs = [
  { key: 'create', label: 'Create' },
  { key: 'improve', label: 'Improve' },
  { key: 'design', label: 'Design' },
  { key: 'analysis', label: 'Analysis' },
]

const slides = ref<Slide[]>([
  { id: '1', title: 'Welcome', bullets: ['Introduction', 'Overview'], notes: '', layout: 'title', background: 'var(--bg-secondary)', elements: [] }
])
const currentSlideIndex = ref(0)
const slideshowMode = ref(false)
const currentTheme = ref<PptTheme>(useAppSettings('ppt').settings.value.theme || 'dark')
const selectedElementId = ref<string | null>(null)
const showLayoutMenu = ref(false)
const showThemeMenu = ref(false)
const showExportMenu = ref(false)
const showImportMenu = ref(false)
const showSendMenu = ref(false)
const aiPanelOpen = ref(false)
const aiActiveTab = ref('create')
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')
const activeRibbonTab = ref('home')

const useOnlyOffice = ref(true)
const ooDocId = ref<string | null>(null)
const editorMode = ref('edit')

function onOnlyOfficeReady() {}
function onOnlyOfficeSaved() {}
const activeMenu = ref('')

const pptRibbonTabs = [
  { id: 'home', label: 'Home' },
  { id: 'insert', label: 'Insert' },
  { id: 'export', label: 'Export' },
  { id: 'ai', label: 'AI' },
]

const pptMenus = computed(() => [
  {
    label: 'File',
    items: [
      { label: 'Save', shortcut: 'Ctrl+S', action: savePresentation },
      { label: 'Open', shortcut: 'Ctrl+O', action: openPresentation },
      { label: 'Export PPTX', action: () => exportPresentation('pptx') },
      { label: 'Export PDF', action: () => exportPresentation('pdf') },
      { label: 'Export HTML', action: () => exportPresentation('html') },
    ] as MenuItem[],
  },
  {
    label: 'Edit',
    items: [
      { label: 'Undo', shortcut: 'Ctrl+Z', action: undo, disabled: !canUndo.value },
      { label: 'Redo', shortcut: 'Ctrl+Y', action: redo, disabled: !canRedo.value },
    ] as MenuItem[],
  },
  {
    label: 'Insert',
    items: [
      { label: 'New Slide', action: addSlide },
      { label: 'Text Box', action: addTextBox },
      { label: 'Image', action: addImageElement },
      { label: 'Shape', action: addShapeElement },
      { label: 'Table', action: addTableElement },
    ] as MenuItem[],
  },
  {
    label: 'Slide',
    items: [
      { label: 'New Slide', action: addSlide },
      { label: 'Duplicate Slide', action: duplicateSlide },
      { label: 'Delete Slide', action: deleteSlide, disabled: slides.value.length <= 1 },
      { label: 'Start Slideshow', shortcut: 'F5', action: startSlideshow },
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
      { label: 'About PolySpace Impress', disabled: true },
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
const dragIndex = ref<number | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const pendingImageTarget = ref<'slide' | string>('slide')

const undoStack = ref<string[]>([])
const redoStack = ref<string[]>([])
const canUndo = computed(() => undoStack.value.length > 0)
const canRedo = computed(() => redoStack.value.length > 0)

const { saveDoc, loadDoc } = useDocumentPersistence('ppt')

const currentSlide = computed(() => slides.value[currentSlideIndex.value])
const leftBullets = computed(() => {
  if (!currentSlide.value?.bullets) return []
  const mid = Math.ceil(currentSlide.value.bullets.length / 2)
  return currentSlide.value.bullets.slice(0, mid)
})
const rightBullets = computed(() => {
  if (!currentSlide.value?.bullets) return []
  const mid = Math.ceil(currentSlide.value.bullets.length / 2)
  return currentSlide.value.bullets.slice(mid)
})

const canvasStyle = computed(() => {
  const th = themeMap[currentTheme.value] || themeMap.dark
  return { background: currentSlide.value?.background || th.bg }
})

const slideshowStyle = computed(() => {
  const th = themeMap[currentTheme.value] || themeMap.dark
  return { background: currentSlide.value?.background || th.bg }
})

function thumbStyle(slide: Slide) {
  return { background: slide.background || 'var(--bg-secondary)' }
}

function elementStyle(el: SlideElement) {
  return {
    left: el.x + 'px',
    top: el.y + 'px',
    width: el.width + 'px',
    height: el.height + 'px',
  }
}

function shapeStyle(el: SlideElement) {
  const base: Record<string, string> = {
    width: '100%',
    height: '100%',
    backgroundColor: el.fillColor || 'rgba(124,111,247,0.2)',
    border: `2px solid ${el.strokeColor || 'var(--ws-accent)'}`,
  }
  if (el.shapeType === 'circle') {
    base.borderRadius = '50%'
  } else if (el.shapeType === 'arrow') {
    base.clipPath = 'polygon(0 35%, 65% 35%, 65% 0, 100% 50%, 65% 100%, 65% 65%, 0 65%)'
  }
  return base
}

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveDoc('default', { slides: slides.value, theme: currentTheme.value, updatedAt: Date.now() })
  }, 1500)
}

function pushUndo() {
  undoStack.value.push(JSON.stringify(slides.value))
  if (undoStack.value.length > 50) undoStack.value.shift()
  redoStack.value = []
}

function undo() {
  if (!canUndo.value) return
  redoStack.value.push(JSON.stringify(slides.value))
  const prev = JSON.parse(undoStack.value.pop()!)
  slides.value = prev
}

function redo() {
  if (!canRedo.value) return
  undoStack.value.push(JSON.stringify(slides.value))
  const next = JSON.parse(redoStack.value.pop()!)
  slides.value = next
}

watch(slides, debouncedSave, { deep: true })

function addSlide() {
  pushUndo()
  const th = themeMap[currentTheme.value] || themeMap.dark
  slides.value.push({
    id: Date.now().toString(),
    title: 'New Slide',
    bullets: [],
    notes: '',
    layout: 'title_content',
    background: th.bg,
    elements: [],
  })
  currentSlideIndex.value = slides.value.length - 1
}

function deleteSlide() {
  if (slides.value.length <= 1) return
  pushUndo()
  slides.value.splice(currentSlideIndex.value, 1)
  if (currentSlideIndex.value >= slides.value.length) currentSlideIndex.value = slides.value.length - 1
}

function duplicateSlide() {
  const src = slides.value[currentSlideIndex.value]
  if (!src) return
  pushUndo()
  const copy: Slide = { ...src, id: Date.now().toString(), bullets: [...src.bullets], notes: src.notes, elements: src.elements.map(e => ({ ...e, id: Date.now().toString() + Math.random().toString(36).slice(2, 6) })) }
  slides.value.splice(currentSlideIndex.value + 1, 0, copy)
  currentSlideIndex.value += 1
}

function addTextBox() {
  if (!currentSlide.value) return
  pushUndo()
  currentSlide.value.bullets.push('New text point')
}

function addImageElement() {
  if (!currentSlide.value) return
  pushUndo()
  currentSlide.value.elements.push({
    id: Date.now().toString(),
    type: 'image',
    x: 50, y: 100, width: 200, height: 150,
    src: '',
  })
}

function addShapeElement() {
  if (!currentSlide.value) return
  pushUndo()
  currentSlide.value.elements.push({
    id: Date.now().toString(),
    type: 'shape',
    x: 100, y: 100, width: 120, height: 80,
    shapeType: 'rect',
    fillColor: 'rgba(124,111,247,0.2)',
    strokeColor: 'var(--ws-accent)',
  })
}

function addTableElement() {
  if (!currentSlide.value) return
  pushUndo()
  const rows = [['Header 1', 'Header 2', 'Header 3'], ['Cell', 'Cell', 'Cell'], ['Cell', 'Cell', 'Cell']]
  currentSlide.value.elements.push({
    id: Date.now().toString(),
    type: 'table',
    x: 50, y: 150, width: 600, height: 150,
    rows,
  })
}

function triggerImageUpload() {
  pendingImageTarget.value = 'slide'
  imageInput.value?.click()
}

function onImageSelected(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const dataUrl = ev.target?.result as string
    if (pendingImageTarget.value === 'slide' && currentSlide.value) {
      pushUndo()
      currentSlide.value.imageUrl = dataUrl
    } else if (typeof pendingImageTarget.value === 'string') {
      const el = currentSlide.value?.elements.find(e => e.id === pendingImageTarget.value)
      if (el) { pushUndo(); el.src = dataUrl }
    }
  }
  reader.readAsDataURL(file)
}

function setLayout(layout: string) {
  if (!currentSlide.value) return
  pushUndo()
  currentSlide.value.layout = layout
}

function applyTheme(themeKey: PptTheme) {
  pushUndo()
  currentTheme.value = themeKey
  const th = themeMap[themeKey]
  if (th) {
    slides.value.forEach(s => { s.background = th.bg })
  }
}

function deselectElement() {
  selectedElementId.value = null
}

function onTitleEdit(e: Event) {
  if (currentSlide.value) currentSlide.value.title = (e.target as HTMLElement).innerText
}

function onTitleRightEdit(e: Event) {
  if (currentSlide.value) currentSlide.value.titleRight = (e.target as HTMLElement).innerText
}

function onSubtitleEdit(e: Event) {
  if (currentSlide.value) {
    if (!currentSlide.value.bullets.length) currentSlide.value.bullets.push('')
    currentSlide.value.bullets[0] = (e.target as HTMLElement).innerText
  }
}

function onBulletEdit(e: Event, index: number) {
  if (currentSlide.value) currentSlide.value.bullets[index] = (e.target as HTMLElement).innerText
}

function onElementEdit(e: Event, elId: string) {
  const el = currentSlide.value?.elements.find(e => e.id === elId)
  if (el && el.type === 'text') el.content = (e.target as HTMLElement).innerText
}

function onTableCellEdit(e: Event, elId: string, ri: number, ci: number) {
  const el = currentSlide.value?.elements.find(e => e.id === elId)
  if (el && el.type === 'table' && el.rows) {
    el.rows[ri][ci] = (e.target as HTMLElement).innerText
  }
}

function prevSlide() { if (currentSlideIndex.value > 0) currentSlideIndex.value-- }
function nextSlide() { if (currentSlideIndex.value < slides.value.length - 1) currentSlideIndex.value++ }

function startSlideshow() {
  slideshowMode.value = true
  currentSlideIndex.value = 0
}

function onDragStart(_e: DragEvent, index: number) { dragIndex.value = index }
function onDrop(_e: DragEvent, targetIndex: number) {
  if (dragIndex.value === null || dragIndex.value === targetIndex) return
  pushUndo()
  const item = slides.value.splice(dragIndex.value, 1)[0]
  slides.value.splice(targetIndex, 0, item)
  currentSlideIndex.value = targetIndex
  dragIndex.value = null
}

function openAiPanel(tab: string) {
  aiPanelOpen.value = true
  aiActiveTab.value = tab
  aiResult.value = null
}

async function aiAction(action: string) {
  if (!currentSlide.value && !['generate_slides', 'outline_to_slides'].includes(action)) return
  aiLoading.value = true
  aiResult.value = null
  aiCurrentAction.value = action
  try {
    let params: Record<string, any> = {}
    switch (action) {
      case 'generate_slides':
        params = { topic: 'General presentation', slide_count: 8 }
        break
      case 'outline_to_slides':
        params = { outline: currentSlide.value?.title || 'Presentation outline', current_content: slides.value.map(s => ({ title: s.title, bullets: s.bullets })) }
        break
      case 'improve_slide':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, slide_index: currentSlideIndex.value }
        break
      case 'expand_content':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, slide_index: currentSlideIndex.value }
        break
      case 'condense_content':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, slide_index: currentSlideIndex.value }
        break
      case 'add_speaker_notes':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, slide_index: currentSlideIndex.value }
        break
      case 'translate':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, target_lang: 'en' }
        break
      case 'tone_adjust':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, tone: 'professional' }
        break
      case 'suggest_design':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets })), total_slides: slides.value.length }
        break
      case 'smart_layout':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets, layout: s.layout })), total_slides: slides.value.length }
        break
      case 'image_suggest':
        params = { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets, slide_index: currentSlideIndex.value }
        break
      case 'coaching':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets, notes: s.notes })), total_slides: slides.value.length }
        break
      case 'summarize_presentation':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets })) }
        break
      case 'check_consistency':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets, layout: s.layout })) }
        break
      case 'audience_analysis':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets })), total_slides: slides.value.length }
        break
      case 'timing_estimate':
        params = { slides: slides.value.map(s => ({ title: s.title, bullets: s.bullets, notes: s.notes })), total_slides: slides.value.length }
        break
      default:
        params = { slide: { title: currentSlide.value!.title, bullets: currentSlide.value!.bullets } }
    }
    const res = await api.post('/ai/workspace/ppt/assist', { action, params })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'AI request failed. Please try again.' }
  } finally {
    aiLoading.value = false
  }
}

function applyAIResult() {
  const data = aiResult.value
  if (!data) return
  pushUndo()
  if (data.slides?.length) {
    const th = themeMap[currentTheme.value] || themeMap.dark
    slides.value = data.slides.map((s: any) => ({
      id: Date.now().toString() + Math.random().toString(36).slice(2, 6),
      title: s.title || 'Untitled',
      bullets: s.bullets || [],
      notes: s.notes || '',
      layout: s.layout_suggestion || s.layout || 'title_content',
      background: th.bg,
      elements: [],
    }))
    currentSlideIndex.value = 0
  } else if (data.improved_title && currentSlide.value) {
    currentSlide.value.title = data.improved_title
    if (data.improved_bullets) currentSlide.value.bullets = data.improved_bullets
  } else if (data.notes && currentSlide.value) {
    currentSlide.value.notes = data.notes
  } else if (data.translated && currentSlide.value) {
    currentSlide.value.title = data.translated
  } else if (data.adjusted && currentSlide.value) {
    currentSlide.value.title = data.adjusted
    if (data.adjusted_bullets) currentSlide.value.bullets = data.adjusted_bullets
  } else if (data.recommended_layouts && currentSlide.value) {
    const rec = data.recommended_layouts[currentSlideIndex.value]
    if (rec) currentSlide.value.layout = rec
  }
  aiResult.value = null
}

function exportPresentation(format: string) {
  const th = themeMap[currentTheme.value] || themeMap.dark
  if (format === 'html') {
    const html = generateHtmlExport(th)
    const blob = new Blob([html], { type: 'text/html' })
    downloadBlob(blob, 'presentation.html')
  } else if (format === 'pdf') {
    const html = generateHtmlExport(th)
    const printWin = window.open('', '_blank')
    if (printWin) {
      printWin.document.write(html)
      printWin.document.close()
      printWin.print()
    }
  } else if (format === 'images') {
    console.warn('Image export requires server-side rendering. Use Export HTML and screenshot instead.')
  }
}

function generateHtmlExport(th: { bg: string; titleColor: string; textColor: string; accentColor: string }): string {
  const slideHtml = slides.value.map((s, i) => `
    <div class="slide" style="background:${s.background || th.bg};width:960px;height:540px;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:60px;page-break-after:always;box-sizing:border-box;">
      <h1 style="color:${th.titleColor};font-size:36px;margin-bottom:24px;text-align:center;">${s.title}</h1>
      ${s.bullets.length ? `<ul style="color:${th.textColor};font-size:20px;line-height:2;list-style:none;padding:0;">${s.bullets.map(b => `<li style="margin-bottom:8px;">&#8226; ${b}</li>`).join('')}</ul>` : ''}
      <div style="position:absolute;bottom:20px;right:30px;color:${th.accentColor};font-size:14px;">${i + 1} / ${slides.value.length}</div>
    </div>
  `).join('')
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Presentation</title><style>body{margin:0;padding:0;font-family:system-ui,-apple-system,sans-serif;}@media print{.slide{break-after:page;}}</style></head><body>${slideHtml}</body></html>`
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

async function importFromDocument() {
  try {
    const { loadDoc } = useDocumentPersistence('document')
    const doc = await loadDoc('default')
    if (doc?.content) {
      pushUndo()
      const th = themeMap[currentTheme.value] || themeMap.dark
      const paragraphs = (doc.content as string).split('\n').filter((p: string) => p.trim())
      const newSlides: Slide[] = []
      for (let i = 0; i < paragraphs.length; i += 3) {
        newSlides.push({
          id: Date.now().toString() + i,
          title: paragraphs[i]?.slice(0, 60) || 'Slide',
          bullets: paragraphs.slice(i + 1, i + 3).filter(Boolean).map((p: string) => p.slice(0, 100)),
          notes: '',
          layout: 'title_content',
          background: th.bg,
          elements: [],
        })
      }
      if (newSlides.length) {
        slides.value = newSlides
        currentSlideIndex.value = 0
      }
    }
  } catch { /* no document data */ }
}

async function importFromMindMap() {
  try {
    const { loadDoc } = useDocumentPersistence('mindmap')
    const doc = await loadDoc('default')
    if (doc?.root) {
      pushUndo()
      const th = themeMap[currentTheme.value] || themeMap.dark
      const root = doc.root
      const newSlides: Slide[] = [{
        id: Date.now().toString() + '0',
        title: root.text || 'MindMap',
        bullets: (root.children || []).map((c: any) => c.text || ''),
        notes: '',
        layout: 'title_content',
        background: th.bg,
        elements: [],
      }]
      if (root.children) {
        for (const child of root.children) {
          newSlides.push({
            id: Date.now().toString() + Math.random().toString(36).slice(2, 6),
            title: child.text || 'Topic',
            bullets: (child.children || []).map((c: any) => c.text || ''),
            notes: '',
            layout: 'title_content',
            background: th.bg,
            elements: [],
          })
        }
      }
      slides.value = newSlides
      currentSlideIndex.value = 0
    }
  } catch { /* no mindmap data */ }
}

function sendToEmail() {
  const subject = encodeURIComponent('Presentation: ' + (slides.value[0]?.title || 'Untitled'))
  const body = encodeURIComponent(slides.value.map((s, i) => `Slide ${i + 1}: ${s.title}\n${s.bullets.join('\n')}`).join('\n\n'))
  window.open(`mailto:?subject=${subject}&body=${body}`)
}

function sendToKnowledge() {
  const content = slides.value.map((s, i) => `## Slide ${i + 1}: ${s.title}\n${s.bullets.map(b => '- ' + b).join('\n')}${s.notes ? '\n\nNotes: ' + s.notes : ''}`).join('\n\n')
  saveDoc('knowledge_import_' + Date.now(), { content, source: 'ppt', title: slides.value[0]?.title || 'Presentation', updatedAt: Date.now() })
}

async function savePresentation() {
  try {
    const content = JSON.stringify({ slides: slides.value, theme: currentTheme.value })
    await api.post('/workspace/documents', {
      title: slides.value[0]?.title || 'Untitled Presentation',
      doc_type: 'presentation',
      content,
      metadata: { slideCount: slides.value.length, theme: currentTheme.value },
    })
    await api.post('/files/write', {
      path: `${slides.value[0]?.title || 'presentation'}.json`,
      content,
      subdir: 'presentations',
    })
  } catch (e) {
    console.error('Failed to save presentation:', e)
  }
}

async function openPresentation() {
  try {
    const res = await api.get('/workspace/documents', { params: { doc_type: 'presentation' } })
    const docs = res.data?.documents || res.data || []
    if (!docs.length) return
    const latest = docs[0]
    if (latest?.content) {
      const data = typeof latest.content === 'string' ? JSON.parse(latest.content) : latest.content
      if (data.slides) {
        pushUndo()
        slides.value = data.slides.map((s: any) => ({
          ...s,
          elements: s.elements || [],
          titleRight: s.titleRight || '',
          imageUrl: s.imageUrl || '',
          transition: s.transition || '',
        }))
        if (data.theme) currentTheme.value = data.theme
        currentSlideIndex.value = 0
      }
    }
  } catch (e) {
    console.error('Failed to open presentation:', e)
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (slideshowMode.value) {
    if (e.key === 'Escape') slideshowMode.value = false
    else if (e.key === 'ArrowRight' || e.key === ' ') nextSlide()
    else if (e.key === 'ArrowLeft') prevSlide()
  } else if (e.key === 'F5') {
    e.preventDefault()
    startSlideshow()
  } else if (e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    undo()
  } else if (e.ctrlKey && e.key === 'y') {
    e.preventDefault()
    redo()
  }
}

function closeAllMenus() {
  showLayoutMenu.value = false
  showThemeMenu.value = false
  showExportMenu.value = false
  showImportMenu.value = false
  showSendMenu.value = false
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  window.addEventListener('click', closeAllMenus)
  const saved = await loadDoc('default')
  if (saved?.slides) {
    slides.value = (saved.slides as any[]).map(s => ({
      ...s,
      elements: s.elements || [],
      titleRight: s.titleRight || '',
      imageUrl: s.imageUrl || '',
      transition: s.transition || '',
    }))
  }
  if (saved?.theme) currentTheme.value = saved.theme
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('click', closeAllMenus)
  if (saveTimer) clearTimeout(saveTimer)
})
</script>

<style scoped>
.ppt-editor { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); color: var(--text-primary); }
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
.lo-btn { display: flex; align-items: center; justify-content: center; gap: 2px; padding: 4px 5px; border-radius: 3px; color: var(--text-secondary); cursor: pointer; background: none; border: none; transition: all 0.12s; position: relative; }
.lo-btn:hover:not(:disabled) { background: var(--border-color); color: var(--text-color); }
.lo-btn.active { background: var(--primary-light); color: var(--primary-color); }
.lo-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.lo-btn-lg { flex-direction: column; padding: 6px 10px; gap: 2px; min-width: 48px; }
.lo-btn-lg span { font-size: 10px; white-space: nowrap; }
.ai-btn { color: var(--primary-color); }
.ai-btn:hover:not(:disabled) { background: var(--primary-light); color: var(--primary-color); }
.ai-tools { gap: 4px; }
.dropdown-wrap { position: relative; }
.dropdown-menu { position: absolute; top: 100%; left: 0; background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 4px; padding: 4px; min-width: 180px; z-index: 100; box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.dropdown-item { display: flex; align-items: center; gap: 8px; width: 100%; padding: 8px 12px; border: none; background: transparent; color: var(--text-secondary); font-size: 12px; cursor: pointer; border-radius: 4px; text-align: left; }
.dropdown-item:hover { background: var(--bg-tertiary); color: var(--text-primary); }
.dropdown-item.active { background: var(--primary-light); color: var(--primary-color); }
.theme-menu { min-width: 220px; }
.theme-item { gap: 10px; }
.theme-preview { width: 36px; height: 24px; border-radius: 4px; display: flex; gap: 3px; align-items: center; justify-content: center; padding: 2px; border: 1px solid var(--border-color); }
.theme-dot { width: 8px; height: 8px; border-radius: 50%; }
.ppt-content { flex: 1; display: flex; overflow: hidden; }
.slide-sidebar { width: 140px; padding: 8px; border-right: 1px solid var(--border-color); overflow-y: auto; background: var(--bg-primary); }
.slide-thumb { padding: 8px; border-radius: var(--radius-md); border: 2px solid transparent; margin-bottom: 6px; cursor: pointer; transition: all 0.15s; background: var(--bg-secondary); }
.slide-thumb:hover { border-color: var(--border-color); }
.slide-thumb.active { border-color: var(--ws-accent); background: var(--ws-accent-light); }
.slide-number { font-size: 10px; color: var(--text-tertiary); }
.slide-thumb-preview { margin-top: 4px; }
.slide-thumb-preview h5 { font-size: 11px; color: var(--text-secondary); margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.slide-thumb-preview p { font-size: 9px; color: var(--text-tertiary); margin: 2px 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.slide-canvas-area { flex: 1; display: flex; align-items: center; justify-content: center; padding: 24px; background: var(--bg-tertiary); overflow: auto; }
.slide-canvas { width: 720px; height: 480px; border-radius: 8px; padding: 40px; display: flex; flex-direction: column; box-shadow: 0 4px 24px rgba(0,0,0,0.4); position: relative; min-width: 720px; }
.editable-title { font-size: 28px; font-weight: 700; color: #fff; outline: none; border: none; background: transparent; min-height: 40px; }
.editable-title:focus { border-bottom: 2px solid var(--ws-accent); }
.editable-subtitle { font-size: 18px; color: var(--text-secondary); outline: none; background: transparent; border: none; text-align: center; }
.editable-subtitle:focus { border-bottom: 1px solid var(--ws-accent); }
.layout-title-center { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.layout-title-center .editable-title { text-align: center; font-size: 36px; }
.slide-bullets-area { flex: 1; margin-top: 16px; }
.bullet-item { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; color: var(--text-secondary); }
.bullet-item svg { margin-top: 5px; color: var(--ws-accent); flex-shrink: 0; }
.editable-bullet { font-size: 16px; line-height: 1.6; outline: none; flex: 1; }
.editable-bullet:focus { border-bottom: 1px solid var(--ws-accent); }
.two-col-layout { display: flex; gap: 24px; flex: 1; margin-top: 16px; }
.two-col-layout .col { flex: 1; }
.comparison-layout { display: flex; gap: 0; flex: 1; }
.comparison-col { flex: 1; padding: 16px; }
.comparison-col .editable-title { font-size: 20px; }
.comparison-divider { width: 1px; background: rgba(255,255,255,0.15); margin: 0 8px; }
.image-placeholder { flex: 1; display: flex; align-items: center; justify-content: center; margin: 16px 0; border: 2px dashed var(--border-color); border-radius: 8px; min-height: 200px; overflow: hidden; }
.slide-image { width: 100%; height: 100%; }
.slide-image img { max-width: 100%; max-height: 280px; object-fit: contain; }
.image-drop-zone { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-tertiary); cursor: pointer; padding: 40px; }
.image-drop-zone:hover { color: var(--ws-accent-soft); border-color: var(--ws-accent); }
.image-caption { text-align: center; font-size: 14px; color: var(--text-tertiary); margin-top: 8px; }
.blank-layout { flex: 1; }
.slide-element { position: absolute; cursor: move; border: 2px solid transparent; border-radius: 4px; }
.slide-element:hover { border-color: rgba(124,111,247,0.4); }
.slide-element.selected { border-color: var(--ws-accent); box-shadow: 0 0 0 2px var(--ws-accent-light); }
.element-text { width: 100%; height: 100%; outline: none; font-size: 14px; color: var(--text-primary); padding: 4px; overflow: hidden; }
.element-image { width: 100%; height: 100%; }
.element-image img { width: 100%; height: 100%; object-fit: contain; }
.element-image-placeholder { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: var(--bg-secondary); border-radius: 4px; color: var(--text-tertiary); }
.element-shape { width: 100%; height: 100%; }
.element-table { width: 100%; height: 100%; overflow: auto; }
.element-table table { width: 100%; border-collapse: collapse; }
.element-table td { border: 1px solid var(--border-color); padding: 6px 8px; font-size: 12px; color: var(--text-secondary); outline: none; min-width: 60px; }
.element-table td:focus { background: var(--bg-tertiary); }
.slide-notes-area { border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: auto; }
.speaker-note { font-size: 12px; color: var(--text-tertiary); font-style: italic; }
.slideshow-view { width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px; cursor: pointer; position: relative; }
.slideshow-title { font-size: 42px; font-weight: 700; color: #fff; text-align: center; margin: 0 0 32px; }
.slideshow-bullets { display: flex; flex-direction: column; gap: 16px; }
.slideshow-bullet { font-size: 22px; color: var(--text-secondary); }
.slideshow-counter { position: absolute; bottom: 20px; right: 30px; font-size: 14px; color: var(--text-tertiary); }
.slideshow-exit { position: absolute; top: 20px; right: 30px; background: none; border: 1px solid var(--border-color); color: var(--text-tertiary); padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; }
.ppt-footer { display: flex; align-items: center; justify-content: space-between; padding: 8px 16px; border-top: 1px solid var(--border-color); background: var(--bg-secondary); font-size: 12px; color: var(--text-tertiary); }
.footer-info { display: flex; gap: 8px; }
.layout-badge { padding: 2px 8px; background: var(--bg-tertiary); border-radius: 3px; font-size: 10px; color: var(--ws-accent-soft); text-transform: capitalize; }
.footer-actions { display: flex; gap: 4px; }
.footer-btn { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: transparent; border: 1px solid var(--border-color); border-radius: 4px; color: var(--text-secondary); cursor: pointer; }
.footer-btn:hover:not(:disabled) { background: var(--bg-tertiary); color: var(--text-primary); }
.footer-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.ai-panel { width: 340px; border-left: 1px solid var(--border-color); background: var(--bg-secondary); display: flex; flex-direction: column; overflow: hidden; }
.ai-panel-header { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border-color); }
.ai-panel-header h4 { margin: 0; font-size: 14px; color: var(--ws-accent-soft); }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; }
.close-btn:hover { color: var(--text-primary); }
.ai-panel-tabs { display: flex; border-bottom: 1px solid var(--border-color); }
.ai-tab { flex: 1; padding: 8px 4px; border: none; background: transparent; color: var(--text-tertiary); font-size: 11px; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s; }
.ai-tab:hover { color: var(--text-secondary); }
.ai-tab.active { color: var(--ws-accent-soft); border-bottom-color: var(--ws-accent); }
.ai-panel-content { flex: 1; overflow-y: auto; padding: 12px; }
.ai-section-content { }
.ai-action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.ai-action-card { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 14px 8px; background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: var(--radius-lg); cursor: pointer; transition: all 0.15s; color: var(--text-secondary); }
.ai-action-card:hover { background: var(--bg-tertiary); border-color: var(--ws-accent); color: var(--ws-accent-soft); }
.ai-action-card span { font-size: 12px; font-weight: 600; }
.ai-action-card small { font-size: 10px; color: var(--text-tertiary); }
.ai-loading { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 24px; color: var(--text-tertiary); }
.spinner { width: 24px; height: 24px; border: 3px solid var(--border-color); border-top-color: var(--ws-accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.ai-result { color: var(--text-primary); }
.ai-section { margin-bottom: 16px; }
.ai-section h5 { font-size: 12px; color: var(--text-tertiary); margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.text-result { white-space: pre-wrap; word-wrap: break-word; font-size: 13px; line-height: 1.6; margin: 0; color: var(--text-secondary); background: var(--bg-tertiary); padding: 10px; border-radius: var(--radius-md); }
.result-text { font-size: 13px; line-height: 1.6; color: var(--text-secondary); margin: 0; padding: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); }
.slide-item { margin-bottom: 8px; padding: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); }
.slide-item strong { font-size: 13px; color: var(--ws-accent-soft); }
.slide-item ul { margin: 4px 0 0; padding-left: 16px; font-size: 12px; color: var(--text-secondary); }
.improved-content { padding: 10px; background: var(--bg-tertiary); border-radius: var(--radius-md); font-size: 13px; }
.improved-content p { margin: 0 0 8px; }
.ai-suggestions ul { padding-left: 16px; font-size: 12px; color: var(--ws-accent-soft); }
.notes-text { padding: 10px; background: var(--bg-tertiary); border-radius: var(--radius-md); font-size: 13px; line-height: 1.6; color: var(--text-secondary); }
.design-item { padding: 8px; background: var(--bg-tertiary); border-radius: var(--radius-md); font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.design-item strong { color: var(--ws-accent-soft); }
.key-points ul { padding-left: 16px; font-size: 12px; color: var(--text-secondary); margin-top: 4px; }
.duration-est { font-size: 12px; color: var(--ws-accent-soft); margin-top: 8px; }
.tone-desc { font-size: 11px; color: var(--text-tertiary); margin-top: 4px; }
.coaching-list { padding-left: 16px; font-size: 13px; line-height: 1.8; color: var(--text-secondary); }
.consistency-list { padding-left: 16px; font-size: 12px; line-height: 1.8; }
.consistency-list .warning { color: var(--ws-warning); }
.consistency-list .error { color: var(--ws-danger); }
.consistency-list .info { color: var(--ws-info); }
.ai-actions { display: flex; gap: 8px; margin-top: 12px; }
.apply-btn { flex: 1; padding: 8px; background: var(--ws-accent); color: #fff; border: none; border-radius: 5px; cursor: pointer; font-size: 12px; }
.apply-btn:hover { background: var(--ws-accent-hover); }
.discard-btn { flex: 1; padding: 8px; background: var(--bg-tertiary); color: var(--text-tertiary); border: none; border-radius: 5px; cursor: pointer; font-size: 12px; }
.discard-btn:hover { background: var(--border-color); color: var(--text-secondary); }
</style>
