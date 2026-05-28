<template>
  <div class="fixed inset-0 z-[90] flex items-center justify-center bg-black/80">
    <div class="terminal-panel w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <span class="text-blood text-base font-bold tracking-wider">⚙ CUSTOM CHARACTER SETTINGS</span>
        <button @click="$emit('close')" class="text-blood-dim hover:text-blood text-sm transition-colors">✕ CLOSE</button>
      </div>

      <div class="w-full h-px bg-blood-dim/20 mb-4"></div>

      <!-- Form fields -->
      <div class="space-y-4 text-sm">
        <!-- Character Name -->
        <div>
          <label class="text-blood-dim block mb-1.5 font-bold">Character Name / 角色名称</label>
          <input
            v-model="form.character_name"
            type="text"
            placeholder="纱希"
            class="w-full terminal-input px-3 py-2.5 text-sm h-10"
          />
        </div>

        <!-- Age -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-blood-dim block mb-1.5 font-bold">Age / 年龄</label>
            <input
              v-model.number="form.age"
              type="number"
              placeholder="17"
              min="1"
              max="999"
              class="w-full terminal-input px-3 py-2.5 text-sm h-10"
            />
          </div>
          <!-- Default Language -->
          <div>
            <label class="text-blood-dim block mb-1.5 font-bold">Default Language / 默认语言</label>
            <select
              v-model="form.default_language"
              class="w-full terminal-input px-3 py-2.5 text-sm bg-terminal-dark h-10"
            >
              <option value="中文">简体中文</option>
              <option value="English">English</option>
              <option value="日本語">日本語</option>
            </select>
          </div>
        </div>

        <!-- Personality -->
        <div>
          <label class="text-blood-dim block mb-1.5 font-bold">Personality / 性格描述</label>
          <textarea
            v-model="form.personality"
            rows="3"
            placeholder="病娇、占有欲极强、对玩家有着扭曲而深刻的依恋..."
            class="w-full terminal-input px-3 py-2.5 text-sm resize-none"
          ></textarea>
        </div>

        <!-- Backstory -->
        <div>
          <label class="text-blood-dim block mb-1.5 font-bold">Backstory / 背景故事</label>
          <textarea
            v-model="form.backstory"
            rows="3"
            placeholder="纱希从小被遗弃在地下实验室..."
            class="w-full terminal-input px-3 py-2.5 text-sm resize-none"
          ></textarea>
        </div>

        <!-- Chat Text Color -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-blood-dim block mb-1.5 font-bold">Text Color / 专属文本颜色</label>
            <div class="flex gap-2">
              <input
                v-model="form.text_color"
                type="color"
                class="w-12 h-10 border border-blood-dim bg-transparent cursor-pointer"
              />
              <input
                v-model="form.text_color"
                type="text"
                placeholder="#CC0000"
                maxlength="7"
                class="flex-1 terminal-input px-3 py-2.5 text-sm h-10"
              />
            </div>
          </div>
          <div>
            <label class="text-blood-dim block mb-1.5 font-bold">TTS Model Path / TTS 模型路径</label>
            <div class="flex gap-2">
              <input
                v-model="form.tts_model_path"
                type="text"
                placeholder="models/saki/saki_e15_s128.pth"
                class="flex-1 terminal-input px-3 py-2.5 text-sm h-10"
              />
              <button
                @click="requestFilePicker('tts_model_path', '选择TTS模型 (.pth)', [['Model File', '*.pth'], ['All Files', '*.*']])"
                type="button"
                class="px-4 h-10 border border-blood text-blood text-xs font-bold hover:bg-blood hover:text-black transition-colors"
              >
                浏览
              </button>
            </div>
          </div>
        </div>

        <!-- GPT Weight Path -->
        <div>
          <label class="text-blood-dim block mb-1.5 font-bold">GPT Weights Path / GPT 权重路径</label>
          <div class="flex gap-2">
            <input
              v-model="form.gpt_weights_path"
              type="text"
              placeholder="models/saki/gpt_weights.ckpt"
              class="flex-1 terminal-input px-3 py-2.5 text-sm h-10"
            />
            <button
              @click="requestFilePicker('gpt_weights_path', '选择GPT权重 (.ckpt)', [['Weights', '*.ckpt'], ['All Files', '*.*']])"
              type="button"
              class="px-4 h-10 border border-blood text-blood text-xs font-bold hover:bg-blood hover:text-black transition-colors"
            >
              浏览
            </button>
          </div>
        </div>

        <!-- SoVITS Weight Path -->
        <div>
          <label class="text-blood-dim block mb-1.5 font-bold">SoVITS Weights Path / SoVITS 权重路径</label>
          <div class="flex gap-2">
            <input
              v-model="form.sovits_weights_path"
              type="text"
              placeholder="models/saki/sovits_weights.pth"
              class="flex-1 terminal-input px-3 py-2.5 text-sm h-10"
            />
            <button
              @click="requestFilePicker('sovits_weights_path', '选择SoVITS权重 (.pth)', [['Weights', '*.pth'], ['All Files', '*.*']])"
              type="button"
              class="px-4 h-10 border border-blood text-blood text-xs font-bold hover:bg-blood hover:text-black transition-colors"
            >
              浏览
            </button>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-4 mt-6 pt-4 border-t border-blood-dim/20">
        <button
          @click="doSave"
          class="px-6 py-2.5 border border-blood text-blood text-sm font-bold hover:bg-blood hover:text-black transition-colors"
        >
          SAVE CURRENT CONFIGURATION
        </button>
        <button
          @click="$emit('close')"
          class="px-6 py-2.5 border border-blood-dim text-blood-dim text-sm hover:border-blood hover:text-blood transition-colors"
        >
          CANCEL
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['close', 'save'])

const form = reactive({
  character_name: '纱希',
  age: 17,
  default_language: '中文',
  personality: '',
  backstory: '',
  text_color: '#CC0000',
  tts_model_path: '',
  gpt_weights_path: '',
  sovits_weights_path: '',
})

const handleFilePickerSelected = (e) => {
  const { field, path } = e.detail
  if (field in form) {
    form[field] = path
  }
}

onMounted(() => {
  window.addEventListener('file-picker-selected', handleFilePickerSelected)
})

onUnmounted(() => {
  window.removeEventListener('file-picker-selected', handleFilePickerSelected)
})

function requestFilePicker(field, title, filetypes) {
  window.dispatchEvent(new CustomEvent('request-file-picker', {
    detail: { field, title, filetypes }
  }))
}

function doSave() {
  emit('save', { ...form })
  emit('close')
}
</script>
