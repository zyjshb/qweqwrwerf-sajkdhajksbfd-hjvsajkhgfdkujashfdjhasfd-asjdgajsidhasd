<template>
  <div class="absolute bottom-12 left-0 right-0 z-50 mx-4 terminal-panel p-4 border-t-2 border-blood">
    <div class="flex items-center justify-between mb-3">
      <span class="text-blood text-sm font-bold">⚙ API & TTS 配置</span>
      <button @click="$emit('close')" class="text-blood-dim hover:text-blood text-xs">✕ CLOSE</button>
    </div>

    <div class="grid grid-cols-3 gap-3 text-xs">
      <!-- API -->
      <div>
        <label class="text-blood-dim block mb-1">API KEY</label>
        <input
          v-model="form.api_key"
          type="password"
          placeholder="sk-..."
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">API BASE</label>
        <input
          v-model="form.api_base"
          type="text"
          placeholder="https://api.deepseek.com"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">MODEL NAME</label>
        <input
          v-model="form.model_name"
          type="text"
          placeholder="deepseek-v4-flash"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>

      <!-- TTS -->
      <div>
        <label class="text-blood-dim block mb-1">TTS BASE</label>
        <input
          v-model="form.tts_base"
          type="text"
          placeholder="http://127.0.0.1:9880"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">参考音频路径</label>
        <input
          v-model="form.refer_wav_path"
          type="text"
          placeholder="models/hua/huahuo.wav"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">参考文本</label>
        <input
          v-model="form.prompt_text"
          type="text"
          placeholder="参考音频对应的文字..."
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">GPT 权重路径</label>
        <input
          v-model="form.gpt_weights_path"
          type="text"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>
      <div>
        <label class="text-blood-dim block mb-1">SoVITS 权重路径</label>
        <input
          v-model="form.sovits_weights_path"
          type="text"
          class="w-full terminal-input px-2 py-1 text-xs"
        />
      </div>

      <!-- Language -->
      <div>
        <label class="text-blood-dim block mb-1">游戏语言</label>
        <select
          v-model="form.selected_language"
          class="w-full terminal-input px-2 py-1 text-xs bg-terminal-dark"
        >
          <option value="中文">简体中文</option>
          <option value="English">English</option>
          <option value="日本語">日本語</option>
        </select>
      </div>
    </div>

    <div class="flex gap-3 mt-4">
      <button
        @click="doSave"
        class="px-4 py-1 border border-blood text-blood text-xs hover:bg-blood hover:text-black transition-colors"
      >
        保存配置
      </button>
      <button
        @click="doTest"
        class="px-4 py-1 border border-blood-dim text-blood-dim text-xs hover:border-blood hover:text-blood transition-colors"
      >
        API 连接测试
      </button>
    </div>

    <div v-if="testResult" class="mt-2 text-xs" :class="testResult.startsWith('✓') ? 'text-green-600' : 'text-red-600'">
      {{ testResult }}
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

const emit = defineEmits(['close', 'save'])

const form = reactive({
  api_key: '',
  api_base: 'https://api.deepseek.com',
  model_name: 'deepseek-v4-flash',
  tts_base: 'http://127.0.0.1:9880',
  refer_wav_path: '',
  prompt_text: '',
  gpt_weights_path: '',
  sovits_weights_path: '',
  selected_language: '中文',
})

const testResult = ref('')

function doSave() {
  emit('save', { ...form })
  emit('close')
}

async function doTest() {
  testResult.value = 'Testing...'
  try {
    let url = form.api_base.trim()
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      throw new Error('API Base URL 必须以 http:// 或 https:// 开头')
    }
    const resp = await fetch(`${url}/chat/completions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${form.api_key}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: form.model_name,
        messages: [{ role: 'user', content: 'say "hello" in one word' }],
        max_tokens: 10,
      }),
    })
    
    const contentType = resp.headers.get('content-type') || ''
    if (resp.ok && !contentType.includes('text/html')) {
      testResult.value = '✓ API 连接成功'
    } else {
      if (contentType.includes('text/html')) {
        testResult.value = '✗ API 连接失败: 返回了 HTML，请检查 Base URL 格式'
      } else {
        testResult.value = `✗ HTTP ${resp.status}: ${await resp.text()}`
      }
    }
  } catch (e) {
    testResult.value = `✗ 连接失败: ${e.message}`
  }
}
</script>
