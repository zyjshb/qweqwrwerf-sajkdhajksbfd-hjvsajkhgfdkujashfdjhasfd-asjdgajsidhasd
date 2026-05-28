<template>
  <div class="flex-1 flex flex-col overflow-hidden mx-4 mb-2">
    <!-- Chat log area -->
    <div
      ref="chatLogRef"
      class="flex-1 overflow-y-auto overflow-x-hidden px-4 py-2 terminal-panel rounded-t"
      :class="{ 'animate-shake': activeGlitches.has('font_shake') }"
    >
      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="mb-3 leading-relaxed"
      >
        <!-- System messages -->
        <div v-if="msg.role === 'system'" class="text-yellow-700 text-xs">
          {{ msg.content }}
        </div>

        <!-- Agent commentary -->
        <div v-else-if="msg.role === 'agent'" class="text-purple-700 text-xs italic">
          {{ msg.content }}
        </div>

        <!-- User message -->
        <div v-else-if="msg.role === 'user'" class="flex gap-2">
          <span class="text-blood-dim shrink-0">&gt;</span>
          <span class="text-blood">{{ msg.content }}</span>
        </div>

        <!-- Assistant (Saki) message -->
        <div v-else-if="msg.role === 'assistant'" class="flex flex-col gap-1 block">
          <!-- Inner monologue (think) -->
          <div
            v-if="msg.think"
            class="text-xs italic pl-3 border-l border-red-950/40 block"
            style="color: #7f1d1d;"
          >
            {{ msg.think }}
          </div>
          <!-- Spoken text -->
          <div
            class="block font-mono"
            :style="{ color: getCharacterColor }"
            :class="{ 'animate-glitch-text': activeGlitches.has('font_shake') }"
          >
            {{ msg.content }}
          </div>
        </div>
      </div>

      <!-- Streaming speech (typewriter in progress) -->
      <div v-if="typewriterDisplay" class="mb-3 block">
        <div
          class="block font-mono"
          :style="{ color: typewriterMode === 'think' ? '#7f1d1d' : getCharacterColor }"
          :class="{ 'italic pl-3 border-l border-red-950/40': typewriterMode === 'think' }"
        >
          <span class="text-red-950/50 text-[10px] select-none" v-if="typewriterMode === 'think'">[内心] </span>
          {{ typewriterDisplay }}
          <span class="animate-pulse">_</span>
        </div>
      </div>

      <div ref="scrollAnchor"></div>
    </div>

    <!-- Input area -->
    <div class="flex items-center gap-2 p-2 terminal-panel rounded-b border-t border-blood-dim">
      <span class="text-blood-dim shrink-0">&gt;</span>
      <input
        ref="inputRef"
        v-model="inputText"
        type="text"
        :placeholder="inputPlaceholder"
        :disabled="disabled || hijackActive"
        class="flex-1 bg-transparent border-none outline-none text-blood placeholder-blood-dim text-sm font-mono"
        @keydown="handleKeydown"
        autofocus
      />
      <button
        @click="doSend"
        :disabled="disabled || hijackActive || !inputText.trim()"
        class="px-4 py-1 border border-blood-dim text-blood-dim text-xs hover:border-blood hover:text-blood transition-colors disabled:opacity-30"
      >
        SEND
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  thinkText: { type: String, default: '' },
  speechText: { type: String, default: '' },
  activeGlitches: { type: Set, default: () => new Set() },
  gameOver: { type: Boolean, default: false },
  ending: { type: Object, default: null },
  hijackActive: { type: Boolean, default: false },
  charId: { type: String, default: 'saki' },
  customCharacters: { type: Array, default: () => [] },
})

const emit = defineEmits(['send', 'restart'])

const inputText = ref('')
const inputRef = ref(null)
const chatLogRef = ref(null)
const scrollAnchor = ref(null)
const typewriterDisplay = ref('')
const typewriterMode = ref('think')

const getCharacterColor = computed(() => {
  if (!props.charId || props.charId === 'saki') return '#ef4444'
  const customChar = props.customCharacters?.find(c => c.id === props.charId || c.character_name === props.charId)
  return customChar?.text_color || '#ef4444'
})

// Hijack sequence
const hijackText = '你走不掉的你走不掉的你走不掉的...'
let hijackIndex = 0

const disabled = computed(() => props.gameOver)
const inputPlaceholder = computed(() => {
  if (props.gameOver) return '游戏结束...'
  if (props.hijackActive) return hijackText
  return '输入你想说的话...'
})

// ── Typewriter effect ──────────────────────────────────────────

let typewriterTimer = null

watch(() => props.thinkText, (text) => {
  if (!text) return
  typewriterMode.value = 'think'
  runTypewriter(text)
})

watch(() => props.speechText, (text) => {
  if (!text) return
  typewriterMode.value = 'speech'
  runTypewriter(text)
})

function runTypewriter(text) {
  if (typewriterTimer) clearInterval(typewriterTimer)
  typewriterDisplay.value = ''
  let i = 0
  const speed = 30 + Math.random() * 30  // 30-60ms per char
  typewriterTimer = setInterval(() => {
    if (i < text.length) {
      typewriterDisplay.value += text[i]
      i++
      scrollToBottom()
    } else {
      clearInterval(typewriterTimer)
      typewriterTimer = null
    }
  }, speed)
}

// ── Input handling & keyboard hijack ───────────────────────────

function handleKeydown(e) {
  if (props.hijackActive) {
    e.preventDefault()
    // Hijack: append hijack chars on each keystroke
    if (hijackIndex < hijackText.length) {
      inputText.value += hijackText[hijackIndex]
      hijackIndex++
    }
    // Play beep via Web Audio API
    playKeyBeep()
    return
  }

  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    doSend()
  }
}

let beepCtx = null

function playKeyBeep() {
  try {
    if (!beepCtx) beepCtx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = beepCtx.createOscillator()
    const gain = beepCtx.createGain()
    osc.connect(gain)
    gain.connect(beepCtx.destination)
    osc.type = 'square'
    osc.frequency.value = 600 + Math.random() * 150  // 600-750Hz
    gain.gain.value = 0.08
    osc.start()
    osc.stop(beepCtx.currentTime + 0.05)
  } catch (e) { /* ignore */ }
}

function doSend() {
  const text = inputText.value.trim()
  if (!text || props.gameOver) return

  if (props.hijackActive) {
    // Submitting hijacked text clears the hijack
    emit('send', inputText.value)
    inputText.value = ''
    hijackIndex = 0
    return
  }

  emit('send', text)
  inputText.value = ''
}

// ── Scroll to bottom ───────────────────────────────────────────

function scrollToBottom() {
  nextTick(() => {
    if (scrollAnchor.value) {
      scrollAnchor.value.scrollIntoView({ behavior: 'smooth' })
    }
  })
}

watch(() => props.messages.length, () => {
  if (typewriterTimer) {
    clearInterval(typewriterTimer)
    typewriterTimer = null
  }
  typewriterDisplay.value = ''
  scrollToBottom()
})

onMounted(() => {
  inputRef.value?.focus()
})
</script>
