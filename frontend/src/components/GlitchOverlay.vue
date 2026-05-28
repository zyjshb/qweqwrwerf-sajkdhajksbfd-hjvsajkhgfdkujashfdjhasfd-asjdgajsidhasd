<template>
  <div class="absolute inset-0 pointer-events-none z-30 overflow-hidden">
    <!-- Scanlines -->
    <div
      v-if="activeGlitches.has('scanlines')"
      class="absolute inset-0"
      style="background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.15) 2px, rgba(0,0,0,0.15) 4px);"
    ></div>

    <!-- Static noise -->
    <div
      v-if="activeGlitches.has('static_noise')"
      class="absolute inset-0"
      :style="staticNoiseStyle"
    ></div>

    <!-- Blood pulse overlay -->
    <div
      v-if="activeGlitches.has('blood_pulse')"
      class="absolute inset-0 animate-pulse"
      style="background: radial-gradient(ellipse at center, transparent 50%, rgba(180,0,0,0.4) 100%);"
    ></div>

    <!-- Chromatic tear (RGB split edges) -->
    <div
      v-if="activeGlitches.has('chromatic_tear')"
      class="absolute inset-0"
    >
      <div class="absolute top-0 right-0 w-2 h-full bg-red-900/30"></div>
      <div class="absolute top-0 left-0 w-2 h-full bg-cyan-900/20"></div>
    </div>

    <!-- Screen tear lines -->
    <div
      v-if="activeGlitches.has('screen_tear')"
      class="absolute inset-0"
    >
      <div
        v-for="i in 8"
        :key="'tear-' + i"
        class="absolute w-full bg-white/20"
        :style="{ top: (i * 73 + 17) % 100 + '%', height: (2 + i % 6) + 'px' }"
      ></div>
    </div>

    <!-- Color invert flash -->
    <div
      v-if="activeGlitches.has('color_invert')"
      class="absolute inset-0"
      style="mix-blend-mode: difference; background: rgba(255,0,0,0.15);"
    ></div>

    <!-- Widget melt: CSS filter -->
    <div
      v-if="activeGlitches.has('widget_melt')"
      class="absolute inset-0"
      style="backdrop-filter: blur(0px); mask-image: linear-gradient(to bottom, black 60%, transparent 100%);"
    ></div>

    <!-- Vignette squeeze -->
    <div
      v-if="activeGlitches.has('vignette_squeeze')"
      class="absolute inset-0"
      style="background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.8) 100%);"
    ></div>

    <!-- Fake error popup -->
    <div
      v-if="activeGlitches.has('fake_error')"
      class="absolute top-1/3 left-1/4 bg-[#000080] border-2 border-white text-white p-4 font-mono text-xs z-40 pointer-events-auto"
    >
      <div class="flex items-center gap-2 mb-2">
        <span class="font-bold">SYSTEM ERROR</span>
        <span class="text-gray-400">0x0000007B</span>
      </div>
      <div class="text-gray-300">
        INACCESSIBLE_BOOT_DEVICE<br/>
        A fatal exception has occurred.<br/>
        The current application will be terminated.
      </div>
      <div class="flex gap-2 mt-3">
        <button class="px-3 py-1 border border-white bg-gray-600 text-white text-xs">OK</button>
        <button class="px-3 py-1 border border-white bg-gray-600 text-white text-xs">Cancel</button>
      </div>
    </div>

    <!-- Subliminal text flash -->
    <div
      v-if="activeGlitches.has('subliminal_popup')"
      class="absolute inset-0 flex items-center justify-center z-40"
    >
      <div
        class="text-6xl text-blood font-bold animate-pulse"
        v-text="subliminalText"
      ></div>
    </div>

    <!-- Mouse magnetic pull visual indicator -->
    <div
      v-if="activeGlitches.has('mouse_attract')"
      class="absolute w-4 h-4 border border-blood rounded-full"
      style="top: 50%; left: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 20px rgba(200,0,0,0.5);"
    ></div>

    <!-- Blood drips -->
    <div
      v-if="activeGlitches.has('blood_drips')"
      class="absolute inset-0 overflow-hidden"
    >
      <div
        v-for="i in 6"
        :key="'drip-' + i"
        class="absolute w-1 bg-red-900/50 animate-blood-drip"
        :style="{ left: (i * 137 + 30) % 100 + '%', animationDelay: (i * 0.5) + 's' }"
        style="height: 80px;"
      ></div>
    </div>

    <!-- Ghost text: ephemeral large text -->
    <div
      v-if="activeGlitches.has('ghost_text')"
      class="absolute inset-0 flex items-center justify-center z-40"
    >
      <div class="text-5xl text-blood font-bold animate-pulse opacity-80" v-text="ghostTextContent"></div>
    </div>

    <!-- Evaporate: chat blur flicker -->
    <div
      v-if="activeGlitches.has('evaporate')"
      class="absolute inset-0 z-20 animate-evaporate-flicker"
      style="backdrop-filter: blur(2px); filter: contrast(0.6) blur(1.5px);"
    ></div>

    <!-- Suffocation: full-screen black with large text -->
    <div
      v-if="activeGlitches.has('suffocation')"
      class="absolute inset-0 z-50 flex items-center justify-center bg-black"
    >
      <div class="text-6xl text-blood font-bold text-center whitespace-pre-line" v-text="suffocationText"></div>
    </div>

    <!-- Dialogue overlap: large overlapped text -->
    <div
      v-if="activeGlitches.has('dialogue_overlap')"
      class="absolute inset-0 flex items-center justify-center z-35"
    >
      <div
        v-for="i in 5"
        :key="'overlap-' + i"
        class="absolute text-blood font-bold opacity-50"
        :style="{ fontSize: (24 + i * 12) + 'px', transform: 'rotate(' + ((i - 2) * 8) + 'deg) translateY(' + ((i - 2) * 15) + 'px)' }"
        v-text="overlapText"
      ></div>
    </div>

    <!-- Scream radial lines -->
    <div v-if="activeGlitches.has('scream_radial')" class="absolute inset-0 z-30">
      <canvas ref="screamCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>

    <!-- Dungeon grid -->
    <div
      v-if="activeGlitches.has('dungeon_grid')"
      class="absolute inset-0 z-30"
      :style="{ backgroundImage: 'linear-gradient(rgba(60,0,0,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(60,0,0,0.3) 1px, transparent 1px)', backgroundSize: '40px 40px' }"
    ></div>

    <!-- Corruption blocks: random data-corruption rects -->
    <div v-if="activeGlitches.has('corruption_blocks')" class="absolute inset-0 z-35">
      <div
        v-for="b in corruptionBlocks"
        :key="'corrupt-' + b.i"
        class="absolute"
        :style="{ left: b.x + 'px', top: b.y + 'px', width: b.w + 'px', height: b.h + 'px', backgroundColor: b.color }"
      ></div>
    </div>

    <!-- Blood splatter: CSS radial gradients -->
    <div
      v-if="activeGlitches.has('blood_splatter')"
      class="absolute inset-0 z-30"
      :style="{ backgroundImage: bloodSplatterStyle }"
    ></div>

    <!-- Pixel melt: vertical drip lines -->
    <div v-if="activeGlitches.has('pixel_melt')" class="absolute inset-0 z-35">
      <canvas ref="meltCanvas" class="absolute inset-0 w-full h-full"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  activeGlitches: { type: Set, default: () => new Set() },
  suspicion: { type: Number, default: 20 },
  language: { type: String, default: '中文' },
})

const subliminalTexts = [
  '你是我的', '離さない', '永遠に', 'DON\'T LEAVE',
  '愛してる', '看着 我', 'ずっと一緒',
]
const subliminalText = ref('你是我的')

// Rotate subliminal messages
watch(() => props.activeGlitches.has('subliminal_popup'), (active) => {
  if (active) {
    let i = 0
    const timer = setInterval(() => {
      subliminalText.value = subliminalTexts[i % subliminalTexts.length]
      i++
    }, 150)
    setTimeout(() => clearInterval(timer), 2000)
  }
})

// ── ghost_text ──
const ghostTextLang = {
  '中文': '纱希: 看着我看着我看着我看着我看着我',
  'English': 'Saki: look at me look at me look at me',
  '日本語': '紗希: 見て見て見て見て見て',
}
const ghostTextContent = ref('')
watch(() => props.activeGlitches.has('ghost_text'), (active) => {
  if (active) {
    ghostTextContent.value = ghostTextLang[props.language] || ghostTextLang['中文']
  }
})

// ── suffocation ──
const suffocationTexts = {
  '中文': '看 着 我 ！\n👁️ 👁️',
  'English': 'LOOK AT ME!\n👁️ 👁️',
  '日本語': 'こ っ ち を 見 て ！\n👁️ 👁️',
}
const suffocationText = computed(() => suffocationTexts[props.language] || suffocationTexts['中文'])

// ── dialogue_overlap ──
const overlapTexts = {
  '中文': '你是我的你是我的你是我的',
  'English': 'you are mine you are mine',
  '日本語': 'あなたは私のものあなたは私のもの',
}
const overlapText = computed(() => overlapTexts[props.language] || overlapTexts['中文'])

// ── corruption_blocks ──
const corruptionBlocks = ref([])
watch(() => props.activeGlitches.has('corruption_blocks'), (active) => {
  if (active) {
    const blocks = []
    const count = 6 + Math.floor(Math.random() * 10)
    const colors = ['rgba(180,0,0,0.5)', 'rgba(0,180,180,0.3)', 'rgba(0,0,0,0.7)', 'rgba(200,0,200,0.25)']
    for (let i = 0; i < count; i++) {
      blocks.push({
        i,
        x: Math.floor(Math.random() * 1000),
        y: Math.floor(Math.random() * 700),
        w: 20 + Math.floor(Math.random() * 100),
        h: 8 + Math.floor(Math.random() * 60),
        color: colors[Math.floor(Math.random() * colors.length)],
      })
    }
    corruptionBlocks.value = blocks
  } else {
    corruptionBlocks.value = []
  }
})

// ── blood_splatter ──
const bloodSplatterStyle = computed(() => {
  const splats = []
  for (let i = 0; i < 8; i++) {
    const x = 10 + Math.random() * 80
    const y = 10 + Math.random() * 80
    const s = 15 + Math.random() * 40
    const r = 120 + Math.floor(Math.random() * 60)
    const g = 0
    const b = 10 + Math.floor(Math.random() * 15)
    splats.push(`radial-gradient(ellipse at ${x}% ${y}%, rgba(${r},${g},${b},0.5) 0%, transparent ${s}%)`)
  }
  return splats.join(', ')
})

// ── scream_radial canvas ──
const screamCanvas = ref(null)
watch(() => props.activeGlitches.has('scream_radial'), async (active) => {
  if (active) {
    await nextTick()
    const cvs = screamCanvas.value
    if (!cvs) return
    const ctx = cvs.getContext('2d')
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    cvs.width = cvs.offsetWidth
    cvs.height = cvs.offsetHeight
    const cx = cvs.width / 2, cy = cvs.height / 2
    const count = 30 + Math.floor(Math.random() * 30)
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2 + (Math.random() - 0.5) * 0.3
      const len = cvs.width * (0.3 + Math.random() * 0.7)
      ctx.beginPath()
      ctx.moveTo(cx, cy)
      ctx.lineTo(cx + Math.cos(angle) * len, cy + Math.sin(angle) * len)
      ctx.strokeStyle = `rgba(200,${Math.floor(Math.random() * 40)},${Math.floor(Math.random() * 20)},${0.3 + Math.random() * 0.4})`
      ctx.lineWidth = 1 + Math.random() * 2
      ctx.stroke()
    }
  }
})

// ── pixel_melt canvas ──
const meltCanvas = ref(null)
watch(() => props.activeGlitches.has('pixel_melt'), async (active) => {
  if (active) {
    await nextTick()
    const cvs = meltCanvas.value
    if (!cvs) return
    const ctx = cvs.getContext('2d')
    ctx.clearRect(0, 0, cvs.width, cvs.height)
    cvs.width = cvs.offsetWidth
    cvs.height = cvs.offsetHeight
    const count = 20 + Math.floor(Math.random() * 30)
    for (let i = 0; i < count; i++) {
      const x = Math.random() * cvs.width
      const h = 30 + Math.random() * 150
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x + (Math.random() - 0.5) * 6, h)
      ctx.strokeStyle = `rgba(180,${Math.floor(Math.random() * 30)},${Math.floor(Math.random() * 20)},${0.2 + Math.random() * 0.5})`
      ctx.lineWidth = 1 + Math.random() * 2
      ctx.stroke()
    }
  }
})

const staticNoiseStyle = computed(() => {
  return {
    background: `
      repeating-linear-gradient(
        0deg,
        rgba(200,0,0,${0.05 + props.suspicion / 500}) 0px,
        transparent 1px,
        rgba(0,0,0,${0.05 + props.suspicion / 1000}) 2px,
        transparent 3px
      ),
      repeating-linear-gradient(
        90deg,
        rgba(200,0,0,${0.03 + props.suspicion / 800}) 0px,
        transparent 1px,
        rgba(0,0,0,${0.03 + props.suspicion / 1000}) 2px,
        transparent 3px
      )
    `,
  }
})
</script>
