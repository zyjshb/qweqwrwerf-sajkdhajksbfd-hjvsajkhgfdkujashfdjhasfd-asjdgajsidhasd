<template>
  <div class="absolute bottom-12 left-0 right-0 z-50 mx-4 terminal-panel p-4 border-t-2 border-blood">
    <div class="flex items-center justify-between mb-3">
      <span class="text-blood text-sm font-bold">💾 存档管理</span>
      <button @click="$emit('close')" class="text-blood-dim hover:text-blood text-xs">✕ CLOSE</button>
    </div>

    <div class="grid grid-cols-5 gap-2">
      <div
        v-for="slot in slots"
        :key="'slot-' + slot.slot"
        class="border border-blood-dim p-2 text-center"
        :class="{ 'border-blood': slot.empty, 'border-yellow-700': !slot.empty }"
      >
        <div class="text-xs text-blood-dim mb-1">SLOT {{ slot.slot }}</div>
        <template v-if="slot.empty">
          <div class="text-xs text-blood-dim">[ 空 ]</div>
          <button
            @click="$emit('save', slot.slot)"
            class="mt-2 px-3 py-1 border border-blood text-blood text-xs hover:bg-blood hover:text-black transition-colors w-full"
          >
            保存
          </button>
        </template>
        <template v-else>
          <div class="text-xs text-yellow-700">DAY {{ slot.day }}</div>
          <div class="text-xs text-yellow-700/60">{{ slot.language }} · {{ slot.char_id }}</div>
          <div class="flex gap-1 mt-2">
            <button
              @click="$emit('load', slot.slot)"
              class="flex-1 px-2 py-1 border border-yellow-700 text-yellow-700 text-xs hover:bg-yellow-700 hover:text-black transition-colors"
            >
              读取
            </button>
            <button
              @click="confirmDelete(slot.slot)"
              class="flex-1 px-2 py-1 border border-red-900 text-red-700 text-xs hover:bg-red-900 hover:text-black transition-colors"
            >
              删除
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div
      v-if="deleteTarget"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80"
    >
      <div class="terminal-panel p-6 text-center">
        <div class="text-blood mb-4">确认删除 Slot {{ deleteTarget }}？</div>
        <div class="text-xs text-blood-dim mb-4">此操作不可撤销</div>
        <div class="flex gap-3 justify-center">
          <button
            @click="doDelete"
            class="px-4 py-1 border border-blood text-blood hover:bg-blood hover:text-black transition-colors"
          >
            确认删除
          </button>
          <button
            @click="deleteTarget = null"
            class="px-4 py-1 border border-blood-dim text-blood-dim hover:border-blood transition-colors"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  slots: { type: Array, default: () => [] },
})

const emit = defineEmits(['close', 'save', 'load', 'delete'])
const deleteTarget = ref(null)

function confirmDelete(slot) {
  deleteTarget.value = slot
}

function doDelete() {
  if (deleteTarget.value) {
    emit('delete', deleteTarget.value)
    deleteTarget.value = null
  }
}
</script>
