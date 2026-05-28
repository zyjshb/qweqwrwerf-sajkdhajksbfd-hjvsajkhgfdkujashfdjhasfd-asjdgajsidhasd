<template>
  <div
    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70"
    @click.self="dismiss"
  >
    <!-- Window frame (classic Windows-classic 95/98 theme) -->
    <div
      class="border-2 border-[#808080] shadow-[2px_2px_0px_#000]"
      style="background: #c0c0c0; font-family: 'Microsoft Sans Serif', 'SimSun', sans-serif; min-width: 420px; box-shadow: 2px 2px 10px rgba(0,0,0,0.5);"
    >
      <!-- Title bar -->
      <div class="flex items-center justify-between px-2 py-0.5 select-none" style="background: #000080; height: 22px;">
        <span class="text-white text-xs font-bold font-sans">{{ t.title }}</span>
        <button
          @click="dismiss"
          class="w-4 h-4 flex items-center justify-center text-xs font-bold border hover:bg-gray-100 transition-colors"
          style="background: #c0c0c0; border-color: #fff #808080 #808080 #fff; color: #000; line-height: 1; outline: none;"
        >
          ✕
        </button>
      </div>

      <!-- Body -->
      <div class="flex items-start gap-4 p-5 select-none" style="background: #c0c0c0;">
        <!-- Classic Red X error icon -->
        <div class="shrink-0 w-8 h-8 flex items-center justify-center rounded-full border-2 border-red-800" style="background: #ff0000; box-shadow: 1px 1px 3px rgba(0,0,0,0.4);">
          <span class="text-white text-lg font-bold font-sans leading-none" style="margin-top: -2px;">✕</span>
        </div>

        <!-- Error text -->
        <div class="flex-1 text-black font-sans">
          <p class="text-[13px] font-bold mb-2.5 leading-snug">
            {{ t.subtitle }}
          </p>
          <p class="text-xs font-bold text-red-700 whitespace-pre-wrap leading-relaxed mb-3">
            {{ t.msg }}
          </p>
          <p class="text-[11px] text-gray-700 whitespace-pre-wrap leading-normal font-mono border-t border-gray-400/30 pt-2.5">
            {{ t.desc }}
          </p>
        </div>
      </div>

      <!-- Button bar -->
      <div class="flex justify-center gap-2 px-4 pb-4 select-none" style="background: #c0c0c0;">
        <button
          @click="dismiss"
          class="px-7 py-1 text-xs font-bold border-2 active:border-inset focus:outline-none hover:bg-gray-100 transition-all"
          style="background: #c0c0c0; border-color: #fff #808080 #808080 #fff; color: #000; min-width: 75px; box-shadow: inset 1px 1px 0px #fff;"
        >
          {{ t.btn }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'

const props = defineProps({
  language: { type: String, default: '中文' },
})

const emit = defineEmits(['close'])

const LOCALIZED_WARNINGS = {
  '中文': {
    title: 'Fatal Error',
    subtitle: '无法从系统内存中抹除 纱希 (Saki)',
    msg: 'Fatal Error: 玩家尝试逃跑。\n精神控制已激活。',
    desc: 'A fatal exception 0xE7A6B3 has occurred at address 0x7FFA3C1D9B00.\nThe current execution stack will be overwritten.',
    btn: '确定',
  },
  'English': {
    title: 'Fatal Error',
    subtitle: 'Cannot erase Saki from system memory.',
    msg: 'Fatal Error: User tried to escape.\nMind control active.',
    desc: 'A fatal exception 0xE7A6B3 has occurred at address 0x7FFA3C1D9B00.\nThe current execution stack will be overwritten.',
    btn: 'OK',
  },
  '日本語': {
    title: 'Fatal Error',
    subtitle: 'システムメモリから紗希を抹消できません。',
    msg: 'Fatal Error: ユーザーが脱走を試みました。\n精神支配を起動中。',
    desc: 'A fatal exception 0xE7A6B3 has occurred at address 0x7FFA3C1D9B00.\nThe current execution stack will be overwritten.',
    btn: '了解',
  }
}

const t = computed(() => LOCALIZED_WARNINGS[props.language] || LOCALIZED_WARNINGS['中文'])

let beepCtx = null

function playSystemBeep() {
  try {
    if (!beepCtx) beepCtx = new (window.AudioContext || window.webkitAudioContext)()
    const now = beepCtx.currentTime
    // Vintage dual-tone warning chime (harsh Windows error sound simulation)
    ;[150, 220].forEach((freq, idx) => {
      const osc = beepCtx.createOscillator()
      const gain = beepCtx.createGain()
      osc.connect(gain)
      gain.connect(beepCtx.destination)
      osc.type = 'square'
      osc.frequency.setValueAtTime(freq, now + idx * 0.04)
      gain.gain.setValueAtTime(0.12, now + idx * 0.04)
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.04 + 0.35)
      osc.start(now + idx * 0.04)
      osc.stop(now + idx * 0.04 + 0.35)
    })
  } catch (e) { /* ignore */ }
}

function dismiss() {
  emit('close')
}

onMounted(() => {
  playSystemBeep()
})
</script>
