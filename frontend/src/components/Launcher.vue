<template>
  <div class="w-full h-full flex flex-col bg-black overflow-hidden relative select-none font-mono text-blood">
    <!-- Background grid noise line layer -->
    <div class="absolute inset-0 pointer-events-none z-0">
      <div
        class="absolute inset-0"
        style="background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(200,0,0,0.06) 2px, rgba(0,0,0,0.03) 4px);"
      ></div>
    </div>

    <!-- Main launcher content -->
    <div class="flex-1 flex flex-col items-center justify-center px-6 py-4 relative z-10">
      <!-- Title Frame -->
      <div class="mb-4 text-center">
        <!-- Retro dot-matrix glowing style -->
        <h1 class="text-3xl font-bold mb-1 tracking-widest dot-matrix-title">
          {{ t.title }}
        </h1>
        <!-- Fluorescent green status bar -->
        <div class="text-[11px] text-green-500 font-bold tracking-wider animate-pulse mt-2">
          {{ t.status }}
        </div>
        <div class="w-64 h-px bg-red-950 mx-auto mt-3"></div>
      </div>

      <!-- Main core panel card -->
      <div class="terminal-panel w-full max-w-2xl p-6 space-y-5 border border-red-950/80 bg-black rounded">
        <!-- ── Layer 2.1: Synapse Connection Settings ── -->
        <div>
          <div class="flex items-center gap-2 mb-3">
            <span class="text-red-500 text-xs font-bold tracking-wider">{{ t.synapse_settings }}</span>
            <div class="flex-1 h-px bg-red-950/30"></div>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-xs">
            <!-- API Key -->
            <div class="col-span-3">
              <label class="text-red-900/60 block mb-1.5 font-bold">{{ t.api_key }}</label>
              <div class="flex gap-2">
                <input
                  :type="showApiKey ? 'text' : 'password'"
                  v-model="form.api_key"
                  placeholder="sk-..."
                  class="flex-1 terminal-input px-3 py-1.5 text-[13px] h-9"
                />
                <button
                  @click="showApiKey = !showApiKey"
                  class="px-4 h-9 border border-red-900 bg-black text-red-500 hover:border-red-500 hover:text-red-400 text-xs font-bold cursor-pointer"
                >
                  {{ showApiKey ? 'HIDE' : 'SHOW' }}
                </button>
              </div>
            </div>
            
            <!-- API Base -->
            <div>
              <label class="text-red-900/60 block mb-1.5 font-bold">{{ t.api_base }}</label>
              <input
                v-model="form.api_base"
                type="text"
                placeholder="https://api.deepseek.com"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
            
            <!-- Model Name -->
            <div>
              <label class="text-red-900/60 block mb-1.5 font-bold">{{ t.model_name }}</label>
              <input
                v-model="form.model_name"
                type="text"
                placeholder="deepseek-v4-flash"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>

            <!-- Test Connection Button & State -->
            <div class="flex items-end gap-2">
              <button
                @click="doTestConnection"
                :disabled="testing"
                class="w-full h-9 border border-red-900 bg-black text-red-500 hover:border-red-500 hover:text-red-400 text-xs font-bold cursor-pointer select-none disabled:opacity-30"
              >
                {{ t.test_conn }}
              </button>
            </div>
          </div>

          <!-- Connection state reporter -->
          <div class="text-xs mt-2.5 select-none h-5">
            <span v-if="testing" class="text-red-900/60 animate-pulse">{{ t.status_testing }}</span>
            <span
              v-else
              :class="testResultStateClass"
            >
              {{ testResultText }}
            </span>
          </div>
        </div>

        <div class="w-full h-px bg-red-950/20"></div>

        <!-- ── Layer 2.2: Language Selection ── -->
        <div>
          <span class="text-red-500 text-xs font-bold tracking-wider block mb-2.5">{{ t.lang_system }}</span>
          <div class="flex gap-2">
            <button
              v-for="lang in languages"
              :key="lang.value"
              @click="selectLanguage(lang.value)"
              class="px-5 py-2 border text-[13px] transition-all bg-transparent select-none cursor-pointer"
              :class="form.selected_language === lang.value
                ? 'border-red-500 text-red-500 bg-red-950/20 shadow-[0_0_10px_rgba(239,68,68,0.25)] font-bold'
                : 'border-red-800 text-red-400 bg-black hover:border-red-500 hover:text-red-300 hover:shadow-[0_0_8px_rgba(239,68,68,0.2)]'"
            >
              {{ lang.label }}
            </button>
          </div>
        </div>

        <div class="w-full h-px bg-red-950/20"></div>

        <!-- ── Layer 2.3: Memory Slot Management (5 Manual Banks) ── -->
        <div>
          <div class="flex items-center justify-between mb-2.5">
            <span class="text-red-500 text-xs font-bold tracking-wider">{{ t.memory_slots }}</span>
            <span class="text-red-900/40 text-[11px] select-none">{{ t.memory_slots_sub }}</span>
          </div>
          
          <!-- Vertical Slots List -->
          <div class="space-y-2 max-h-[220px] overflow-y-auto hacker-scroll pr-1 select-none">
            <div
              v-for="slot in manualSlots"
              :key="slot.slot"
              class="border px-3 py-2 flex items-center justify-between h-14 transition-colors"
              :class="slot.empty
                ? 'border-red-950/30 bg-black/10'
                : 'border-red-950/80 bg-black/40'"
            >
              <!-- Vacant State -->
              <div v-if="slot.empty" class="text-xs text-zinc-600 flex-1 italic">
                {{ getSlotVacantText(slot.slot) }}
              </div>
              
              <!-- Occupied State (Fluorescent Green) -->
              <div v-else class="text-xs text-green-500 font-bold flex-1">
                BANK {{ slot.slot }} : [ ACTIVE ] 第 {{ slot.day }} 天 | 好感: {{ slot.favorability }}% 疑心: {{ slot.suspicion }}% | 神经宿主: {{ slot.charName }}
              </div>

              <!-- Slot Actions -->
              <div class="flex gap-2.5">
                <button
                  v-if="!slot.empty"
                  @click="deleteSlot(slot.slot)"
                  class="px-3 py-1 border border-red-800 text-red-800 hover:border-red-500 hover:text-red-500 text-xs cursor-pointer"
                >
                  {{ t.delete }}
                </button>
                <button
                  v-if="!slot.empty"
                  @click="loadSlot(slot.slot)"
                  class="px-3 py-1 border border-green-800 text-green-700 hover:border-green-500 hover:text-green-500 text-xs font-bold cursor-pointer"
                >
                  {{ t.load }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="w-full h-px bg-red-950/20"></div>

        <!-- ── Layer 2.4: Actions ── -->
        <div class="flex items-center gap-4">
          <button
            @click="showCharacterSettings = true"
            class="px-5 py-2.5 border border-red-900 text-red-600 text-xs font-bold bg-transparent select-none cursor-pointer rounded mita-interactive-ui"
          >
            {{ t.char_settings }}
          </button>
          <div class="flex-1"></div>
          <button
            @click="enterGame"
            class="px-8 py-3.5 border border-red-950 text-red-500 text-sm font-bold tracking-widest cursor-pointer select-none transition-all rounded shadow-[0_0_15px_rgba(200,0,0,0.15)] mita-interactive-ui bg-black"
          >
            {{ t.enter_game }}
          </button>
        </div>
      </div>

      <!-- Footer -->
      <div class="mt-4 text-[9px] text-red-950/40 tracking-wider select-none">
        SAKI PROJECT · TERMINAL A.I. · ALL RIGHTS RESERVED
      </div>
    </div>

    <!-- Character Settings Modal -->
    <CharacterSettings
      v-if="showCharacterSettings"
      @close="showCharacterSettings = false"
      @save="handleCharSave"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import CharacterSettings from './CharacterSettings.vue'

const emit = defineEmits([
  'enterGame',
  'updateConfig',
  'loadSlot',
  'deleteSlot',
])

const props = defineProps({
  slots: { type: Array, default: () => [] },
  savedConfig: { type: Object, default: () => ({}) },
})

const showApiKey = ref(false)
const showCharacterSettings = ref(false)
const testing = ref(false)
const testResult = ref('untested') // 'untested' | 'success' | 'failed'
const testMessage = ref('')
const transitioning = ref(false)

// ── Multi-language UI dictionaries ──
const LOCALIZATION = {
  '中文': {
    title: '纱希 (Saki) - Terminal A.I.',
    status: '● SYSTEM OVERLORD STATUS: ONLINE | NEURAL COUPLING STABLE',
    synapse_settings: '⚡ SYNAPSE CONNECTION SETTINGS',
    api_key: 'API KEY / 密钥',
    api_base: 'API BASE URL / 端点',
    model_name: 'MODEL NAME / 模型',
    test_conn: '测试 API 联通性 / Test Connection',
    status_ready: '[ 状态: 未测试 / Ready ]',
    status_testing: '[ 状态: 测试中 / Testing ]',
    status_success: '[ 状态: 联通激活 / Active ]',
    status_failed: '[ 状态: 联通失败 / Failed ]',
    lang_system: '🌐 LANGUAGE SYSTEM / 语言系统',
    memory_slots: '💾 MEMORY SLOT MANAGEMENT / 记忆存取',
    memory_slots_sub: '5 MANUAL SLOTS + 1 AUTO SAVE',
    char_settings: '⚙ CUSTOM CHARACTER SETTINGS / 自定义角色',
    enter_game: 'ENTER GAME / 进入脑干接口',
    vacant: 'BANK {slot} : [ VACANT SLOT ] - 空白记忆区间 - (Empty Memory Slot)',
    active: 'BANK {slot} : [ ACTIVE ] 第 {day} 天 | 好感: {favor}% 疑心: {sus}% | 神经宿主: {char}',
    delete: '删除',
    load: '载入突触'
  },
  'English': {
    title: 'Saki (Saki) - Terminal A.I.',
    status: '● SYSTEM OVERLORD STATUS: ONLINE | NEURAL COUPLING STABLE',
    synapse_settings: '⚡ SYNAPSE CONNECTION SETTINGS',
    api_key: 'API KEY',
    api_base: 'API BASE URL',
    model_name: 'MODEL NAME',
    test_conn: 'Test Connection',
    status_ready: '[ Status: Ready ]',
    status_testing: '[ Status: Testing... ]',
    status_success: '[ Status: Connection Stable ]',
    status_failed: '[ Status: Connection Failed ]',
    lang_system: '🌐 LANGUAGE SYSTEM',
    memory_slots: '💾 MEMORY SLOT MANAGEMENT',
    memory_slots_sub: '5 MANUAL SLOTS + 1 AUTO SAVE',
    char_settings: '⚙ CUSTOM CHARACTER SETTINGS',
    enter_game: 'ENTER GAME',
    vacant: 'BANK {slot} : [ VACANT SLOT ] - Empty Memory Slot',
    active: 'BANK {slot} : [ ACTIVE ] DAY {day} | Favor: {favor}% Sus: {sus}% | Host: {char}',
    delete: 'DELETE',
    load: 'LOAD SYNAPSE'
  },
  '日本語': {
    title: '紗希 (Saki) - ターミナル A.I.',
    status: '● SYSTEM OVERLORD STATUS: ONLINE | NEURAL COUPLING STABLE',
    synapse_settings: '⚡ シナプス接続設定',
    api_key: 'API キー',
    api_base: 'API ベース URL',
    model_name: 'モデル名',
    test_conn: 'API 接続テスト',
    status_ready: '[ 状態: 未テスト / Ready ]',
    status_testing: '[ 状態: テスト中... ]',
    status_success: '[ 状態: 接続成功 ]',
    status_failed: '[ 状態: 接続失敗 ]',
    lang_system: '🌐 言語システム',
    memory_slots: '💾 記憶体スロット管理',
    memory_slots_sub: '5 手動スロット + 1 自動',
    char_settings: '⚙ カスタムキャラクター設定',
    enter_game: '脳幹インターフェースに入る',
    vacant: 'BANK {slot} : [ VACANT SLOT ] - 空白記憶領域',
    active: 'BANK {slot} : [ ACTIVE ] 第 {day} 日 | 好感: {favor}% 疑心: {sus}% | ホスト: {char}',
    delete: '削除',
    load: 'シナプスロード'
  }
}

const t = computed(() => LOCALIZATION[form.selected_language] || LOCALIZATION['中文'])

const languages = [
  { label: '简体中文', value: '中文' },
  { label: 'English', value: 'English' },
  { label: '日本語', value: '日本語' },
]

const form = reactive({
  api_key: '',
  api_base: 'https://api.deepseek.com',
  model_name: 'deepseek-v4-flash',
  selected_language: '中文',
})

// Hydrate from saved config
watch(() => props.savedConfig, (conf) => {
  if (conf && Object.keys(conf).length > 0) {
    if (conf.api_key !== undefined) form.api_key = conf.api_key
    if (conf.api_base !== undefined) form.api_base = conf.api_base
    if (conf.model_name !== undefined) form.model_name = conf.model_name
    if (conf.selected_language !== undefined) form.selected_language = conf.selected_language
  }
}, { immediate: true, deep: true })

// ── Connection Test State Computeds ──
const testResultText = computed(() => {
  if (testResult.value === 'untested') return t.value.status_ready
  if (testResult.value === 'success') return t.value.status_success
  return `${t.value.status_failed} ${testMessage.value}`
})

const testResultStateClass = computed(() => {
  if (testResult.value === 'untested') return 'text-red-900/60'
  if (testResult.value === 'success') return 'text-green-500 font-bold'
  return 'text-red-500 font-bold'
})

// ── Language Mapping ──
function selectLanguage(lang) {
  form.selected_language = lang
  // Map exact strings to backend normalized aliases (which we've updated to support codes)
  let code = 'zh'
  if (lang === 'English') code = 'en'
  if (lang === '日本語') code = 'ja'
  
  emit('updateConfig', {
    selected_language: lang,
    language_code: code,
  })
}

// ── Slots Rendering ──
const manualSlots = computed(() => {
  const result = []
  for (let i = 1; i <= 5; i++) {
    const found = props.slots.find(s => s.slot === i && !s.empty)
    if (found) {
      result.push({
        slot: i,
        empty: false,
        day: found.day,
        charName: found.char_id === 'saki' ? '纱希 (Saki)' : found.char_id,
        favorability: found.favorability !== undefined ? found.favorability : 50,
        suspicion: found.suspicion !== undefined ? found.suspicion : 20,
      })
    } else {
      result.push({ slot: i, empty: true })
    }
  }
  return result
})

function getSlotVacantText(slotNum) {
  return t.value.vacant.replace('{slot}', slotNum)
}

// ── Actions ──
async function doTestConnection() {
  testing.value = true
  testResult.value = 'untested'
  testMessage.value = ''
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
      testResult.value = 'success'
    } else {
      const txt = await resp.text().catch(() => '')
      testResult.value = 'failed'
      if (contentType.includes('text/html')) {
        testMessage.value = '(API 返回了 HTML，请检查 Base URL 格式)'
      } else {
        testMessage.value = `(HTTP ${resp.status}: ${txt.slice(0, 40)})`
      }
    }
  } catch (e) {
    testResult.value = 'failed'
    testMessage.value = `(${e.message.slice(0, 40)})`
  } finally {
    testing.value = false
  }
}

function loadSlot(slot) {
  emit('loadSlot', slot)
}

function deleteSlot(slot) {
  emit('deleteSlot', slot)
}

function handleCharSave(data) {
  emit('updateConfig', { character_settings: data })
}

function enterGame() {
  transitioning.value = true
  let code = 'zh'
  if (form.selected_language === 'English') code = 'en'
  if (form.selected_language === '日本語') code = 'ja'

  emit('updateConfig', {
    api_key: form.api_key,
    api_base: form.api_base,
    model_name: form.model_name,
    selected_language: form.selected_language,
    language_code: code,
  })
  
  setTimeout(() => {
    transitioning.value = false
    emit('enterGame')
  }, 250)
}
</script>

<style scoped>
.dot-matrix-title {
  color: #ef4444;
  text-shadow: 
    0 0 4px rgba(239, 68, 68, 0.4), 
    0 0 12px rgba(239, 68, 68, 0.2);
}

.character-sprite-container {
  animation: breath-scale 4s ease-in-out infinite;
}

@keyframes breath-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.025); }
}

.animate-breath {
  animation: breath-scale 3s ease-in-out infinite;
}
</style>
