<template>
  <div 
    v-if="visible" 
    class="fixed inset-0 pointer-events-none z-[150] transition-all duration-300 overflow-hidden flex items-center justify-center"
    :style="overlayStyle"
  >
    <!-- Vignette shadow contraction layer -->
    <div 
      class="absolute inset-0 transition-all duration-[300ms]"
      :style="vignetteStyle"
    ></div>
    
    <!-- Massive scattered text blocks (Mita Yandere Obsession Spawning) -->
    <div
      v-for="item in scatteredTexts"
      :key="'gt-' + item.id"
      class="absolute font-bold select-none mita-chromatic-text"
      :style="item.style"
    >
      {{ item.text }}
    </div>
    
    <!-- Climax pitch-black overlay layer -->
    <div 
      v-if="climaxBlackout" 
      class="absolute inset-0 bg-black transition-opacity duration-300"
      :style="{ opacity: blackoutOpacity }"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  count: { type: Number, default: 60 },
  dialogueText: { type: String, default: '' },
  suspicion: { type: Number, default: 20 },
})

const visible = ref(false)
const scatteredTexts = ref([])
const climaxBlackout = ref(false)
const blackoutOpacity = ref(1)

// Vignette scale closing in
const vignetteRadius = ref(100)
// Backdrop blur value
const backdropBlur = ref(0)
// Backdrop red darkness
const backdropRed = ref(0)

const overlayStyle = computed(() => {
  return {
    backdropFilter: `blur(${backdropBlur.value}px)`,
    background: `radial-gradient(circle, rgba(20,0,0,${backdropRed.value * 0.45}) 0%, rgba(0,0,0,${backdropRed.value * 0.98}) 100%)`
  }
})

const vignetteStyle = computed(() => {
  return {
    background: `radial-gradient(circle, transparent ${vignetteRadius.value}%, rgba(0,0,0,0.99) ${vignetteRadius.value + 10}%)`,
    boxShadow: `inset 0 0 120px rgba(255,0,0,${backdropRed.value * 0.35})`
  }
})

// Mita-style highly aggressive Chinese yandere obsessed phrases
const textBank = [
  '你别想甩掉我', '我爱死你了', '求求你别离开我', '为什么不接电话',
  '他在看谁', '你在干嘛', '我比他们更爱你', '我哪里做错了我可以改',
  '就算死也得待在我身边', '别想逃避我的视线', '看着我❤', '你是我的',
  '不准走', '不许离开我', '不准看别人', '永远待在地下室里吧',
  '开视频给我看立刻', '不要逼我做坏事', '好爱你❤', '好爱你❤'
]

let spawnTimer = null
let synthCtx = null
let oscDrone = null
let oscScrape = null
let droneGain = null
let scrapeGain = null

// Heartbeat variables
let heartbeatTimer = null
let currentBpm = 60

function playSuffocatingSoundscape() {
  try {
    if (!synthCtx) {
      synthCtx = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (synthCtx.state === 'suspended') {
      synthCtx.resume()
    }
    
    const now = synthCtx.currentTime
    
    // 1. Deep rumbling drone oscillator (desperation / heartbeat amplification)
    oscDrone = synthCtx.createOscillator()
    droneGain = synthCtx.createGain()
    oscDrone.type = 'sawtooth'
    oscDrone.frequency.setValueAtTime(30, now)
    oscDrone.frequency.linearRampToValueAtTime(68, now + 4.8)
    
    droneGain.gain.setValueAtTime(0.001, now)
    droneGain.gain.linearRampToValueAtTime(0.45, now + 4.8)
    
    const lp = synthCtx.createBiquadFilter()
    lp.type = 'lowpass'
    lp.frequency.setValueAtTime(90, now)
    lp.frequency.linearRampToValueAtTime(180, now + 4.8)
    
    oscDrone.connect(lp)
    lp.connect(droneGain)
    droneGain.connect(synthCtx.destination)
    
    oscDrone.start(now)
    
    // 2. High metallic scrape oscillator (shiver feedback breakdown)
    oscScrape = synthCtx.createOscillator()
    scrapeGain = synthCtx.createGain()
    oscScrape.type = 'triangle'
    oscScrape.frequency.setValueAtTime(700, now)
    
    const lfo = synthCtx.createOscillator()
    const lfoGain = synthCtx.createGain()
    lfo.type = 'sine'
    lfo.frequency.setValueAtTime(8, now)
    lfoGain.gain.setValueAtTime(200, now)
    
    lfo.connect(lfoGain)
    lfoGain.connect(oscScrape.frequency)
    
    scrapeGain.gain.setValueAtTime(0.001, now)
    scrapeGain.gain.linearRampToValueAtTime(0.12, now + 4.8)
    
    const hp = synthCtx.createBiquadFilter()
    hp.type = 'highpass'
    hp.frequency.setValueAtTime(900, now)
    
    oscScrape.connect(hp)
    hp.connect(scrapeGain)
    scrapeGain.connect(synthCtx.destination)
    
    lfo.start(now)
    oscScrape.start(now)
    
    // 3. Heartbeat synth accelerator
    currentBpm = 60
    triggerAcceleratingHeartbeat()
    
  } catch (e) {
    console.error('Failed to start suffocating soundscape', e)
  }
}

function playSingleHeartThump(time, volume) {
  if (!synthCtx) return
  try {
    const osc = synthCtx.createOscillator()
    const gain = synthCtx.createGain()
    osc.connect(gain)
    gain.connect(synthCtx.destination)
    
    osc.type = 'sine'
    osc.frequency.setValueAtTime(55, time)
    osc.frequency.exponentialRampToValueAtTime(35, time + 0.12)
    
    gain.gain.setValueAtTime(0.001, time)
    gain.gain.linearRampToValueAtTime(volume, time + 0.02)
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.12)
    
    osc.start(time)
    osc.stop(time + 0.14)
  } catch (e) {}
}

function triggerAcceleratingHeartbeat() {
  const tick = () => {
    if (!visible.value || climaxBlackout.value) return
    
    const now = synthCtx.currentTime
    const vol = 0.15 + (currentBpm / 150) * 0.45 // Get louder as BPM rises
    
    // Double pulse heartbeat
    playSingleHeartThump(now, vol)
    playSingleHeartThump(now + 0.22 - (currentBpm / 150) * 0.06, vol * 0.8)
    
    // Accelerate BPM from 60 to 150
    if (currentBpm < 155) {
      currentBpm += 4.5
    }
    
    const intervalMs = (60 / currentBpm) * 1000
    heartbeatTimer = setTimeout(tick, intervalMs)
  }
  tick()
}

function playClimaxScreech() {
  try {
    if (!synthCtx) return
    const now = synthCtx.currentTime
    
    const osc1 = synthCtx.createOscillator()
    const osc2 = synthCtx.createOscillator()
    const gain = synthCtx.createGain()
    
    osc1.type = 'sawtooth'
    osc1.frequency.setValueAtTime(2900, now)
    osc1.frequency.exponentialRampToValueAtTime(40, now + 1.5)
    
    osc2.type = 'square'
    osc2.frequency.setValueAtTime(1400, now)
    osc2.frequency.linearRampToValueAtTime(100, now + 1.5)
    
    gain.gain.setValueAtTime(0.45, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 1.5)
    
    const filter = synthCtx.createBiquadFilter()
    filter.type = 'peaking'
    filter.frequency.setValueAtTime(1800, now)
    filter.Q.value = 18
    
    osc1.connect(filter)
    osc2.connect(filter)
    filter.connect(gain)
    gain.connect(synthCtx.destination)
    
    osc1.start(now)
    osc2.start(now)
    osc1.stop(now + 1.6)
    osc2.stop(now + 1.6)
  } catch (e) {}
}

function stopSoundscape() {
  try {
    if (oscDrone) {
      oscDrone.stop()
      oscDrone = null
    }
    if (oscScrape) {
      oscScrape.stop()
      oscScrape = null
    }
    if (heartbeatTimer) {
      clearTimeout(heartbeatTimer)
      heartbeatTimer = null
    }
  } catch (e) {}
}

let textIdCounter = 0

watch(() => props.active, (isActive) => {
  if (isActive) {
    visible.value = true
    climaxBlackout.value = false
    blackoutOpacity.value = 0
    scatteredTexts.value = []
    
    vignetteRadius.value = 100
    backdropBlur.value = 0
    backdropRed.value = 0
    
    playSuffocatingSoundscape()
    
    let ticks = 0
    const maxTicks = 95 // Spawning count
    
    spawnTimer = setInterval(() => {
      ticks++
      
      // Contract vignette shadows deeply
      if (vignetteRadius.value > 8) {
        vignetteRadius.value -= 1.1
      }
      
      // Backdrop filters squeeze
      if (backdropBlur.value < 14) {
        backdropBlur.value += 0.16
      }
      if (backdropRed.value < 1) {
        backdropRed.value += 0.015
      }
      
      // Spawning text blocks
      const text = textBank[Math.floor(Math.random() * textBank.length)]
      const left = `${Math.floor(Math.random() * 80) + 10}%`
      const top = `${Math.floor(Math.random() * 80) + 10}%`
      
      // Extremely large, bold, highly aggressive Mita-style sizes!
      const size = 26 + Math.floor(Math.random() * 64) // 26px to 90px!
      const rotate = Math.floor(Math.random() * 50) - 25 // -25deg to 25deg
      const sizeScale = 1.0 + (ticks / maxTicks) * 0.9 // Extreme growth
      
      const colors = ['#ff0000', '#ef4444', '#dc2626', '#b91c1c', '#7f1d1d']
      const color = colors[Math.floor(Math.random() * colors.length)]
      const font = Math.random() < 0.5 ? "'SimSun', 'STSong', serif" : 'inherit'
      
      scatteredTexts.value.push({
        id: textIdCounter++,
        text,
        style: {
          left,
          top,
          fontSize: `${size * sizeScale}px`,
          color,
          transform: `rotate(${rotate}deg) translate(-50%, -50%)`,
          textShadow: `0 0 15px ${color}, 0 0 35px rgba(255,0,0,0.95)`,
          opacity: 0.4 + (ticks / maxTicks) * 0.6,
          fontFamily: font,
          fontWeight: '900',
          position: 'absolute',
          letterSpacing: '2px',
          animation: Math.random() < 0.35 ? 'shake-intense 0.2s infinite' : 'pulse-glitch 0.4s infinite'
        }
      })
      
      // Sound sync click crunches during text spawning
      if (ticks % 2 === 0) {
        try {
          if (!synthCtx) synthCtx = new (window.AudioContext || window.webkitAudioContext)()
          const osc = synthCtx.createOscillator()
          const gain = synthCtx.createGain()
          osc.type = 'sawtooth'
          osc.frequency.setValueAtTime(50 + Math.random() * 60, synthCtx.currentTime)
          osc.connect(gain)
          gain.connect(synthCtx.destination)
          gain.gain.setValueAtTime(0.05, synthCtx.currentTime)
          gain.gain.exponentialRampToValueAtTime(0.001, synthCtx.currentTime + 0.1)
          osc.start()
          osc.stop(synthCtx.currentTime + 0.1)
        } catch (e) {}
      }
      
      // Climax phase
      if (ticks >= maxTicks) {
        clearInterval(spawnTimer)
        spawnTimer = null
        stopSoundscape()
        
        // 1. Extreme jump-scare screech
        playClimaxScreech()
        
        // 2. Direct fullscreen visual invert flash
        window.dispatchEvent(new CustomEvent('trigger-glitch-direct', { detail: 'color_invert' }))
        
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('remove-glitch-direct', { detail: 'color_invert' }))
          
          // 3. Blackout overlay fades to pitch black
          climaxBlackout.value = true
          blackoutOpacity.value = 1
          
          setTimeout(() => {
            visible.value = false
            climaxBlackout.value = false
            scatteredTexts.value = []
          }, 1800)
          
        }, 150)
      }
      
    }, 45)
    
  } else {
    if (spawnTimer) clearInterval(spawnTimer)
    spawnTimer = null
    stopSoundscape()
    visible.value = false
    climaxBlackout.value = false
    scatteredTexts.value = []
  }
})

onUnmounted(() => {
  if (spawnTimer) clearInterval(spawnTimer)
  stopSoundscape()
})
</script>

<style scoped>
@keyframes shake-intense {
  0%, 100% { transform: translate(-50%, -50%) translate(0, 0) rotate(0deg); }
  20% { transform: translate(-50%, -50%) translate(-6px, 5px) rotate(-4deg); }
  40% { transform: translate(-50%, -50%) translate(7px, -6px) rotate(5deg); }
  60% { transform: translate(-50%, -50%) translate(-5px, -5px) rotate(-3deg); }
  80% { transform: translate(-50%, -50%) translate(6px, 6px) rotate(4deg); }
}

@keyframes pulse-glitch {
  0%, 100% { filter: hue-rotate(0deg); opacity: 1; }
  50% { filter: hue-rotate(180deg); opacity: 0.65; }
}
</style>
