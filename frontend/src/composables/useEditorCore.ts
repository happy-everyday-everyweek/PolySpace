import { ref, shallowRef, triggerRef, computed } from 'vue'
import api from '../utils/api'

type ClipType = 'video' | 'audio' | 'subtitle' | 'image' | 'text' | 'sticker'
type TrackType = 'video' | 'audio' | 'subtitle'

interface KeyframeData {
  id: string
  time: number
  property: string
  value: unknown
  ease: string
}

interface TimelineClip {
  id: string
  name: string
  trackId: string
  startTime: number
  duration: number
  trimStart: number
  trimEnd: number
  file?: File
  previewUrl?: string
  type: ClipType
  text?: string
  volume: number
  muted: boolean
  hidden: boolean
  opacity: number
  playbackRate: number
  rotation: number
  scale: number
  x: number
  y: number
  speed: number
  blur: number
  brightness: number
  contrast: number
  saturation: number
  hueRotate: number
  filterPreset: string
  filterCustom: string
  transitionIn: string
  transitionOut: string
  transitionDuration: number
  keyframes: KeyframeData[]
}

interface TimelineTrack {
  id: string
  name: string
  type: TrackType
  clips: TimelineClip[]
  muted: boolean
  hidden: boolean
  height: number
}

interface AssetItem {
  id: string
  name: string
  type: string
  category: string
  src: string
  thumbnail: string
  tags: string[]
  metadata: Record<string, unknown>
  packId: string
}

interface AssetPack {
  packId: string
  name: string
  version: string
  author: string
  description: string
  itemCount: number
  items: AssetItem[]
}

interface FilterPreset {
  label: string
  css: string
}

interface TransitionPreset {
  label: string
  type: string
  duration?: number
  direction?: string
}

interface AISuggestion {
  type: string
  description: string
  confidence: number
}

interface AIEditStep {
  action: string
  reason: string
  clip_index?: number
  params?: Record<string, unknown>
}

interface AIStyleAnalysis {
  mood?: string
  pace?: string
  genre_suggestion?: string
  color_palette?: string[]
  recommended_transitions?: string[]
}

interface AISubtitle {
  start_time: string
  end_time: string
  text: string
}

interface AIAnalysisResult {
  suggestions?: AISuggestion[]
  auto_edit_plan?: { steps: AIEditStep[] }
  style_analysis?: AIStyleAnalysis
  subtitles?: AISubtitle[]
  result?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ExportOptions {
  format: 'mp4' | 'webm' | 'gif' | 'mov'
  quality: 'low' | 'medium' | 'high' | 'draft' | 'standard'
  resolution: string
  includeSubtitles: boolean
  fps: 24 | 30 | 60
}

interface Command {
  execute(): void
  undo(): void
  description: string
}

const DEFAULT_CLIP: Omit<TimelineClip, 'id' | 'trackId' | 'name' | 'type' | 'startTime' | 'duration' | 'trimStart' | 'trimEnd'> = {
  volume: 1, muted: false, hidden: false, opacity: 1, playbackRate: 1,
  rotation: 0, scale: 1, x: 0, y: 0, speed: 1,
  blur: 0, brightness: 100, contrast: 100, saturation: 100, hueRotate: 0,
  filterPreset: '', filterCustom: '',
  transitionIn: '', transitionOut: '', transitionDuration: 0.5,
  keyframes: [],
}

function generateId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`
}

class CommandManager {
  private history: Command[] = []
  private redoStack: Command[] = []
  canUndo = ref(false)
  canRedo = ref(false)
  private maxHistory = 100

  execute(command: Command) {
    command.execute()
    this.history.push(command)
    if (this.history.length > this.maxHistory) this.history.shift()
    this.redoStack = []
    this.canUndo.value = true
    this.canRedo.value = false
  }

  undo() {
    const command = this.history.pop()
    if (!command) return
    command.undo()
    this.redoStack.push(command)
    this.canUndo.value = this.history.length > 0
    this.canRedo.value = true
  }

  redo() {
    const command = this.redoStack.pop()
    if (!command) return
    command.execute()
    this.history.push(command)
    this.canUndo.value = true
    this.canRedo.value = this.redoStack.length > 0
  }

  clear() {
    this.history = []
    this.redoStack = []
    this.canUndo.value = false
    this.canRedo.value = false
  }
}

class PlaybackManager {
  isPlaying = ref(false)
  currentTime = ref(0)
  duration = ref(0)
  volume = ref(1)
  playbackRate = ref(1)
  private videoElement: HTMLVideoElement | null = null
  private animFrame: number | null = null

  attachVideo(el: HTMLVideoElement) {
    this.detachVideo()
    this.videoElement = el
    el.addEventListener('loadedmetadata', this._onMeta)
    el.addEventListener('ended', this._onEnded)
    el.addEventListener('timeupdate', this._onTimeUpdate)
  }

  detachVideo() {
    if (this.videoElement) {
      this.videoElement.removeEventListener('loadedmetadata', this._onMeta)
      this.videoElement.removeEventListener('ended', this._onEnded)
      this.videoElement.removeEventListener('timeupdate', this._onTimeUpdate)
      this.videoElement = null
    }
    this.stopTick()
  }

  play() {
    if (!this.videoElement) return
    this.videoElement.play().catch(() => {})
    this.isPlaying.value = true
    this.startTick()
  }

  pause() {
    if (!this.videoElement) return
    this.videoElement.pause()
    this.isPlaying.value = false
    this.stopTick()
  }

  togglePlay() { this.isPlaying.value ? this.pause() : this.play() }

  seek(time: number) {
    if (!this.videoElement) return
    this.videoElement.currentTime = Math.max(0, Math.min(time, this.duration.value))
    this.currentTime.value = this.videoElement.currentTime
  }

  skipBack(seconds = 5) { this.seek(this.currentTime.value - seconds) }
  skipForward(seconds = 5) { this.seek(this.currentTime.value + seconds) }

  setVolume(v: number) {
    this.volume.value = Math.max(0, Math.min(1, v))
    if (this.videoElement) this.videoElement.volume = this.volume.value
  }

  setPlaybackRate(rate: number) {
    this.playbackRate.value = Math.max(0.25, Math.min(4, rate))
    if (this.videoElement) this.videoElement.playbackRate = this.playbackRate.value
  }

  private _onMeta = () => {
    if (this.videoElement) this.duration.value = this.videoElement.duration
  }
  private _onEnded = () => { this.isPlaying.value = false; this.stopTick() }
  private _onTimeUpdate = () => {
    if (this.videoElement && !this.isPlaying.value) this.currentTime.value = this.videoElement.currentTime
  }
  private startTick() {
    this.stopTick()
    const tick = () => {
      if (!this.isPlaying.value || !this.videoElement) return
      this.currentTime.value = this.videoElement.currentTime
      this.animFrame = requestAnimationFrame(tick)
    }
    this.animFrame = requestAnimationFrame(tick)
  }
  private stopTick() {
    if (this.animFrame !== null) { cancelAnimationFrame(this.animFrame); this.animFrame = null }
  }
}

class TimelineManager {
  tracks = shallowRef<TimelineTrack[]>([])
  selectedClipId = ref<string | null>(null)
  selectedTrackId = ref<string | null>(null)
  zoomLevel = ref(5)
  scrollLeft = ref(0)
  snapEnabled = ref(true)
  snapThreshold = 8

  get pxPerSec() { return this.zoomLevel.value * 2 }

  get selectedClip(): TimelineClip | null {
    if (!this.selectedClipId.value) return null
    for (const track of this.tracks.value) {
      const clip = track.clips.find(c => c.id === this.selectedClipId.value)
      if (clip) return clip
    }
    return null
  }

  findClipTrack(clipId: string): { track: TimelineTrack; clip: TimelineClip } | null {
    for (const track of this.tracks.value) {
      const clip = track.clips.find(c => c.id === clipId)
      if (clip) return { track, clip }
    }
    return null
  }

  setTracks(newTracks: TimelineTrack[]) {
    this.tracks.value = newTracks
    triggerRef(this.tracks)
  }

  addTrack(type: TrackType, name?: string): string {
    const id = generateId('track')
    const track: TimelineTrack = {
      id,
      name: name || (type === 'video' ? '视频' : type === 'audio' ? '音频' : '字幕'),
      type, clips: [], muted: false, hidden: false, height: 40,
    }
    this.setTracks([...this.tracks.value, track])
    return id
  }

  removeTrack(trackId: string) {
    this.setTracks(this.tracks.value.filter(t => t.id !== trackId))
  }

  addClip(trackId: string, clip: Omit<TimelineClip, 'id' | 'trackId'>): string {
    const id = generateId('clip')
    const newClip: TimelineClip = { ...clip, id, trackId }
    this.setTracks(this.tracks.value.map(t => t.id === trackId ? { ...t, clips: [...t.clips, newClip] } : t))
    return id
  }

  removeClip(clipId: string) {
    this.setTracks(this.tracks.value.map(t => ({ ...t, clips: t.clips.filter(c => c.id !== clipId) })))
    if (this.selectedClipId.value === clipId) this.selectedClipId.value = null
  }

  updateClip(clipId: string, updates: Partial<TimelineClip>) {
    this.setTracks(this.tracks.value.map(t => ({
      ...t,
      clips: t.clips.map(c => (c.id === clipId ? { ...c, ...updates } : c)),
    })))
  }

  moveClip(clipId: string, newStartTime: number, newTrackId?: string) {
    let snappedTime = this.snapEnabled.value ? this.snap(newStartTime) : newStartTime
    snappedTime = Math.max(0, snappedTime)
    if (newTrackId) {
      const sourceClip = this.tracks.value.flatMap(t => t.clips).find(c => c.id === clipId)
      if (!sourceClip) return
      const movedClip = { ...sourceClip, trackId: newTrackId, startTime: snappedTime }
      this.setTracks(this.tracks.value.map(t => {
        if (t.id === newTrackId) return { ...t, clips: [...t.clips, movedClip] }
        return { ...t, clips: t.clips.filter(c => c.id !== clipId) }
      }))
    } else {
      this.setTracks(this.tracks.value.map(t => ({
        ...t,
        clips: t.clips.map(c => c.id === clipId ? { ...c, startTime: snappedTime } : c),
      })))
    }
  }

  splitClip(clipId: string, splitTime: number): { leftId: string; rightId: string } | null {
    const found = this.findClipTrack(clipId)
    if (!found) return null
    const { clip } = found
    const relativeTime = splitTime - clip.startTime
    if (relativeTime <= 0 || relativeTime >= clip.duration) return null
    const leftId = generateId('clip')
    const rightId = generateId('clip')
    const leftClip: TimelineClip = { ...clip, id: leftId, duration: relativeTime, trimEnd: clip.trimEnd + (clip.duration - relativeTime) }
    const rightClip: TimelineClip = { ...clip, id: rightId, startTime: splitTime, duration: clip.duration - relativeTime, trimStart: clip.trimStart + relativeTime }
    this.setTracks(this.tracks.value.map(t => ({ ...t, clips: [...t.clips.filter(c => c.id !== clipId), leftClip, rightClip] })))
    return { leftId, rightId }
  }

  addKeyframe(clipId: string, keyframe: Omit<KeyframeData, 'id'>): string {
    const kfId = generateId('kf')
    const kf: KeyframeData = { ...keyframe, id: kfId }
    this.setTracks(this.tracks.value.map(t => ({
      ...t,
      clips: t.clips.map(c => c.id === clipId ? { ...c, keyframes: [...c.keyframes, kf] } : c),
    })))
    return kfId
  }

  removeKeyframe(clipId: string, keyframeId: string) {
    this.setTracks(this.tracks.value.map(t => ({
      ...t,
      clips: t.clips.map(c => c.id === clipId ? { ...c, keyframes: c.keyframes.filter(kf => kf.id !== keyframeId) } : c),
    })))
  }

  updateKeyframe(clipId: string, keyframeId: string, updates: Partial<KeyframeData>) {
    this.setTracks(this.tracks.value.map(t => ({
      ...t,
      clips: t.clips.map(c => c.id === clipId ? {
        ...c,
        keyframes: c.keyframes.map(kf => kf.id === keyframeId ? { ...kf, ...updates } : kf),
      } : c),
    })))
  }

  toggleTrackMute(trackId: string) {
    this.setTracks(this.tracks.value.map(t => t.id === trackId ? { ...t, muted: !t.muted } : t))
  }

  toggleTrackHidden(trackId: string) {
    this.setTracks(this.tracks.value.map(t => t.id === trackId ? { ...t, hidden: !t.hidden } : t))
  }

  private snap(time: number): number {
    const threshold = this.snapThreshold / this.pxPerSec
    for (const track of this.tracks.value) {
      for (const clip of track.clips) {
        if (Math.abs(time - clip.startTime) < threshold) return clip.startTime
        const clipEnd = clip.startTime + clip.duration
        if (Math.abs(time - clipEnd) < threshold) return clipEnd
      }
    }
    return time
  }

  getTotalDuration(): number {
    let max = 0
    for (const track of this.tracks.value) {
      for (const clip of track.clips) {
        const end = clip.startTime + clip.duration
        if (end > max) max = end
      }
    }
    return max
  }

  selectClip(clipId: string | null) { this.selectedClipId.value = clipId }

  clear() {
    this.setTracks([])
    this.selectedClipId.value = null
    this.selectedTrackId.value = null
  }
}

class EditorCore {
  private static instance: EditorCore | null = null
  readonly command = new CommandManager()
  readonly playback = new PlaybackManager()
  readonly timeline = new TimelineManager()
  private objectUrls: Set<string> = new Set()
  filterPresets = ref<Record<string, FilterPreset>>({})
  transitionPresets = ref<Record<string, TransitionPreset>>({})
  assetPacks = ref<AssetPack[]>([])

  static getInstance(): EditorCore {
    if (!EditorCore.instance) EditorCore.instance = new EditorCore()
    return EditorCore.instance
  }

  static reset(): void {
    if (EditorCore.instance) EditorCore.instance.destroy()
    EditorCore.instance = null
  }

  createObjectUrl(file: File): string {
    const url = URL.createObjectURL(file)
    this.objectUrls.add(url)
    return url
  }

  revokeObjectUrl(url: string) {
    if (this.objectUrls.has(url)) { URL.revokeObjectURL(url); this.objectUrls.delete(url) }
  }

  destroy() {
    for (const url of this.objectUrls) URL.revokeObjectURL(url)
    this.objectUrls.clear()
    this.playback.detachVideo()
    this.timeline.clear()
    this.command.clear()
  }

  initDefaultTracks() {
    if (this.timeline.tracks.value.length === 0) {
      this.timeline.addTrack('video', '视频 1')
      this.timeline.addTrack('audio', '音频 1')
      this.timeline.addTrack('subtitle', '字幕')
    }
  }

  async loadFilterPresets() {
    try {
      const res = await api.post('/tools/call/clip_editor', { action: 'get_filter_presets' })
      if (res.data?.result?.presets) this.filterPresets.value = res.data.result.presets
    } catch { /* ignore */ }
  }

  async loadTransitionPresets() {
    try {
      const res = await api.post('/tools/call/clip_editor', { action: 'get_transition_presets' })
      if (res.data?.result?.presets) this.transitionPresets.value = res.data.result.presets
    } catch { /* ignore */ }
  }

  async loadAssetPacks() {
    try {
      const res = await api.post('/tools/call/clip_editor', { action: 'list_asset_packs' })
      if (res.data?.result?.packs) this.assetPacks.value = res.data.result.packs
    } catch { /* ignore */ }
  }

  async importAssetPack(zipPath: string): Promise<boolean> {
    try {
      const res = await api.post('/tools/call/clip_editor', { action: 'import_asset_pack', zip_path: zipPath })
      if (res.data?.result?.success) { await this.loadAssetPacks(); return true }
      return false
    } catch { return false }
  }

  async applyFilter(compositionId: string, elementId: string, filterPreset: string, adjustments?: Record<string, number>) {
    try {
      await api.post('/tools/call/clip_editor', {
        action: 'apply_filter', composition_id: compositionId, element_id: elementId,
        filter_preset: filterPreset, adjustments,
      })
    } catch { /* ignore */ }
  }

  async aiColorGrade(compositionId: string, elementId: string, style: string) {
    try {
      const res = await api.post('/tools/call/clip_editor', {
        action: 'ai_color_grade', composition_id: compositionId, element_id: elementId, style,
      })
      return res.data?.result
    } catch { return null }
  }
}

function createAddClipCommand(timeline: TimelineManager, trackId: string, clipData: Omit<TimelineClip, 'id' | 'trackId'>): Command {
  let clipId: string | null = null
  return {
    description: `添加片段 "${clipData.name}"`,
    execute() { clipId = timeline.addClip(trackId, clipData) },
    undo() { if (clipId) timeline.removeClip(clipId) },
  }
}

function createRemoveClipCommand(timeline: TimelineManager, clipId: string): Command {
  const found = timeline.findClipTrack(clipId)
  if (!found) return { description: '删除片段 (未找到)', execute() {}, undo() {} }
  const { track, clip } = found
  const trackId = track.id
  const clipData = { ...clip }
  return {
    description: `删除片段 "${clip.name}"`,
    execute() { timeline.removeClip(clipId) },
    undo() { timeline.addClip(trackId, clipData) },
  }
}

function createUpdateClipCommand(timeline: TimelineManager, clipId: string, updates: Partial<TimelineClip>): Command {
  const found = timeline.findClipTrack(clipId)
  if (!found) return { description: '更新片段 (未找到)', execute() {}, undo() {} }
  const previousValues: Record<string, unknown> = {}
  for (const key of Object.keys(updates)) previousValues[key] = found.clip[key as keyof TimelineClip]
  return {
    description: `更新片段 "${found.clip.name}"`,
    execute() { timeline.updateClip(clipId, updates) },
    undo() { timeline.updateClip(clipId, previousValues) },
  }
}

function createMoveClipCommand(timeline: TimelineManager, clipId: string, newStartTime: number, newTrackId?: string): Command {
  const found = timeline.findClipTrack(clipId)
  if (!found) return { description: '移动片段 (未找到)', execute() {}, undo() {} }
  const oldStartTime = found.clip.startTime
  const oldTrackId = found.track.id
  return {
    description: `移动片段 "${found.clip.name}"`,
    execute() { timeline.moveClip(clipId, newStartTime, newTrackId) },
    undo() { timeline.moveClip(clipId, oldStartTime, oldTrackId) },
  }
}

function createSplitClipCommand(timeline: TimelineManager, clipId: string, splitTime: number): Command {
  const found = timeline.findClipTrack(clipId)
  if (!found) return { description: '分割片段 (未找到)', execute() {}, undo() {} }
  const originalClip = { ...found.clip }
  const trackId = found.track.id
  let splitResult: { leftId: string; rightId: string } | null = null
  return {
    description: `分割片段 "${found.clip.name}"`,
    execute() { splitResult = timeline.splitClip(clipId, splitTime) },
    undo() {
      if (splitResult) {
        timeline.removeClip(splitResult.leftId)
        timeline.removeClip(splitResult.rightId)
        timeline.addClip(trackId, originalClip)
      }
    },
  }
}

export function useEditorCore() {
  const editor = EditorCore.getInstance()

  const undo = () => editor.command.undo()
  const redo = () => editor.command.redo()
  const canUndo = editor.command.canUndo
  const canRedo = editor.command.canRedo

  const isPlaying = editor.playback.isPlaying
  const currentTime = editor.playback.currentTime
  const duration = editor.playback.duration
  const volume = editor.playback.volume
  const playbackRate = editor.playback.playbackRate
  const togglePlay = () => editor.playback.togglePlay()
  const seek = (t: number) => editor.playback.seek(t)
  const skipBack = () => editor.playback.skipBack()
  const skipForward = () => editor.playback.skipForward()
  const attachVideo = (el: HTMLVideoElement) => editor.playback.attachVideo(el)
  const detachVideo = () => editor.playback.detachVideo()
  const setVolume = (v: number) => editor.playback.setVolume(v)
  const setPlaybackRate = (r: number) => editor.playback.setPlaybackRate(r)

  const tracks = editor.timeline.tracks
  const selectedClipId = editor.timeline.selectedClipId
  const selectedClip = computed(() => editor.timeline.selectedClip)
  const zoomLevel = editor.timeline.zoomLevel
  const pxPerSec = computed(() => editor.timeline.pxPerSec)
  const snapEnabled = editor.timeline.snapEnabled
  const filterPresets = editor.filterPresets
  const transitionPresets = editor.transitionPresets
  const assetPacks = editor.assetPacks

  const addTrack = (type: TrackType, name?: string) => editor.timeline.addTrack(type, name)
  const removeTrack = (trackId: string) => editor.timeline.removeTrack(trackId)
  const addClip = (trackId: string, clip: Omit<TimelineClip, 'id' | 'trackId'>) => {
    editor.command.execute(createAddClipCommand(editor.timeline, trackId, clip))
  }
  const removeClip = (clipId: string) => {
    editor.command.execute(createRemoveClipCommand(editor.timeline, clipId))
  }
  const updateClip = (clipId: string, updates: Partial<TimelineClip>) => {
    editor.command.execute(createUpdateClipCommand(editor.timeline, clipId, updates))
  }
  const moveClip = (clipId: string, newStartTime: number, newTrackId?: string) => {
    editor.command.execute(createMoveClipCommand(editor.timeline, clipId, newStartTime, newTrackId))
  }
  const splitClip = (clipId: string, splitTime: number) => {
    editor.command.execute(createSplitClipCommand(editor.timeline, clipId, splitTime))
  }
  const selectClip = (clipId: string | null) => editor.timeline.selectClip(clipId)
  const toggleTrackMute = (trackId: string) => editor.timeline.toggleTrackMute(trackId)
  const toggleTrackHidden = (trackId: string) => editor.timeline.toggleTrackHidden(trackId)
  const getTotalDuration = () => editor.timeline.getTotalDuration()
  const initDefaultTracks = () => editor.initDefaultTracks()

  const addKeyframe = (clipId: string, keyframe: Omit<KeyframeData, 'id'>) => {
    editor.timeline.addKeyframe(clipId, keyframe)
  }
  const removeKeyframe = (clipId: string, keyframeId: string) => {
    editor.timeline.removeKeyframe(clipId, keyframeId)
  }
  const updateKeyframe = (clipId: string, keyframeId: string, updates: Partial<KeyframeData>) => {
    editor.timeline.updateKeyframe(clipId, keyframeId, updates)
  }

  const importVideo = (file: File): string => {
    const url = editor.createObjectUrl(file)
    initDefaultTracks()
    const videoTrack = tracks.value.find(t => t.type === 'video')
    if (videoTrack) {
      addClip(videoTrack.id, {
        ...DEFAULT_CLIP,
        name: file.name, startTime: 0, duration: 0, trimStart: 0, trimEnd: 0,
        type: 'video', file, previewUrl: url,
      })
    }
    return url
  }

  const importAudio = (file: File): string => {
    const url = editor.createObjectUrl(file)
    initDefaultTracks()
    const audioTrack = tracks.value.find(t => t.type === 'audio')
    if (audioTrack) {
      addClip(audioTrack.id, {
        ...DEFAULT_CLIP,
        name: file.name, startTime: 0, duration: 0, trimStart: 0, trimEnd: 0,
        type: 'audio', file, previewUrl: url,
      })
    }
    return url
  }

  const importSubtitle = (text: string, startTime: number, durationSec: number) => {
    initDefaultTracks()
    const subTrack = tracks.value.find(t => t.type === 'subtitle')
    if (subTrack) {
      addClip(subTrack.id, {
        ...DEFAULT_CLIP,
        name: text, startTime, duration: durationSec, trimStart: 0, trimEnd: 0,
        type: 'subtitle', text,
      })
    }
  }

  const importAssetPack = (zipPath: string) => editor.importAssetPack(zipPath)
  const loadFilterPresets = () => editor.loadFilterPresets()
  const loadTransitionPresets = () => editor.loadTransitionPresets()
  const loadAssetPacks = () => editor.loadAssetPacks()
  const applyFilter = (compId: string, elId: string, preset: string, adj?: Record<string, number>) => editor.applyFilter(compId, elId, preset, adj)
  const aiColorGrade = (compId: string, elId: string, style: string) => editor.aiColorGrade(compId, elId, style)

  const getProjectData = () => ({
    tracks: tracks.value.map(t => ({
      ...t,
      clips: t.clips.map(c => {
        const { file, previewUrl, ...data } = c
        return data
      }),
    })),
    zoomLevel: zoomLevel.value,
  })

  const clearProject = () => editor.destroy()

  return {
    editor, undo, redo, canUndo, canRedo,
    isPlaying, currentTime, duration, volume, playbackRate,
    togglePlay, seek, skipBack, skipForward, attachVideo, detachVideo,
    setVolume, setPlaybackRate,
    tracks, selectedClipId, selectedClip, zoomLevel, pxPerSec, snapEnabled,
    filterPresets, transitionPresets, assetPacks,
    addTrack, removeTrack, addClip, removeClip, updateClip, moveClip, splitClip,
    selectClip, toggleTrackMute, toggleTrackHidden,
    addKeyframe, removeKeyframe, updateKeyframe,
    getTotalDuration, initDefaultTracks,
    importVideo, importAudio, importSubtitle, importAssetPack,
    loadFilterPresets, loadTransitionPresets, loadAssetPacks,
    applyFilter, aiColorGrade,
    getProjectData, clearProject,
  }
}

export type {
  TimelineClip, TimelineTrack, Command, ClipType, TrackType,
  KeyframeData, AssetItem, AssetPack, FilterPreset, TransitionPreset,
  AIAnalysisResult, AISuggestion, AIEditStep, AIStyleAnalysis, AISubtitle,
  ChatMessage, ExportOptions,
}
export { EditorCore, CommandManager, PlaybackManager, TimelineManager, DEFAULT_CLIP }
