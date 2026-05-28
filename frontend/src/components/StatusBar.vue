<template>
  <div class="px-4 py-1 flex items-center gap-4 text-xs">
    <!-- Day -->
    <div class="flex items-center gap-1">
      <span class="text-blood-dim">DAY</span>
      <span class="text-blood font-bold">{{ day }}</span>
    </div>

    <div class="w-px h-4 bg-blood-dim"></div>

    <!-- Favorability -->
    <div class="flex items-center gap-1 flex-1 max-w-[200px]">
      <span class="text-blood-dim w-6">♥</span>
      <div class="flex-1 h-3 bg-terminal-dark border border-blood-dim relative overflow-hidden">
        <div
          class="h-full transition-all duration-500 ease-out"
          :class="favorColorClass"
          :style="{ width: favorability + '%' }"
        ></div>
      </div>
      <span class="text-blood-dim w-8 text-right">{{ favorability }}</span>
    </div>

    <!-- Suspicion -->
    <div class="flex items-center gap-1 flex-1 max-w-[200px]">
      <span class="text-blood-dim w-6">⚠</span>
      <div class="flex-1 h-3 bg-terminal-dark border border-blood-dim relative overflow-hidden">
        <div
          class="h-full transition-all duration-500 ease-out"
          :class="suspicionColorClass"
          :style="{ width: suspicion + '%' }"
        ></div>
      </div>
      <span class="text-blood-dim w-8 text-right">{{ suspicion }}</span>
    </div>

    <!-- Escape rate -->
    <div class="flex items-center gap-1 flex-1 max-w-[200px]">
      <span class="text-blood-dim w-6">⇱</span>
      <div class="flex-1 h-3 bg-terminal-dark border border-blood-dim relative overflow-hidden">
        <div
          class="h-full transition-all duration-500 ease-out"
          :class="escapeColorClass"
          :style="{ width: escapeRate + '%' }"
        ></div>
      </div>
      <span class="text-blood-dim w-8 text-right">{{ escapeRate }}%</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  favorability: { type: Number, default: 50 },
  suspicion: { type: Number, default: 20 },
  escapeRate: { type: Number, default: 0 },
  day: { type: Number, default: 1 },
  language: { type: String, default: '中文' },
})

const favorColorClass = computed(() => {
  const f = props.favorability
  if (f <= 10) return 'bg-red-900'
  if (f <= 30) return 'bg-red-700'
  if (f <= 60) return 'bg-yellow-700'
  return 'bg-green-700'
})

const suspicionColorClass = computed(() => {
  const s = props.suspicion
  if (s >= 85) return 'bg-red-600 animate-pulse'
  if (s >= 75) return 'bg-red-500'
  if (s >= 55) return 'bg-orange-600'
  if (s >= 35) return 'bg-yellow-600'
  return 'bg-green-700'
})

const escapeColorClass = computed(() => {
  const e = props.escapeRate
  if (e >= 75) return 'bg-red-600 animate-pulse'
  if (e >= 50) return 'bg-orange-600'
  if (e >= 25) return 'bg-yellow-600'
  return 'bg-green-700'
})
</script>
