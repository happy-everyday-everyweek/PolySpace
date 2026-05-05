<template>
  <div class="document-editor">
    <div class="lo-menubar">
      <div class="menu-item" v-for="menu in menus" :key="menu.label" @click="toggleMenu(menu.label)" @mouseenter="openMenuOnHover(menu.label)">
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
        <button v-for="tab in ribbonTabs" :key="tab.id" class="ribbon-tab" :class="{ active: activeRibbonTab === tab.id }" @click="activeRibbonTab = tab.id">{{ tab.label }}</button>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'home'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <select class="lo-select" @change="onHeadingChange" :value="currentHeading" title="Paragraph Style">
              <option value="0">Text Body</option>
              <option value="1">Heading 1</option>
              <option value="2">Heading 2</option>
              <option value="3">Heading 3</option>
              <option value="4">Heading 4</option>
              <option value="5">Heading 5</option>
              <option value="6">Heading 6</option>
            </select>
            <select class="lo-select lo-select-font" @change="onFontFamilyChange" :value="currentFontFamily" title="Font Name">
              <option value="">Default</option>
              <option value="SimSun">SimSun</option>
              <option value="SimHei">SimHei</option>
              <option value="Microsoft YaHei">Microsoft YaHei</option>
              <option value="KaiTi">KaiTi</option>
              <option value="FangSong">FangSong</option>
              <option value="Arial">Arial</option>
              <option value="Times New Roman">Times New Roman</option>
              <option value="Courier New">Courier New</option>
              <option value="Georgia">Georgia</option>
            </select>
            <select class="lo-select lo-select-size" @change="onFontSizeChange" :value="currentFontSize" title="Font Size">
              <option value="0">Default</option>
              <option value="1">13px</option>
              <option value="2">15px</option>
              <option value="3">18px</option>
              <option value="4">22px</option>
            </select>
          </div>
          <div class="ribbon-group-label">Font</div>
        </div>

        <div class="ribbon-separator"></div>

        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" :class="{ active: editor?.isActive('bold') }" @click="editor?.chain().focus().toggleBold().run()" title="Bold (Ctrl+B)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 2h5a3.5 3.5 0 012.5 6 3.5 3.5 0 01-2 6.5H4V2zm2 2v3.5h3a1.75 1.75 0 000-3.5H6zm0 5.5V13h3.5a1.75 1.75 0 000-3.5H6z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('italic') }" @click="editor?.chain().focus().toggleItalic().run()" title="Italic (Ctrl+I)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M7 2h6v2h-2.2L9 12h2v2H5v-2h2.2L9 4H7V2z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('underline') }" @click="editor?.chain().focus().toggleUnderline().run()" title="Underline (Ctrl+U)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 2h2v5.5a2.5 2.5 0 005 0V2h2v5.5a4.5 4.5 0 01-9 0V2zM3 14h10v1.5H3V14z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('strike') }" @click="editor?.chain().focus().toggleStrike().run()" title="Strikethrough">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 7h10v2H3V7zm3-3a2 2 0 014 0h2a4 4 0 00-8 0h2zm0 8a2 2 0 004 0h2a4 4 0 01-8 0h2z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('superscript') }" @click="editor?.chain().focus().toggleSuperscript().run()" title="Superscript">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M10 12L6 8l4-4h2L8.5 7.5 12 11v1h-2zM3 12h2v1H3v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('subscript') }" @click="editor?.chain().focus().toggleSubscript().run()" title="Subscript">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M10 4L6 8l4 4h2L8.5 8.5 12 5V4h-2zM3 12h2v1H3v-1z" fill="currentColor"/></svg>
            </button>
            <div class="lo-btn-color-wrap">
              <button class="lo-btn" title="Font Color" @click="($refs.textColor as HTMLInputElement).click()">
                <svg width="16" height="16" viewBox="0 0 16 16"><path d="M4 13h8l-2-6H6L4 13zm1.5-4h5L12 12H4l1.5-3zM8 2l2.5 4h-5L8 2z" fill="currentColor"/><rect x="3" y="14" width="10" height="1.5" rx="0.5" fill="currentColor"/></svg>
                <span class="color-bar" :style="{ background: currentTextColor }"></span>
              </button>
              <input ref="textColor" type="color" class="hidden-color-input" :value="currentTextColor" @input="onTextColorChange" />
            </div>
            <div class="lo-btn-color-wrap">
              <button class="lo-btn" :class="{ active: editor?.isActive('highlight') }" title="Highlight" @click="($refs.hlColor as HTMLInputElement).click()">
                <svg width="16" height="16" viewBox="0 0 16 16"><rect x="2" y="10" width="12" height="4" rx="1" fill="currentColor" opacity="0.4"/><path d="M4 9l2-7h4l2 7H4zm1.5-1h5L8 3.5 5.5 8z" fill="currentColor"/></svg>
                <span class="color-bar" :style="{ background: currentHighlightColor }"></span>
              </button>
              <input ref="hlColor" type="color" class="hidden-color-input" :value="currentHighlightColor" @input="onHighlightChange" />
            </div>
          </div>
          <div class="ribbon-group-label">Formatting</div>
        </div>

        <div class="ribbon-separator"></div>

        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" :class="{ active: editor?.isActive('textAlign', 'left') }" @click="editor?.chain().focus().setTextAlign('left').run()" title="Align Left">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm0 3h8v1H2V6zm0 3h12v1H2V9zm0 3h8v1H2v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('textAlign', 'center') }" @click="editor?.chain().focus().setTextAlign('center').run()" title="Center">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm2 3h8v1H4V6zm-2 3h12v1H2V9zm2 3h8v1H4v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('textAlign', 'right') }" @click="editor?.chain().focus().setTextAlign('right').run()" title="Align Right">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm4 3h8v1H6V6zm-4 3h12v1H2V9zm4 3h8v1H6v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('textAlign', 'justify') }" @click="editor?.chain().focus().setTextAlign('justify').run()" title="Justified">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm0 3h12v1H2V6zm0 3h12v1H2V9zm0 3h12v1H2v-1z" fill="currentColor"/></svg>
            </button>
            <span class="ribbon-vdiv"></span>
            <button class="lo-btn" :class="{ active: editor?.isActive('bulletList') }" @click="editor?.chain().focus().toggleBulletList().run()" title="Bullets">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h2v2H2V3zm4 0h8v2H6V3zm-4 4h2v2H2V7zm4 0h8v2H6V7zm-4 4h2v2H2v-2zm4 0h8v2H6v-2z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" :class="{ active: editor?.isActive('orderedList') }" @click="editor?.chain().focus().toggleOrderedList().run()" title="Numbering">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h1v1H2V3zm0 4h1v1H2V7zm0 4h1v1H2v-1zm4-8h8v1H6V3zm0 4h8v1H6V7zm0 4h8v1H6v-1z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" @click="editor?.chain().focus().sinkListItem('listItem').run()" :disabled="!editor?.can().sinkListItem('listItem')" title="Increase Indent">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm0 4h12v1H2V7zm0 4h12v1H2v-1z" fill="currentColor" opacity="0.5"/><path d="M2 2v5l3-2.5L2 2z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" @click="editor?.chain().focus().liftListItem('listItem').run()" :disabled="!editor?.can().liftListItem('listItem')" title="Decrease Indent">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M2 3h12v1H2V3zm0 4h12v1H2V7zm0 4h12v1H2v-1z" fill="currentColor" opacity="0.5"/><path d="M5 2v5L2 4.5 5 2z" fill="currentColor"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Paragraph</div>
        </div>

        <div class="ribbon-separator"></div>

        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn" @click="editor?.chain().focus().undo().run()" :disabled="!editor?.can().undo()" title="Undo (Ctrl+Z)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M3 8l4-4v3h4a3 3 0 010 6H9v-2h2a1 1 0 000-2H7v3L3 8z" fill="currentColor"/></svg>
            </button>
            <button class="lo-btn" @click="editor?.chain().focus().redo().run()" :disabled="!editor?.can().redo()" title="Redo (Ctrl+Y)">
              <svg width="16" height="16" viewBox="0 0 16 16"><path d="M13 8l-4-4v3H5a3 3 0 000 6h2v-2H5a1 1 0 010-2h4v3l4-4z" fill="currentColor"/></svg>
            </button>
          </div>
          <div class="ribbon-group-label">Edit</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'insert'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="insertTable" title="Insert Table">
              <svg width="20" height="20" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M2 6h12M2 10h12M6 2v12" stroke="currentColor" stroke-width="1"/></svg>
              <span>Table</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="addImage" title="Insert Image">
              <svg width="20" height="20" viewBox="0 0 16 16"><rect x="2" y="2" width="12" height="12" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="5.5" cy="5.5" r="1.5" fill="none" stroke="currentColor" stroke-width="1"/><path d="M2 11l3-3 2 2 3-4 4 5" fill="none" stroke="currentColor" stroke-width="1"/></svg>
              <span>Image</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="openLinkDialog" title="Insert Hyperlink">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M6 10a3 3 0 01-3-3V6a3 3 0 016 0v1M10 6a3 3 0 013 3v1a3 3 0 01-6 0V9" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>
              <span>Link</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="editor?.chain().focus().setHorizontalRule().run()" title="Horizontal Rule">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M2 8h12" stroke="currentColor" stroke-width="2"/></svg>
              <span>Rule</span>
            </button>
          </div>
          <div class="ribbon-group-label">Insert</div>
        </div>

        <div class="ribbon-separator"></div>

        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" :class="{ active: editor?.isActive('blockquote') }" @click="editor?.chain().focus().toggleBlockquote().run()" title="Blockquote">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M3 3h3v3H3V3zm0 7h3v3H3v-3zm7-7h3v3h-3V3zm0 7h3v3h-3v-3z" fill="currentColor" opacity="0.5"/><path d="M7 3v10" stroke="currentColor" stroke-width="2"/></svg>
              <span>Quote</span>
            </button>
            <button class="lo-btn lo-btn-lg" :class="{ active: editor?.isActive('codeBlock') }" @click="editor?.chain().focus().toggleCodeBlock().run()" title="Code Block">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M5 4L1 8l4 4M11 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
              <span>Code</span>
            </button>
            <button class="lo-btn lo-btn-lg" :class="{ active: editor?.isActive('taskList') }" @click="editor?.chain().focus().toggleTaskList().run()" title="Task List">
              <svg width="20" height="20" viewBox="0 0 16 16"><rect x="2" y="3" width="4" height="4" rx="1" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M3.5 5.5l1 1 2-2" stroke="currentColor" stroke-width="1" fill="none"/><path d="M8 4h6M8 7h4M2 10h12M2 13h8" stroke="currentColor" stroke-width="1"/></svg>
              <span>Tasks</span>
            </button>
          </div>
          <div class="ribbon-group-label">Block</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'layout'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="exportDoc('docx')" title="Export as DOCX">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/><path d="M16 13H8M16 17H8M10 9H8"/></svg>
              <span>DOCX</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="exportDoc('pdf')" title="Export as PDF">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14,2 14,8 20,8"/></svg>
              <span>PDF</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="exportDoc('html')" title="Export as HTML">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M2 2h7l3 3v9a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1zm2 4h4v1H5V6zm0 3h6v1H5V9zm0 3h4v1H5v-1z" fill="currentColor"/></svg>
              <span>HTML</span>
            </button>
          </div>
          <div class="ribbon-group-label">Export</div>
        </div>

        <div class="ribbon-separator"></div>

        <div class="ribbon-group">
          <div class="ribbon-group-inner">
            <button class="lo-btn lo-btn-lg" @click="saveDocument" title="Save">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17,21 17,13 7,13 7,21"/><polyline points="7,3 7,8 15,8"/></svg>
              <span>Save</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="openDocument" title="Open">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>
              <span>Open</span>
            </button>
            <button class="lo-btn lo-btn-lg" @click="showVersionHistory = true" title="Versions">
              <svg width="20" height="20" viewBox="0 0 16 16"><path d="M8 1a7 7 0 107 7h-1.5a5.5 5.5 0 11-1.6-3.9L8 7h7V0l-2.3 2.3A7 7 0 008 1z" fill="currentColor"/></svg>
              <span>Versions</span>
            </button>
          </div>
          <div class="ribbon-group-label">File</div>
        </div>
      </div>

      <div class="ribbon-content" v-if="activeRibbonTab === 'ai'">
        <div class="ribbon-group">
          <div class="ribbon-group-inner ai-tools">
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('summarize')" title="AI Summarize">
              <svg width="18" height="18" viewBox="0 0 16 16"><rect x="1" y="2" width="14" height="2" rx="1" fill="currentColor"/><rect x="1" y="6" width="10" height="2" rx="1" fill="currentColor"/><rect x="1" y="10" width="12" height="2" rx="1" fill="currentColor"/></svg>
              <span>Summarize</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('expand')" title="AI Expand">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M3 8h10M8 3v10" fill="none" stroke="currentColor" stroke-width="2"/></svg>
              <span>Expand</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('rewrite')" title="AI Rewrite">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M12 1l3 3-9 9H3v-3l9-9z" fill="currentColor"/></svg>
              <span>Rewrite</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('grammar')" title="AI Grammar Check">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M8 1l2 4 4.5.7-3.2 3.1.7 4.5L8 11.3 3.9 13.3l.7-4.5L1.4 5.7 6 5z" fill="currentColor"/></svg>
              <span>Grammar</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('translate')" title="AI Translate">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M4 3h8v2H4V3zM2 7h5v1.5H2V7zm7 0h5v1.5H9V7zM3 11h3v1.5H3V11zm7 0h3v1.5H10V11z" fill="currentColor"/><path d="M6 2l4 12" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
              <span>Translate</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('tone_adjust')" title="AI Tone Adjust">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M8 2a6 6 0 100 12A6 6 0 008 2zm0 1.5a4.5 4.5 0 110 9 4.5 4.5 0 010-9zM8 5v3l2 2" stroke="currentColor" stroke-width="1.2" fill="none"/></svg>
              <span>Tone</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('continue_writing')" title="AI Continue Writing">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 4h8v1.5H2V4zm0 3h6v1.5H2V7zm0 3h10v1.5H2V10z" fill="currentColor"/><path d="M12 5l3 3-3 3" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
              <span>Continue</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('outline')" title="AI Outline">
              <svg width="18" height="18" viewBox="0 0 16 16"><path d="M2 2h3v3H2V2zm5 1h7v1H7V3zM2 7h3v3H2V7zm5 1h7v1H7V8zM2 12h3v3H2v-3zm5 1h7v1H7v-1z" fill="currentColor"/></svg>
              <span>Outline</span>
            </button>
            <button class="lo-btn lo-btn-lg ai-btn" @click="aiAction('qa')" title="AI Document Q&A">
              <svg width="18" height="18" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M6 6.5a2 2 0 013.5.5c0 1.5-2 2-2 2M8 10.5v.5" stroke="currentColor" stroke-width="1" fill="none"/></svg>
              <span>Q&A</span>
            </button>
          </div>
          <div class="ribbon-group-label">AI Assistant</div>
        </div>
      </div>
    </div>

    <div class="lo-ruler">
      <div class="ruler-track">
        <div v-for="i in 40" :key="i" class="ruler-tick" :class="{ major: i % 5 === 0 }">
          <span v-if="i % 5 === 0" class="ruler-num">{{ i }}</span>
        </div>
      </div>
    </div>

    <div class="editor-body">
      <EditorContent :editor="(editorProp as any)" />
    </div>

    <AiAssistantPanel
      v-if="aiPanelOpen"
      :loading="aiLoading"
      :result="aiResult"
      :action-label="aiCurrentAction"
      @close="aiPanelOpen = false"
      @apply="applyAIResult"
    />

    <div class="lo-statusbar">
      <div class="status-left">
        <span class="status-info">{{ wordCount }} words / {{ charCount }} chars</span>
        <span class="status-sep">|</span>
        <span class="status-save" :class="saveStatus">{{ saveStatusLabel }}</span>
      </div>
      <div class="status-right">
        <button class="status-btn" @click="sendToModule('ppt')" title="Send to PPT">PPT</button>
        <button class="status-btn" @click="sendToModule('todo')" title="Create Todo">Todo</button>
        <button class="status-btn" @click="sendToModule('email')" title="Send via Email">Email</button>
        <button class="status-btn" @click="sendToModule('knowledge')" title="Save to Knowledge">Knowledge</button>
        <span class="status-sep">|</span>
        <span class="zoom-label">100%</span>
      </div>
    </div>

    <div v-if="linkDialogOpen" class="dialog-overlay" @click.self="linkDialogOpen = false">
      <div class="link-dialog">
        <h4>Insert Link</h4>
        <div class="dialog-field">
          <label>URL</label>
          <input v-model="linkUrl" type="url" placeholder="https://example.com" class="global-input" @keydown.enter="confirmLink" />
        </div>
        <div class="dialog-actions">
          <button class="global-btn global-btn-secondary" @click="removeLink" v-if="editor?.isActive('link')">Remove</button>
          <button class="global-btn global-btn-secondary" @click="linkDialogOpen = false">Cancel</button>
          <button class="global-btn global-btn-primary" @click="confirmLink">Confirm</button>
        </div>
      </div>
    </div>

    <div v-if="imageDialogOpen" class="dialog-overlay" @click.self="imageDialogOpen = false">
      <div class="link-dialog">
        <h4>Insert Image</h4>
        <div class="dialog-field">
          <label>Image URL</label>
          <input v-model="imageUrl" type="url" placeholder="https://example.com/image.png" class="global-input" @keydown.enter="confirmImage" />
        </div>
        <div class="dialog-field">
          <label>Alt Text</label>
          <input v-model="imageAlt" type="text" placeholder="Image description" class="global-input" />
        </div>
        <div class="dialog-actions">
          <button class="global-btn global-btn-secondary" @click="imageDialogOpen = false">Cancel</button>
          <button class="global-btn global-btn-primary" @click="confirmImage">Insert</button>
        </div>
      </div>
    </div>

    <div v-if="showVersionHistory" class="dialog-overlay" @click.self="showVersionHistory = false">
      <div class="version-dialog">
        <div class="version-dialog-header">
          <h4>Version History</h4>
          <button class="close-btn" @click="showVersionHistory = false">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>
        <div class="version-list">
          <div v-if="versions.length === 0" class="version-empty">No versions saved yet</div>
          <div v-for="ver in versions" :key="ver.id" class="version-item" @click="restoreVersion(ver)">
            <span class="version-label">{{ ver.label || 'Auto save' }}</span>
            <span class="version-time">{{ formatTime(ver.createdAt) }}</span>
          </div>
        </div>
        <div class="version-actions">
          <button class="global-btn global-btn-primary" @click="saveVersion">Save Current Version</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onBeforeUnmount, onMounted, watch } from 'vue'
import { Editor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Link from '@tiptap/extension-link'
import TaskList from '@tiptap/extension-task-list'
import TaskItem from '@tiptap/extension-task-item'
import Placeholder from '@tiptap/extension-placeholder'
import Image from '@tiptap/extension-image'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableCell from '@tiptap/extension-table-cell'
import TableHeader from '@tiptap/extension-table-header'
import Highlight from '@tiptap/extension-highlight'
import Superscript from '@tiptap/extension-superscript'
import Subscript from '@tiptap/extension-subscript'
import { TextStyle } from '@tiptap/extension-text-style'
import FontFamily from '@tiptap/extension-font-family'
import Color from '@tiptap/extension-color'
import Typography from '@tiptap/extension-typography'
import CharacterCount from '@tiptap/extension-character-count'
import api from '../../utils/api'
import { useActivityStore } from '@/stores/activity'
import { useWorkspaceStore } from '@/stores/workspace'
import AiAssistantPanel from './AiAssistantPanel.vue'
import { useDocumentPersistence } from '@/composables/useDocumentPersistence'
import { useAppSettings } from '@/composables/useAppSettings'

interface MenuItem {
  label: string
  shortcut?: string
  action?: () => void
  disabled?: boolean
}

const props = defineProps<{
  modelValue?: string
  docId?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'save': [content: string]
}>()

const activityStore = useActivityStore()
const workspaceStore = useWorkspaceStore()
const { saveDoc, saveVersion: persistVersion, getVersions, saveStatus } = useDocumentPersistence('document')
const docDefaults = useAppSettings('document').settings.value

const docTitle = ref('Untitled Document')
const aiPanelOpen = ref(false)
const aiLoading = ref(false)
const aiResult = ref<any>(null)
const aiCurrentAction = ref('')
const linkDialogOpen = ref(false)
const linkUrl = ref('')
const imageDialogOpen = ref(false)
const imageUrl = ref('')
const imageAlt = ref('')
const showVersionHistory = ref(false)
const versions = ref<any[]>([])
const currentTextColor = ref('#000000')
const currentHighlightColor = ref('#fef08a')
const activeRibbonTab = ref('home')
const activeMenu = ref('')

const ribbonTabs = [
  { id: 'home', label: 'Home' },
  { id: 'insert', label: 'Insert' },
  { id: 'layout', label: 'Layout' },
  { id: 'ai', label: 'AI' },
]

const menus = computed(() => [
  {
    label: 'File',
    items: [
      { label: 'New', shortcut: 'Ctrl+N', action: () => { editor.value?.commands.clearContent() } },
      { label: 'Open', shortcut: 'Ctrl+O', action: openDocument },
      { label: 'Save', shortcut: 'Ctrl+S', action: saveDocument },
      { label: 'Save Version', action: saveVersion },
      { label: 'Export DOCX', action: () => exportDoc('docx') },
      { label: 'Export PDF', action: () => exportDoc('pdf') },
      { label: 'Export HTML', action: () => exportDoc('html') },
    ] as MenuItem[],
  },
  {
    label: 'Edit',
    items: [
      { label: 'Undo', shortcut: 'Ctrl+Z', action: () => editor.value?.chain().focus().undo().run(), disabled: !editor.value?.can().undo() },
      { label: 'Redo', shortcut: 'Ctrl+Y', action: () => editor.value?.chain().focus().redo().run(), disabled: !editor.value?.can().redo() },
      { label: 'Select All', shortcut: 'Ctrl+A', action: () => editor.value?.chain().focus().selectAll().run() },
    ] as MenuItem[],
  },
  {
    label: 'View',
    items: [
      { label: 'Version History', action: () => { showVersionHistory.value = true } },
    ] as MenuItem[],
  },
  {
    label: 'Insert',
    items: [
      { label: 'Image', action: addImage },
      { label: 'Link', action: openLinkDialog },
      { label: 'Table', action: insertTable },
      { label: 'Horizontal Rule', action: () => editor.value?.chain().focus().setHorizontalRule().run() },
    ] as MenuItem[],
  },
  {
    label: 'Format',
    items: [
      { label: 'Bold', shortcut: 'Ctrl+B', action: () => editor.value?.chain().focus().toggleBold().run() },
      { label: 'Italic', shortcut: 'Ctrl+I', action: () => editor.value?.chain().focus().toggleItalic().run() },
      { label: 'Underline', shortcut: 'Ctrl+U', action: () => editor.value?.chain().focus().toggleUnderline().run() },
      { label: 'Strikethrough', action: () => editor.value?.chain().focus().toggleStrike().run() },
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
      { label: 'About PolySpace Writer', disabled: true },
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

const editor = ref<Editor | null>(null)
const editorProp = computed(() => editor.value ?? undefined)

onMounted(() => {
  editor.value = new Editor({
    content: props.modelValue || '',
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3, 4, 5, 6] },
      }),
      Underline,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Link.configure({ openOnClick: false, HTMLAttributes: { class: 'editor-link' } }),
      TaskList,
      TaskItem.configure({ nested: true }),
      Placeholder.configure({ placeholder: '开始输入...' }),
      Image.configure({ inline: false, allowBase64: true }),
      Table.configure({ resizable: true }),
      TableRow,
      TableCell,
      TableHeader,
      Highlight.configure({ multicolor: true }),
      Superscript,
      Subscript,
      TextStyle,
      FontFamily,
      Color,
      Typography,
      CharacterCount,
    ],
    onUpdate: ({ editor }) => {
      const html = editor.getHTML()
      emit('update:modelValue', html)
      saveStatus.value = 'unsaved'
      debouncedSave(html)
    },
    onCreate: ({ editor }) => {
      if (docDefaults.fontFamily && docDefaults.fontFamily !== 'Default') {
        editor.chain().setFontFamily(docDefaults.fontFamily).run()
        currentFontFamily.value = docDefaults.fontFamily
      }
    },
  })
})

const currentHeading = computed(() => {
  for (let i = 1; i <= 6; i++) {
    if (editor.value?.isActive('heading', { level: i })) return `${i}`
  }
  return '0'
})

const currentFontSize = computed(() => {
  for (let i = 1; i <= 4; i++) {
    if (editor.value?.isActive('textStyle', { fontSize: `${i}` })) return `${i}`
  }
  return '0'
})

const currentFontFamily = ref('')

const wordCount = computed(() => {
  const text = (editor.value?.getText() ?? '').trim()
  if (!text) return 0
  const cjk = text.match(/[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/g)
  const cjkCount = cjk ? cjk.length : 0
  const withoutCjk = text.replace(/[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff]/g, ' ')
  const wc = withoutCjk.split(/\s+/).filter(w => w.length > 0).length
  return cjkCount + wc
})

const charCount = computed(() => (editor.value?.getText() ?? '').length)

const saveStatusLabel = computed(() => {
  const map: Record<string, string> = { saved: 'Saved', unsaved: 'Unsaved', saving: 'Saving...' }
  return map[saveStatus.value] || ''
})

let saveTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSave(content: string) {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    saveStatus.value = 'saving'
    saveDoc(props.docId || 'default', { content, title: docTitle.value, updatedAt: Date.now() }).then(() => {
      saveStatus.value = 'saved'
      emit('save', content)
    })
  }, 1500)
}

function onHeadingChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  const level = parseInt(val)
  if (level === 0) {
    editor.value?.chain().focus().setParagraph().run()
  } else {
    editor.value?.chain().focus().toggleHeading({ level: level as 1 | 2 | 3 | 4 | 5 | 6 }).run()
  }
}

function onFontSizeChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  const sizeMap: Record<string, string> = { '0': '', '1': '13px', '2': '15px', '3': '18px', '4': '22px' }
  const size = sizeMap[val]
  if (!size) {
    editor.value?.chain().focus().unsetMark('textStyle').run()
  } else {
    editor.value?.chain().focus().setMark('textStyle', { fontSize: size }).run()
  }
}

function onFontFamilyChange(e: Event) {
  const val = (e.target as HTMLSelectElement).value
  currentFontFamily.value = val
  if (!val) {
    editor.value?.chain().focus().unsetFontFamily().run()
  } else {
    editor.value?.chain().focus().setFontFamily(val).run()
  }
}

function onTextColorChange(e: Event) {
  const color = (e.target as HTMLInputElement).value
  currentTextColor.value = color
  editor.value?.chain().focus().setColor(color).run()
}

function onHighlightChange(e: Event) {
  const color = (e.target as HTMLInputElement).value
  currentHighlightColor.value = color
  editor.value?.chain().focus().toggleHighlight({ color }).run()
}

function openLinkDialog() {
  const previous = editor.value?.getAttributes('link')?.href
  linkUrl.value = previous || ''
  linkDialogOpen.value = true
}

function confirmLink() {
  if (!linkUrl.value) return
  editor.value?.chain().focus().extendMarkRange('link').setLink({ href: linkUrl.value }).run()
  linkDialogOpen.value = false
  linkUrl.value = ''
}

function removeLink() {
  editor.value?.chain().focus().extendMarkRange('link').unsetLink().run()
  linkDialogOpen.value = false
  linkUrl.value = ''
}

function addImage() {
  imageUrl.value = ''
  imageAlt.value = ''
  imageDialogOpen.value = true
}

function confirmImage() {
  if (!imageUrl.value) return
  editor.value?.chain().focus().setImage({ src: imageUrl.value, alt: imageAlt.value || '' }).run()
  imageDialogOpen.value = false
  imageUrl.value = ''
  imageAlt.value = ''
}

function insertTable() {
  editor.value?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
}

function getSelectedText(): string {
  const { from, to } = editor.value?.state?.selection ?? { from: 0, to: 0 }
  const text = editor.value?.state?.doc.textBetween(from, to, '\n') ?? ''
  return text || (editor.value?.getText() ?? '')
}

async function aiAction(action: string) {
  const text = getSelectedText()
  if (!text.trim()) return
  aiCurrentAction.value = action.charAt(0).toUpperCase() + action.slice(1).replace(/_/g, ' ')
  aiLoading.value = true
  aiPanelOpen.value = true
  aiResult.value = null
  activityStore.recordAIAction(action, text.substring(0, 50))
  try {
    const res = await api.post('/ai/workspace/document/assist', {
      action,
      content: text,
      context: editor.value?.getText() ?? '',
      operation_path: activityStore.getContextSummary(),
    })
    aiResult.value = res.data
  } catch {
    aiResult.value = { result: 'AI processing failed. Please try again.' }
  } finally {
    aiLoading.value = false
  }
}

function applyAIResult(resultData?: any) {
  const data = resultData || aiResult.value
  if (!data) return
  if (data.corrected) {
    editor.value?.chain().focus().insertContent(data.corrected).run()
  } else if (data.result) {
    editor.value?.chain().focus().insertContent(data.result).run()
  } else if (data.adjusted) {
    editor.value?.chain().focus().insertContent(data.adjusted).run()
  } else if (data.translated) {
    editor.value?.chain().focus().insertContent(data.translated).run()
  } else if (data.continuation) {
    editor.value?.chain().focus().insertContent(data.continuation).run()
  } else if (data.slides) {
    const outline = data.slides
      .map((s: any, i: number) => `<h2>${i + 1}. ${s.title}</h2><ul>${(s.bullets || []).map((b: string) => `<li>${b}</li>`).join('')}</ul>`)
      .join('')
    editor.value?.chain().focus().insertContent(outline).run()
  } else if (data.outline) {
    const html = data.outline
      .map((item: any) => {
        const tag = item.level === 1 ? 'h2' : item.level === 2 ? 'h3' : 'p'
        return `<${tag}>${item.text}</${tag}>`
      })
      .join('')
    editor.value?.chain().focus().insertContent(html).run()
  } else if (data.answer) {
    editor.value?.chain().focus().insertContent(`<blockquote>${data.answer}</blockquote>`).run()
  }
  aiPanelOpen.value = false
}

function sendToModule(module: string) {
  workspaceStore.setActiveTab(module)
  activityStore.recordActivity({
    type: 'document',
    name: `Send to ${module}`,
    detail: docTitle.value,
  })
  switch (module) {
    case 'ppt':
      workspaceStore.setActiveDocument(docTitle.value, 'presentation')
      break
    case 'todo':
      workspaceStore.setActiveDocument(docTitle.value, 'document')
      break
    case 'email':
      workspaceStore.setActiveDocument(docTitle.value, 'document')
      break
    case 'knowledge':
      workspaceStore.setActiveDocument(docTitle.value, 'document')
      break
  }
}

async function exportDoc(format: string) {
  if (format === 'html') {
    const blob = new Blob([editor.value?.getHTML() ?? ''], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${docTitle.value || 'document'}.html`
    a.click()
    URL.revokeObjectURL(url)
    return
  }

  try {
    saveStatus.value = 'saving'
    const htmlContent = editor.value?.getHTML() ?? ''
    const res = await api.post('/documents/html/to/' + format, null, {
      params: { html_content: htmlContent, title: docTitle.value || 'Document' },
      responseType: 'blob',
    })
    const blob = new Blob([res.data])
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${docTitle.value || 'document'}.${format}`
    a.click()
    URL.revokeObjectURL(url)
    saveStatus.value = 'saved'
  } catch (e) {
    console.error('Export failed, falling back to local:', e)
    if (format === 'docx') {
      const htmlContent = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40"><head><meta charset="utf-8"><title>${docTitle.value}</title></head><body>${editor.value?.getHTML() ?? ''}</body></html>`
      const blob = new Blob([htmlContent], { type: 'application/msword' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${docTitle.value || 'document'}.doc`
      a.click()
      URL.revokeObjectURL(url)
    }
    saveStatus.value = 'unsaved'
  }
}

async function saveDocument() {
  saveStatus.value = 'saving'
  try {
    const content = editor.value?.getHTML() ?? ''
    await api.post('/workspace/documents', {
      title: docTitle.value || 'Untitled Document',
      doc_type: 'document',
      content,
      metadata: { wordCount: wordCount.value, charCount: charCount.value },
    })
    await api.post('/files/write', {
      path: `${docTitle.value || 'document'}.html`,
      content,
      subdir: 'documents',
    })
    saveStatus.value = 'saved'
  } catch (e) {
    console.error('Failed to save document:', e)
    saveStatus.value = 'unsaved'
  }
}

async function openDocument() {
  try {
    const res = await api.get('/workspace/documents', { params: { doc_type: 'document' } })
    const docs = res.data?.documents || res.data || []
    if (!docs.length) return
    const latest = docs[0]
    if (latest?.content) {
      editor.value?.commands.setContent(latest.content)
      docTitle.value = latest.title || 'Untitled Document'
      saveStatus.value = 'saved'
    }
  } catch (e) {
    console.error('Failed to open document:', e)
  }
}

async function saveVersion() {
  const content = editor.value?.getHTML() ?? ''
  await persistVersion(props.docId || 'default', content, docTitle.value)
  await loadVersions()
}

async function loadVersions() {
  const vers = await getVersions(props.docId || 'default')
  versions.value = vers || []
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleString()
}

async function restoreVersion(ver: any) {
  if (ver.content) {
    editor.value?.commands.setContent(ver.content)
  }
  showVersionHistory.value = false
}

watch(() => props.modelValue, (val) => {
  if (val !== (editor.value?.getHTML() ?? '')) {
    editor.value?.commands.setContent(val || '')
  }
})

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer)
  editor.value?.destroy()
})
</script>

<style scoped>
.document-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
  position: relative;
}

.lo-menubar {
  display: flex;
  align-items: center;
  padding: 2px 8px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  font-size: 13px;
  user-select: none;
}

.menu-item {
  position: relative;
  padding: 4px 10px;
  color: var(--text-color);
  cursor: pointer;
  border-radius: 3px;
}

.menu-item:hover {
  background: var(--border-color);
}

.menu-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  min-width: 220px;
  z-index: 200;
  padding: 4px 0;
}

.menu-dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 16px;
  cursor: pointer;
  color: var(--text-color);
  font-size: 13px;
}

.menu-dropdown-item:hover:not(.disabled) {
  background: var(--primary-color);
  color: white;
}

.menu-dropdown-item.disabled {
  opacity: 0.4;
  cursor: default;
}

.menu-item-shortcut {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-left: 24px;
}

.menu-dropdown-item:hover:not(.disabled) .menu-item-shortcut {
  color: rgba(255,255,255,0.7);
}

.lo-ribbon {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.ribbon-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  padding: 0 8px;
}

.ribbon-tab {
  padding: 6px 16px;
  border: none;
  background: none;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}

.ribbon-tab:hover {
  color: var(--text-color);
  background: var(--border-color);
}

.ribbon-tab.active {
  color: var(--primary-color);
  border-bottom-color: var(--primary-color);
}

.ribbon-content {
  display: flex;
  align-items: stretch;
  padding: 6px 12px;
  min-height: 72px;
  gap: 2px;
}

.ribbon-group {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ribbon-group-inner {
  display: flex;
  align-items: center;
  gap: 1px;
  flex: 1;
  padding: 2px 4px;
}

.ribbon-group-label {
  font-size: 10px;
  color: var(--text-tertiary);
  text-align: center;
  padding: 2px 0 0;
  white-space: nowrap;
}

.ribbon-separator {
  width: 1px;
  background: var(--border-color);
  margin: 4px 6px;
  align-self: stretch;
}

.ribbon-vdiv {
  width: 1px;
  height: 20px;
  background: var(--border-color);
  margin: 0 3px;
}

.lo-select {
  padding: 3px 6px;
  border: 1px solid var(--border-color);
  border-radius: 3px;
  background: var(--input-bg);
  color: var(--text-color);
  font-size: 12px;
  cursor: pointer;
  outline: none;
  max-width: 100px;
}

.lo-select:focus {
  border-color: var(--primary-color);
}

.lo-select-font {
  max-width: 130px;
}

.lo-select-size {
  max-width: 70px;
}

.lo-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 4px 5px;
  border-radius: 3px;
  color: var(--text-secondary);
  cursor: pointer;
  background: none;
  border: none;
  transition: all 0.12s;
  position: relative;
}

.lo-btn:hover:not(:disabled) {
  background: var(--border-color);
  color: var(--text-color);
}

.lo-btn.active {
  background: var(--primary-light);
  color: var(--primary-color);
}

.lo-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.lo-btn-lg {
  flex-direction: column;
  padding: 6px 10px;
  gap: 2px;
  min-width: 48px;
}

.lo-btn-lg span {
  font-size: 10px;
  white-space: nowrap;
}

.lo-btn-color-wrap {
  position: relative;
}

.color-bar {
  display: block;
  width: 14px;
  height: 3px;
  border-radius: 1px;
  margin-top: 1px;
}

.hidden-color-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.ai-btn {
  color: var(--primary-color);
}

.ai-btn:hover:not(:disabled) {
  background: var(--primary-light);
  color: var(--primary-color);
}

.ai-tools {
  gap: 4px;
}

.lo-ruler {
  height: 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  overflow: hidden;
  user-select: none;
}

.ruler-track {
  display: flex;
  align-items: flex-end;
  height: 100%;
  padding: 0 48px;
}

.ruler-tick {
  flex: 1;
  height: 6px;
  border-left: 1px solid var(--text-tertiary);
  position: relative;
}

.ruler-tick.major {
  height: 10px;
}

.ruler-num {
  position: absolute;
  top: -2px;
  left: 1px;
  font-size: 8px;
  color: var(--text-tertiary);
}

.editor-body {
  flex: 1;
  padding: 24px 48px;
  overflow: auto;
  max-width: 100%;
}

.editor-body :deep(.tiptap) {
  outline: none;
  min-height: 100%;
  font-size: 15px;
  line-height: 1.8;
  color: var(--text-color);
  max-width: 800px;
  margin: 0 auto;
}

.editor-body :deep(.tiptap p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--text-tertiary);
  pointer-events: none;
  height: 0;
  opacity: 0.5;
}

.editor-body :deep(.tiptap h1) { font-size: 28px; font-weight: 700; margin: 20px 0 10px; line-height: 1.3; }
.editor-body :deep(.tiptap h2) { font-size: 22px; font-weight: 600; margin: 16px 0 8px; line-height: 1.4; }
.editor-body :deep(.tiptap h3) { font-size: 18px; font-weight: 600; margin: 14px 0 6px; line-height: 1.4; }
.editor-body :deep(.tiptap ul) { list-style: disc; padding-left: 24px; }
.editor-body :deep(.tiptap ol) { list-style: decimal; padding-left: 24px; }
.editor-body :deep(.tiptap blockquote) { border-left: 3px solid var(--primary-color); padding-left: 16px; margin: 8px 0; color: var(--text-secondary); }
.editor-body :deep(.tiptap pre) { background: var(--bg-tertiary); border-radius: var(--radius-lg); padding: 12px; font-family: monospace; font-size: 13px; overflow-x: auto; }
.editor-body :deep(.tiptap code) { background: var(--bg-tertiary); padding: 2px 4px; border-radius: var(--radius-sm); font-family: monospace; font-size: 13px; }
.editor-body :deep(.tiptap .editor-link) { color: var(--primary-color); text-decoration: underline; cursor: pointer; }
.editor-body :deep(.tiptap hr) { border: none; border-top: 1px solid var(--border-color); margin: 16px 0; }
.editor-body :deep(.tiptap ul[data-type="taskList"]) { list-style: none; padding-left: 0; }
.editor-body :deep(.tiptap ul[data-type="taskList"] li) { display: flex; align-items: flex-start; gap: 8px; }
.editor-body :deep(.tiptap ul[data-type="taskList"] li label) { display: flex; align-items: center; gap: 4px; cursor: pointer; }
.editor-body :deep(.tiptap ul[data-type="taskList"] li label input[type="checkbox"]) { accent-color: var(--primary-color); }
.editor-body :deep(.tiptap img) { max-width: 100%; height: auto; border-radius: var(--radius-lg); margin: 8px 0; }
.editor-body :deep(.tiptap table) { border-collapse: collapse; width: 100%; margin: 8px 0; overflow: hidden; }
.editor-body :deep(.tiptap table td), .editor-body :deep(.tiptap table th) { border: 1px solid var(--border-color); padding: 6px 10px; min-width: 60px; vertical-align: top; text-align: left; }
.editor-body :deep(.tiptap table th) { background: var(--bg-secondary); font-weight: 600; }
.editor-body :deep(.tiptap table .selectedCell) { background: var(--primary-light); }
.editor-body :deep(.tiptap mark) { border-radius: 2px; padding: 0 2px; }

.lo-statusbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 16px;
  border-top: 1px solid var(--border-color);
  font-size: 11px;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
}

.status-left, .status-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-sep {
  color: var(--border-color);
}

.status-save {
  font-weight: 500;
}

.status-save.saved { color: #16a34a; }
.status-save.unsaved { color: #d97706; }
.status-save.saving { color: var(--primary-color); }

.status-btn {
  padding: 2px 8px;
  border-radius: 3px;
  border: 1px solid var(--border-color);
  background: none;
  color: var(--text-tertiary);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.12s;
}

.status-btn:hover {
  background: var(--border-color);
  color: var(--text-color);
}

.zoom-label {
  font-size: 11px;
}

.dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.link-dialog, .version-dialog {
  background: var(--card-bg);
  border-radius: var(--radius-xl);
  padding: 20px;
  min-width: 360px;
  box-shadow: var(--shadow-lg);
}

.link-dialog h4, .version-dialog h4 { margin: 0 0 16px; font-size: 15px; color: var(--text-color); }
.dialog-field { margin-bottom: 12px; }
.dialog-field label { display: block; font-size: 12px; font-weight: 500; margin-bottom: 4px; color: var(--text-secondary); }
.dialog-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.version-dialog-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.version-dialog-header h4 { margin: 0; }
.close-btn { background: none; border: none; color: var(--text-tertiary); cursor: pointer; padding: 4px; border-radius: var(--radius-md); }
.close-btn:hover { color: var(--text-color); background: var(--border-color); }
.version-list { max-height: 300px; overflow-y: auto; }
.version-empty { text-align: center; color: var(--text-tertiary); padding: 24px; font-size: 13px; }
.version-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-radius: var(--radius-md); cursor: pointer; transition: background var(--transition-fast); }
.version-item:hover { background: var(--bg-secondary); }
.version-label { font-size: 13px; color: var(--text-color); }
.version-time { font-size: 11px; color: var(--text-tertiary); }
.version-actions { margin-top: 12px; display: flex; justify-content: center; }
</style>
