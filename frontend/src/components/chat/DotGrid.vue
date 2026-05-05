<template>
  <div ref="wrapperRef" class="dot-grid-wrapper">
    <canvas ref="canvasRef" class="dot-grid-canvas" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'

interface Dot {
  cx: number
  cy: number
  xOffset: number
  yOffset: number
  vx: number
  vy: number
}

const props = withDefaults(defineProps<{
  dotSize?: number
  gap?: number
  baseColor?: string
  activeColor?: string
  proximity?: number
  excludeRect?: { x: number; y: number; w: number; h: number }
}>(), {
  dotSize: 16,
  gap: 32,
  baseColor: '#cccccc',
  activeColor: '#1a1a1a',
  proximity: 150,
})

const wrapperRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const dots = ref<Dot[]>([])

const pointer = ref({
  x: -9999,
  y: -9999,
  vx: 0,
  vy: 0,
  speed: 0,
  lastTime: 0,
  lastX: 0,
  lastY: 0,
})

function hexToRgb(hex: string) {
  const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i)
  if (!m) return { r: 0, g: 0, b: 0 }
  return {
    r: parseInt(m[1], 16),
    g: parseInt(m[2], 16),
    b: parseInt(m[3], 16),
  }
}

const baseRgb = computed(() => hexToRgb(props.baseColor))
const activeRgb = computed(() => hexToRgb(props.activeColor))

const SPRING_K = 0.15
const DAMPING = 0.85
const SPEED_TRIGGER = 100
const SHOCK_RADIUS = 250
const SHOCK_STRENGTH = 0.12

function buildGrid() {
  const wrap = wrapperRef.value
  const canvas = canvasRef.value
  if (!wrap || !canvas) return

  const { width, height } = wrap.getBoundingClientRect()
  if (width === 0 || height === 0) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = `${width}px`
  canvas.style.height = `${height}px`
  const ctx = canvas.getContext('2d')
  if (ctx) ctx.scale(dpr, dpr)

  const cell = props.dotSize + props.gap
  const cols = Math.floor((width + props.gap) / cell)
  const rows = Math.floor((height + props.gap) / cell)

  const gridW = cell * cols - props.gap
  const gridH = cell * rows - props.gap
  const startX = (width - gridW) / 2 + props.dotSize / 2
  const startY = (height - gridH) / 2 + props.dotSize / 2

  const newDots: Dot[] = []
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      const cx = startX + x * cell
      const cy = startY + y * cell
      if (props.excludeRect) {
        const er = props.excludeRect
        if (cx > er.x && cx < er.x + er.w && cy > er.y && cy < er.y + er.h) continue
      }
      newDots.push({
        cx,
        cy,
        xOffset: 0,
        yOffset: 0,
        vx: 0,
        vy: 0,
      })
    }
  }
  dots.value = newDots
}

let rafId = 0
let resizeObserver: ResizeObserver | null = null

function updatePhysics() {
  for (const dot of dots.value) {
    dot.vx += -SPRING_K * dot.xOffset
    dot.vy += -SPRING_K * dot.yOffset
    dot.vx *= DAMPING
    dot.vy *= DAMPING
    dot.xOffset += dot.vx
    dot.yOffset += dot.vy

    if (Math.abs(dot.xOffset) < 0.1 && Math.abs(dot.yOffset) < 0.1 &&
        Math.abs(dot.vx) < 0.1 && Math.abs(dot.vy) < 0.1) {
      dot.xOffset = 0
      dot.yOffset = 0
      dot.vx = 0
      dot.vy = 0
    }
  }
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  updatePhysics()
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const { x: px, y: py } = pointer.value
  const proxSq = props.proximity * props.proximity
  const dotRadius = props.dotSize / 2

  for (const dot of dots.value) {
    const ox = dot.cx + dot.xOffset
    const oy = dot.cy + dot.yOffset
    const dx = dot.cx - px
    const dy = dot.cy - py
    const dsq = dx * dx + dy * dy

    let style = props.baseColor
    if (dsq <= proxSq) {
      const dist = Math.sqrt(dsq)
      const t = 1 - dist / props.proximity
      const r = Math.round(baseRgb.value.r + (activeRgb.value.r - baseRgb.value.r) * t)
      const g = Math.round(baseRgb.value.g + (activeRgb.value.g - baseRgb.value.g) * t)
      const b = Math.round(baseRgb.value.b + (activeRgb.value.b - baseRgb.value.b) * t)
      style = `rgb(${r},${g},${b})`
    }

    ctx.beginPath()
    ctx.arc(ox, oy, dotRadius, 0, Math.PI * 2)
    ctx.fillStyle = style
    ctx.fill()
  }

  rafId = requestAnimationFrame(draw)
}

function onMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return

  const rect = canvas.getBoundingClientRect()
  if (e.clientX < rect.left || e.clientX > rect.right ||
      e.clientY < rect.top || e.clientY > rect.bottom) {
    pointer.value.x = -9999
    pointer.value.y = -9999
    return
  }

  const now = performance.now()
  const pr = pointer.value
  const dt = pr.lastTime ? now - pr.lastTime : 16
  const dx = e.clientX - pr.lastX
  const dy = e.clientY - pr.lastY

  let vx = (dx / dt) * 1000
  let vy = (dy / dt) * 1000
  let speed = Math.hypot(vx, vy)

  if (speed > 5000) {
    const scale = 5000 / speed
    vx *= scale
    vy *= scale
    speed = 5000
  }

  pr.lastTime = now
  pr.lastX = e.clientX
  pr.lastY = e.clientY
  pr.vx = vx
  pr.vy = vy
  pr.speed = speed

  pr.x = e.clientX - rect.left
  pr.y = e.clientY - rect.top

  if (speed > SPEED_TRIGGER) {
    for (const dot of dots.value) {
      const dist = Math.hypot(dot.cx - pr.x, dot.cy - pr.y)
      if (dist < props.proximity) {
        const pushX = (dot.cx - pr.x) * 0.015 + vx * 0.002
        const pushY = (dot.cy - pr.y) * 0.015 + vy * 0.002
        dot.vx += pushX
        dot.vy += pushY
      }
    }
  }
}

function onClick(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  if (e.clientX < rect.left || e.clientX > rect.right ||
      e.clientY < rect.top || e.clientY > rect.bottom) return

  const cx = e.clientX - rect.left
  const cy = e.clientY - rect.top

  for (const dot of dots.value) {
    const dist = Math.hypot(dot.cx - cx, dot.cy - cy)
    if (dist < SHOCK_RADIUS) {
      const falloff = Math.max(0, 1 - dist / SHOCK_RADIUS)
      dot.vx += (dot.cx - cx) * SHOCK_STRENGTH * falloff
      dot.vy += (dot.cy - cy) * SHOCK_STRENGTH * falloff
    }
  }
}

let lastThrottle = 0
function throttledMouseMove(e: MouseEvent) {
  const now = performance.now()
  if (now - lastThrottle >= 50) {
    lastThrottle = now
    onMouseMove(e)
  }
}

onMounted(async () => {
  await nextTick()
  buildGrid()
  draw()

  if ('ResizeObserver' in window) {
    resizeObserver = new ResizeObserver(buildGrid)
    if (wrapperRef.value) {
      resizeObserver.observe(wrapperRef.value)
    }
  }

  window.addEventListener('mousemove', throttledMouseMove, { passive: true })
  window.addEventListener('click', onClick)
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (resizeObserver) resizeObserver.disconnect()
  window.removeEventListener('mousemove', throttledMouseMove)
  window.removeEventListener('click', onClick)
})

watch([() => props.dotSize, () => props.gap, () => props.excludeRect], () => {
  buildGrid()
})

watch([() => props.baseColor, () => props.activeColor], () => {
  if (rafId) cancelAnimationFrame(rafId)
  draw()
})
</script>

<style scoped>
.dot-grid-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.dot-grid-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
