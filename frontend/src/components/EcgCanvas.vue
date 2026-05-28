<template>
  <canvas
    ref="canvasRef"
    class="w-full"
    :height="canvasHeight"
  ></canvas>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  suspicion: { type: Number, default: 20 },
  favorability: { type: Number, default: 50 },
  activeGlitches: { type: Set, default: () => new Set() },
})

const canvasRef = ref(null)
const canvasHeight = 60

let animFrameId = null
let phase = 0
let particles = []

// ── P-QRS-T waveform generator ─────────────────────────────────

function ecgSample(t, suspicion) {
  // Normalized cardiac cycle: P → Q → R → S → T
  const cyclePos = ((t % 1) + 1) % 1
  const fearFactor = suspicion / 100  // 0..1

  // P wave (atrial depolarization): small bump at ~0.15
  const pWave = 0.08 * Math.exp(-((cyclePos - 0.15) ** 2) / 0.0004)

  // QRS complex: sharp spike at ~0.35
  const qWave = -0.12 * Math.exp(-((cyclePos - 0.32) ** 2) / 0.0001)
  const rWave = 0.55 * Math.exp(-((cyclePos - 0.35) ** 2) / 0.0001)
  const sWave = -0.2 * Math.exp(-((cyclePos - 0.38) ** 2) / 0.0001)

  // T wave (ventricular repolarization): broad bump at ~0.6
  const tWave = 0.15 * Math.exp(-((cyclePos - 0.6) ** 2) / 0.002)

  // Fear distortions: higher suspicion = taller R, erratic baseline
  const baselineNoise = fearFactor * 0.02 * Math.sin(t * 47)
  const rAmplify = 1 + fearFactor * 1.2
  const rateFactor = 1 + fearFactor * 0.8  // faster cycle when scared

  return {
    value: (pWave + qWave + rWave * rAmplify + sWave + tWave + baselineNoise),
    rate: rateFactor,
  }
}

// ── Particles ──────────────────────────────────────────────────

function spawnParticle(w) {
  return {
    x: Math.random() * w,
    y: canvasHeight + 5,
    vy: -0.3 - Math.random() * 0.7,
    vx: (Math.random() - 0.5) * 0.3,
    size: 0.5 + Math.random() * 1.5,
    life: 1,
    decay: 0.003 + Math.random() * 0.008,
  }
}

// ── Render loop ────────────────────────────────────────────────

function render() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = canvas.width = canvas.clientWidth
  const h = canvasHeight
  const midY = h / 2

  ctx.clearRect(0, 0, w, h)

  // Background
  ctx.fillStyle = '#000000'
  ctx.fillRect(0, 0, w, h)

  // Grid lines
  ctx.strokeStyle = 'rgba(85, 0, 0, 0.2)'
  ctx.lineWidth = 0.5
  for (let y = 10; y < h; y += 15) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(w, y)
    ctx.stroke()
  }

  // ECG waveform
  const suspicion = props.suspicion
  const rateFactor = 1 + (suspicion / 100) * 0.8
  const amplitude = 20 + (suspicion / 100) * 20
  const lineColor = suspicion >= 85
    ? `rgb(${200 + Math.random() * 55}, 0, 0)`
    : suspicion >= 55
      ? 'rgb(200, 20, 20)'
      : 'rgb(180, 0, 0)'

  // Glow
  ctx.shadowColor = lineColor
  ctx.shadowBlur = 4 + (suspicion / 100) * 10

  ctx.beginPath()
  ctx.strokeStyle = lineColor
  ctx.lineWidth = 1.5

  const samples = w
  const cycleWidth = w / (3 + suspicion / 30)  // fewer visible cycles = wider

  for (let i = 0; i < samples; i++) {
    const t = phase + (i / cycleWidth) * rateFactor
    const { value } = ecgSample(t, suspicion)
    const x = i
    const y = midY - value * amplitude

    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
  ctx.shadowBlur = 0

  // Flatline on game over
  if (props.activeGlitches.has('flatline')) {
    ctx.beginPath()
    ctx.strokeStyle = '#FF0000'
    ctx.lineWidth = 2
    ctx.moveTo(0, midY)
    ctx.lineTo(w, midY)
    ctx.stroke()
  }

  // Particles (smoldering embers)
  if (particles.length < 30) {
    particles.push(spawnParticle(w))
  }

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.y += p.vy
    p.x += p.vx
    p.life -= p.decay
    if (p.life <= 0 || p.y < -10) {
      particles.splice(i, 1)
      continue
    }
    ctx.fillStyle = `rgba(180, 0, 0, ${p.life * 0.6})`
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
    ctx.fill()
  }

  // Advance phase
  phase += 0.008 * rateFactor

  animFrameId = requestAnimationFrame(render)
}

// ── Lifecycle ───────────────────────────────────────────────────

onMounted(() => {
  render()
})

onUnmounted(() => {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId)
  }
})
</script>
