<template>
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 select-none font-mono">
    <!-- Classic Windows 95 3D Raised Dialog Box -->
    <div
      class="w-[550px] bg-[#D4D0C8] p-[4px] border-2 border-white shadow-[2px_2px_0px_#000,-2px_-2px_0px_#fff,1px_1px_0px_#808080,-1px_-1px_0px_#c0c0c0]"
    >
      <!-- Title Bar -->
      <div class="bg-[#000080] text-white px-2 py-1 flex items-center justify-between font-bold text-sm h-7 select-none">
        <span class="tracking-wide">神经接口断开与存档管理</span>
        <!-- Close button (x) -->
        <button
          @click="$emit('close')"
          class="w-5 h-5 bg-[#D4D0C8] text-black border border-white shadow-[1px_1px_0px_#000] flex items-center justify-center font-bold text-xs outline-none hover:bg-[#c0c0c0] cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Main Body Container -->
      <div class="p-5 space-y-4 text-sm text-black">
        <!-- Explanatory note -->
        <div
          v-if="suspicion >= 75"
          class="text-xs font-bold text-red-500 leading-relaxed border border-inset p-3 bg-black border-red-900 animate-pulse"
        >
          ⚠️ 警告：检测到违规的意识剥离尝试。所有的记忆通路已断开。你无法逃避，你无法隐藏，看着我。
        </div>
        <div
          v-else
          class="text-xs font-bold text-zinc-800 leading-relaxed border border-inset p-3 bg-[#fff] border-b-white border-r-white border-t-zinc-700 border-l-zinc-700"
        >
          ⚠️ 警告：检测到突触物理连接断开请求。选择下方脑波记忆区（BANK 1-5）进行意识上传，或强制断开连接。
        </div>

        <!-- Vertical memory slot bank selector -->
        <div v-if="suspicion >= 75" class="p-8 border border-red-900 bg-black text-center text-red-500 font-bold tracking-widest text-base select-none animate-pulse">
          [ 错误：意识出口已被纱希永久锁定 ]
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="slot in manualSlots"
            :key="slot.slot"
            @click="selectedSlot = slot.slot"
            class="p-2.5 border cursor-pointer select-none transition-all flex items-center justify-between"
            :class="[
              slot.empty
                ? 'border-zinc-400 bg-zinc-100 text-zinc-500'
                : 'border-red-900 bg-red-950/10 text-red-700 font-bold',
              selectedSlot === slot.slot
                ? 'bg-blue-900 text-white border-blue-900 shadow-inner'
                : ''
            ]"
          >
            <div class="text-[13px] truncate flex-1 font-mono">
              <span v-if="slot.empty">BANK {{ slot.slot }} : [ EMPTY SLOT ] 空白记忆区间</span>
              <span v-else :class="selectedSlot === slot.slot ? 'text-white' : 'text-red-700'">
                BANK {{ slot.slot }} : DAY {{ slot.day }} | 好感 {{ slot.favor }}% 疑心 {{ slot.sus }}% | 神经宿主: {{ slot.charName }}
              </span>
            </div>
            <!-- Indicator dot -->
            <div
              class="w-3 h-3 rounded-full border border-zinc-400"
              :class="selectedSlot === slot.slot ? 'bg-blue-400 border-white' : 'bg-transparent'"
            ></div>
          </div>
        </div>

        <!-- Selected indicator report -->
        <div class="text-xs text-zinc-600 font-bold select-none h-5">
          {{ suspicion >= 75 ? '目标磁道: 🔒 心之深渊' : '已选中目标磁道: BANK ' + selectedSlot }}
        </div>

        <!-- Action Triggers -->
        <div class="flex flex-col gap-2.5 pt-3 border-t border-zinc-400">
          <div v-if="suspicion < 75" class="flex gap-2">
            <!-- [保存并返回主菜单] (green) -->
            <button
              @click="doSaveAndExit"
              class="flex-1 py-2.5 bg-green-700 hover:bg-green-600 active:bg-green-800 text-white font-bold border-2 border-white shadow-[1px_1px_0px_#000] text-xs cursor-pointer"
            >
              保存并返回主菜单
            </button>
            <!-- [直接退出（不保存）] (red) -->
            <button
              @click="doExitNoSave"
              class="flex-1 py-2.5 bg-red-700 hover:bg-red-600 active:bg-red-800 text-white font-bold border-2 border-white shadow-[1px_1px_0px_#000] text-xs cursor-pointer"
            >
              直接退出（不保存）
            </button>
          </div>
          
          <!-- [返回] (grey) -->
          <button
            @click="$emit('close')"
            class="w-full py-2 font-bold border-2 border-white shadow-[1px_1px_0px_#000] cursor-pointer"
            :class="suspicion >= 75
              ? 'bg-red-700 hover:bg-red-600 active:bg-red-800 text-white text-sm py-3 animate-pulse-red'
              : 'bg-[#D4D0C8] hover:bg-[#c0c0c0] active:bg-[#e0e0e0] text-black text-xs'"
          >
            {{ suspicion >= 75 ? '留下来，陪着我❤' : '返回意识接口（Cancel）' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  slots: { type: Array, default: () => [] },
  suspicion: { type: Number, default: 20 },
})

const emit = defineEmits([
  'close',
  'saveAndExit',
  'exitWithoutSaving',
])

const selectedSlot = ref(1)

// ── Manual slots rendering ──
const manualSlots = computed(() => {
  const result = []
  for (let i = 1; i <= 5; i++) {
    const found = props.slots.find(s => s.slot === i && !s.empty)
    if (found) {
      result.push({
        slot: i,
        empty: false,
        day: found.day,
        charName: found.char_id === 'saki' ? '纱希' : found.char_id,
        favor: found.favorability !== undefined ? found.favorability : 50,
        sus: found.suspicion !== undefined ? found.suspicion : 20,
      })
    } else {
      result.push({ slot: i, empty: true })
    }
  }
  return result
})

function doSaveAndExit() {
  emit('saveAndExit', selectedSlot.value)
}

function doExitNoSave() {
  emit('exitWithoutSaving')
}
</script>

<style scoped>
.border-inset {
  border-width: 1px;
  border-style: solid;
}
</style>
