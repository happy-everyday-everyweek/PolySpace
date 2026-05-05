<template>
  <div class="settings-section">
    <h2 class="global-section-title">应用设置</h2>

    <div class="global-form-group">
      <label>默认模式</label>
      <select v-model="form.defaultMode" class="global-input">
        <option value="agent">AI Agent</option>
        <option value="workspace">工作台</option>
      </select>
      <span class="setting-hint">启动时默认进入的模式</span>
    </div>

    <div class="app-settings-divider"></div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>
        天气
      </h3>
      <div class="global-form-group">
        <label>默认城市</label>
        <div class="city-search-row">
          <input v-model="weatherSearch" placeholder="搜索城市..." class="global-input city-input" @input="onWeatherSearch" />
          <div v-if="weatherResults.length" class="city-dropdown">
            <div v-for="city in weatherResults" :key="city.id" class="city-item" @click="selectWeatherCity(city)">
              <span>{{ city.name }}</span>
              <span class="city-detail">{{ city.admin1 }}, {{ city.country }}</span>
            </div>
          </div>
        </div>
        <span v-if="form.weather.cityName" class="setting-hint">当前: {{ form.weather.cityName }}, {{ form.weather.country }}</span>
        <span v-else class="setting-hint">未设置默认城市</span>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
        邮件
      </h3>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.email.autoReply" />
          <span>自动回复</span>
        </label>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.email.taskExtraction" />
          <span>任务提取</span>
        </label>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.email.notification" />
          <span>通知</span>
        </label>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.email.monitoring" />
          <span>AI 邮件监控</span>
        </label>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
        屏幕录制
      </h3>
      <div class="global-form-group">
        <label>录制源</label>
        <select v-model="form.screenRecorder.sourceType" class="global-input">
          <option value="screen">屏幕</option>
          <option value="window">窗口</option>
          <option value="tab">浏览器标签</option>
          <option value="region">区域</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>画质</label>
        <select v-model="form.screenRecorder.quality" class="global-input">
          <option value="low">低 (720p/15fps)</option>
          <option value="medium">中 (1080p/24fps)</option>
          <option value="high">高 (1080p/30fps)</option>
          <option value="original">原始</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>录制模板</label>
        <select v-model="form.screenRecorder.template" class="global-input">
          <option value="">无</option>
          <option value="tutorial">教程</option>
          <option value="bug_report">Bug 报告</option>
          <option value="meeting">会议</option>
          <option value="demo">产品演示</option>
        </select>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.screenRecorder.changeDetection" />
          <span>变化检测</span>
        </label>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.screenRecorder.includeAudio" />
          <span>包含音频</span>
        </label>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.screenRecorder.includeCursor" />
          <span>包含光标</span>
        </label>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
        PPT
      </h3>
      <div class="global-form-group">
        <label>默认主题</label>
        <select v-model="form.ppt.theme" class="global-input">
          <option value="light">浅色</option>
          <option value="dark">深色</option>
          <option value="blue">蓝色</option>
          <option value="green">绿色</option>
          <option value="warm">暖色</option>
          <option value="purple">紫色</option>
          <option value="red">红色</option>
        </select>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        PDF
      </h3>
      <div class="global-form-group">
        <label>水印文字</label>
        <input v-model="form.pdf.watermarkText" class="global-input" placeholder="留空则不添加水印" />
      </div>
      <div class="global-form-group">
        <label>水印字号</label>
        <input type="number" v-model.number="form.pdf.watermarkFontSize" class="global-input" min="8" max="120" />
      </div>
      <div class="global-form-group">
        <label>水印透明度</label>
        <input type="range" v-model.number="form.pdf.watermarkOpacity" min="0" max="1" step="0.05" class="global-input range-input" />
        <span class="range-value">{{ form.pdf.watermarkOpacity }}</span>
      </div>
      <div class="global-form-group">
        <label>水印角度</label>
        <input type="number" v-model.number="form.pdf.watermarkAngle" class="global-input" min="-180" max="180" />
      </div>
      <div class="global-form-group">
        <label>水印位置</label>
        <select v-model="form.pdf.watermarkPosition" class="global-input">
          <option value="center">居中</option>
          <option value="tile">平铺</option>
          <option value="top-left">左上</option>
          <option value="top-right">右上</option>
          <option value="bottom-left">左下</option>
          <option value="bottom-right">右下</option>
        </select>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>
        视频
      </h3>
      <div class="global-form-group">
        <label>导出格式</label>
        <select v-model="form.video.exportFormat" class="global-input">
          <option value="mp4">MP4</option>
          <option value="webm">WebM</option>
          <option value="gif">GIF</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>导出画质</label>
        <select v-model="form.video.exportQuality" class="global-input">
          <option value="low">低 (720p)</option>
          <option value="medium">中 (1080p)</option>
          <option value="high">高 (1080p 高码率)</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>导出分辨率</label>
        <select v-model="form.video.exportResolution" class="global-input">
          <option value="original">原始</option>
          <option value="1920x1080">1920x1080</option>
          <option value="1280x720">1280x720</option>
          <option value="854x480">854x480</option>
          <option value="640x360">640x360</option>
        </select>
      </div>
      <div class="global-form-group">
        <label class="toggle-row">
          <input type="checkbox" v-model="form.video.includeSubtitles" />
          <span>烧录字幕</span>
        </label>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        图片
      </h3>
      <div class="global-form-group">
        <label>亮度 ({{ form.image.brightness }}%)</label>
        <input type="range" v-model.number="form.image.brightness" min="0" max="200" class="global-input range-input" />
      </div>
      <div class="global-form-group">
        <label>对比度 ({{ form.image.contrast }}%)</label>
        <input type="range" v-model.number="form.image.contrast" min="0" max="200" class="global-input range-input" />
      </div>
      <div class="global-form-group">
        <label>饱和度 ({{ form.image.saturate }}%)</label>
        <input type="range" v-model.number="form.image.saturate" min="0" max="200" class="global-input range-input" />
      </div>
      <div class="global-form-group">
        <label>模糊 ({{ form.image.blur }}px)</label>
        <input type="range" v-model.number="form.image.blur" min="0" max="20" class="global-input range-input" />
      </div>
      <div class="global-form-group">
        <label>灰度 ({{ form.image.grayscale }}%)</label>
        <input type="range" v-model.number="form.image.grayscale" min="0" max="100" class="global-input range-input" />
      </div>
      <div class="global-form-group">
        <label>褐色 ({{ form.image.sepia }}%)</label>
        <input type="range" v-model.number="form.image.sepia" min="0" max="100" class="global-input range-input" />
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        文档
      </h3>
      <div class="global-form-group">
        <label>默认字体</label>
        <select v-model="form.document.fontFamily" class="global-input">
          <option value="Default">默认</option>
          <option value="SimSun">宋体</option>
          <option value="SimHei">黑体</option>
          <option value="Microsoft YaHei">微软雅黑</option>
          <option value="KaiTi">楷体</option>
          <option value="FangSong">仿宋</option>
          <option value="Arial">Arial</option>
          <option value="Times New Roman">Times New Roman</option>
          <option value="Courier New">Courier New</option>
          <option value="Georgia">Georgia</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>默认字号</label>
        <select v-model="form.document.fontSize" class="global-input">
          <option value="Default">默认</option>
          <option value="13px">13px</option>
          <option value="15px">15px</option>
          <option value="18px">18px</option>
          <option value="22px">22px</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>默认标题级别</label>
        <select v-model="form.document.heading" class="global-input">
          <option value="p">正文</option>
          <option value="h1">H1</option>
          <option value="h2">H2</option>
          <option value="h3">H3</option>
          <option value="h4">H4</option>
          <option value="h5">H5</option>
          <option value="h6">H6</option>
        </select>
      </div>
    </div>

    <div class="app-group">
      <h3 class="app-group-title">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        专注计时
      </h3>
      <div class="global-form-group">
        <label>默认模式</label>
        <select v-model="form.focusTimer.mode" class="global-input">
          <option value="pomodoro">番茄钟</option>
          <option value="deep">深度专注</option>
          <option value="custom">自定义</option>
        </select>
      </div>
      <div class="global-form-group">
        <label>工作时长 (分钟)</label>
        <input type="number" v-model.number="form.focusTimer.workDuration" class="global-input" min="1" max="120" />
      </div>
      <div class="global-form-group">
        <label>休息时长 (分钟)</label>
        <input type="number" v-model.number="form.focusTimer.breakDuration" class="global-input" min="1" max="60" />
      </div>
      <div class="global-form-group">
        <label>长休息时长 (分钟)</label>
        <input type="number" v-model.number="form.focusTimer.longBreakDuration" class="global-input" min="1" max="60" />
      </div>
      <div class="global-form-group">
        <label>长休息前工作轮数</label>
        <input type="number" v-model.number="form.focusTimer.sessionsBeforeLongBreak" class="global-input" min="1" max="10" />
      </div>
    </div>

    <div class="save-bar">
      <button class="save-btn" :class="{ saved: saved, 'save-error': messageType === 'error' && message }" @click="saveAll" :disabled="saving">
        <svg v-if="saved" class="check-icon" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M3.5 8.5L6.5 11.5L12.5 4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-if="saving">保存中...</span>
        <span v-else-if="saved">已保存</span>
        <span v-else>保存设置</span>
      </button>
      <button class="cancel-btn" @click="resetAll">重置</button>
      <span v-if="message && messageType === 'error'" class="save-error-text">{{ message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useSettings } from '@/composables/useSettings'
import api from '@/utils/api'

const { settings, updateApp } = useSettings()

const form = reactive({
  defaultMode: settings.value.app.defaultMode,
  weather: { ...settings.value.app.weather },
  email: { ...settings.value.app.email },
  screenRecorder: { ...settings.value.app.screenRecorder },
  ppt: { ...settings.value.app.ppt },
  pdf: { ...settings.value.app.pdf },
  video: { ...settings.value.app.video },
  image: { ...settings.value.app.image },
  document: { ...settings.value.app.document },
  focusTimer: { ...settings.value.app.focusTimer },
})

const saving = ref(false)
const saved = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const weatherSearch = ref('')
const weatherResults = ref<any[]>([])
let weatherTimer: ReturnType<typeof setTimeout> | null = null

async function onWeatherSearch() {
  if (weatherTimer) clearTimeout(weatherTimer)
  if (!weatherSearch.value.trim()) {
    weatherResults.value = []
    return
  }
  weatherTimer = setTimeout(async () => {
    try {
      const res = await api.get('/ai/workspace/weather/cities', { params: { q: weatherSearch.value } })
      weatherResults.value = res.data?.cities || res.data || []
    } catch {
      weatherResults.value = []
    }
  }, 300)
}

function selectWeatherCity(city: any) {
  form.weather.cityId = city.id
  form.weather.cityName = city.name
  form.weather.country = city.country
  weatherSearch.value = ''
  weatherResults.value = []
}

async function saveAll() {
  saving.value = true
  message.value = ''
  saved.value = false
  try {
    await updateApp({
      defaultMode: form.defaultMode,
      weather: form.weather,
      email: form.email,
      screenRecorder: form.screenRecorder,
      ppt: form.ppt,
      pdf: form.pdf,
      video: form.video,
      image: form.image,
      document: form.document,
      focusTimer: form.focusTimer,
    })
    saved.value = true
    messageType.value = 'success'
    setTimeout(() => { saved.value = false }, 1500)
  } catch (e: any) {
    message.value = e.message || '保存失败'
    messageType.value = 'error'
    setTimeout(() => { message.value = '' }, 3000)
  } finally {
    saving.value = false
  }
}

function resetAll() {
  const app = settings.value.app
  form.defaultMode = app.defaultMode
  Object.assign(form.weather, app.weather)
  Object.assign(form.email, app.email)
  Object.assign(form.screenRecorder, app.screenRecorder)
  Object.assign(form.ppt, app.ppt)
  Object.assign(form.pdf, app.pdf)
  Object.assign(form.video, app.video)
  Object.assign(form.image, app.image)
  Object.assign(form.document, app.document)
  Object.assign(form.focusTimer, app.focusTimer)
}
</script>

<style scoped>
.settings-section {
  max-width: 600px;
}

.setting-hint {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #888);
  margin-top: 2px;
}

.app-settings-divider {
  height: 1px;
  background: var(--border-color);
  margin: 20px 0;
}

.app-group {
  margin-bottom: 24px;
  padding: 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
}

.app-group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-color);
}

.toggle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.toggle-row input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.city-search-row {
  position: relative;
}

.city-input {
  width: 100%;
}

.city-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.city-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.city-item:hover {
  background: var(--border-color);
}

.city-detail {
  font-size: 11px;
  color: var(--text-secondary);
}

.range-input {
  width: calc(100% - 50px);
  vertical-align: middle;
}

.range-value {
  display: inline-block;
  width: 40px;
  text-align: right;
  font-size: 12px;
  color: var(--text-secondary);
  margin-left: 8px;
}

.save-bar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-top: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.save-btn {
  padding: 6px 20px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  background: var(--primary-color);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.save-btn:hover {
  opacity: 0.9;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.save-btn.saved {
  background: var(--text-secondary);
  animation: save-pop 0.35s ease;
}

.save-btn.save-error {
  background: var(--text-primary);
  animation: save-shake 0.4s ease;
}

.check-icon {
  width: 14px;
  height: 14px;
}

@keyframes save-pop {
  0% { transform: scale(1); }
  40% { transform: scale(1.08); }
  100% { transform: scale(1); }
}

@keyframes save-shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-3px); }
  40% { transform: translateX(3px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
}

.cancel-btn {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  cursor: pointer;
}

.cancel-btn:hover {
  background: var(--border-color);
}

.save-error-text {
  font-size: 12px;
  color: #ef4444;
  margin-left: 4px;
}
</style>
