<template>
  <div class="flex-1 flex items-center justify-center p-4 bg-black/40">
    <!-- Main Rigid Window Frame (1100x800px) -->
    <div
      class="relative w-[1100px] h-[800px] bg-black border border-red-950/80 flex flex-col overflow-hidden select-none font-mono text-blood shadow-[0_0_50px_rgba(138,3,3,0.25)] rounded transition-all duration-700"
      :class="{ 'mita-screen-tilt': props.suspicion >= 55 }"
    >
      <!-- Saki Avatar / Sprite on Left Side (Only when sprite image is loaded) -->
      <div v-if="characterSprite" class="absolute left-0 top-8 bottom-12 w-[35%] pointer-events-none z-10 flex items-end justify-center">
        <div class="character-sprite-container">
          <img
            :src="characterSprite"
            alt="Saki"
            class="max-h-[60vh] object-contain opacity-85"
          />
        </div>
      </div>

      <!-- ── Layer 1: Title Bar ── -->
      <div class="h-8 border-b border-red-950 flex items-center justify-between px-4 bg-[#050000] shrink-0 z-20">
        <div class="text-[12px] text-blood-dim flex items-center gap-2 select-none">
          <span>{{ t.title }}</span>
          <span class="text-green-700 font-bold" v-if="wsConnected">[ONLINE]</span>
          <span class="text-red-900/60 font-bold" v-else>[OFFLINE]</span>
        </div>
        <div class="flex items-center gap-3 text-[12px]">
          <button
            @click="showSettings = !showSettings"
            class="text-red-500/70 hover:text-red-400 transition-colors cursor-pointer select-none border-none bg-transparent outline-none font-mono"
          >
            {{ showSettings ? t.hide_config : t.show_config }}
          </button>
          <button
            @click="emit('toggleSaveSlots')"
            class="text-red-500/70 hover:text-red-400 transition-colors cursor-pointer border-none bg-transparent outline-none font-mono"
          >
            {{ t.memory_access }}
          </button>
          <span class="text-red-950/50 select-none">|</span>
          <span class="text-blood-dim select-none">MS: {{ latency }}</span>
        </div>
      </div>

      <!-- ── Layer 2: Collapsible Config/Settings Pane ── -->
      <div
        v-show="showSettings"
        class="border-b border-red-950 bg-[#070000] p-5 text-sm space-y-4 shrink-0 z-20 transition-all duration-300"
      >
        <div class="grid grid-cols-3 gap-4 text-xs">
          <!-- Column 1: API parameters -->
          <div class="space-y-2.5">
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">API KEY</label>
              <input
                v-model="form.api_key"
                type="password"
                placeholder="在此输入你的 API Key"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">MODEL NAME</label>
              <input
                v-model="form.model_name"
                type="text"
                placeholder="默认: deepseek-v4-flash"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
          </div>

          <!-- Column 2: URL endpoints -->
          <div class="space-y-2.5">
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">API BASE URL</label>
              <input
                v-model="form.api_base"
                type="text"
                placeholder="https://api.deepseek.com"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">TTS BASE URL</label>
              <input
                v-model="form.tts_base"
                type="text"
                placeholder="http://127.0.0.1:9880"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
          </div>

          <!-- Column 3: Reference paths -->
          <div class="space-y-2.5">
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">参考音频路径 (.wav)</label>
              <div class="flex gap-2">
                <input
                  v-model="form.refer_wav_path"
                  type="text"
                  placeholder="选择参考音频"
                  class="flex-1 terminal-input px-3 py-1.5 text-[13px] h-9"
                />
                <button
                  @click="requestFilePicker('refer_wav_path', '选择参考音频 (.wav)', [['Audio Files', '*.wav'], ['All Files', '*.*']])"
                  type="button"
                  class="px-2 h-9 border border-red-900 bg-black text-red-500 hover:border-red-500 hover:text-red-400 text-xs font-bold cursor-pointer select-none"
                >
                  浏览
                </button>
              </div>
            </div>
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">参考文本内容</label>
              <input
                v-model="form.prompt_text"
                type="text"
                placeholder="参考音频的中文文本"
                class="w-full terminal-input px-3 py-1.5 text-[13px] h-9"
              />
            </div>
          </div>

          <!-- GPT / SoVITS Model Weights -->
          <div class="col-span-2 grid grid-cols-2 gap-4">
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">GPT 权重路径 (.ckpt)</label>
              <div class="flex gap-2">
                <input
                  v-model="form.gpt_weights_path"
                  type="text"
                  class="flex-1 terminal-input px-3 py-1.5 text-[13px] h-9"
                />
                <button
                  @click="requestFilePicker('gpt_weights_path', '选择GPT权重 (.ckpt)', [['Weights', '*.ckpt'], ['All Files', '*.*']])"
                  type="button"
                  class="px-2 h-9 border border-red-900 bg-black text-red-500 hover:border-red-500 hover:text-red-400 text-xs font-bold cursor-pointer select-none"
                >
                  浏览
                </button>
              </div>
            </div>
            <div>
              <label class="text-red-500/80 block mb-1.5 font-bold">SoVITS 权重路径 (.pth)</label>
              <div class="flex gap-2">
                <input
                  v-model="form.sovits_weights_path"
                  type="text"
                  class="flex-1 terminal-input px-3 py-1.5 text-[13px] h-9"
                />
                <button
                  @click="requestFilePicker('sovits_weights_path', '选择SoVITS权重 (.pth)', [['Weights', '*.pth'], ['All Files', '*.*']])"
                  type="button"
                  class="px-2 h-9 border border-red-900 bg-black text-red-500 hover:border-red-500 hover:text-red-400 text-xs font-bold cursor-pointer select-none"
                >
                  浏览
                </button>
              </div>
            </div>
          </div>

          <!-- Language settings & buttons -->
          <div class="flex flex-col justify-end space-y-2">
            <div class="flex gap-2">
              <button
                @click="doSaveSettings"
                class="flex-1 h-9 border border-blood text-blood text-xs transition-colors bg-transparent select-none cursor-pointer font-bold mita-interactive-ui"
              >
                {{ t.save_config }}
              </button>
              <button
                @click="doTestConnection"
                :disabled="testing"
                class="flex-1 h-9 border border-blood-dim text-blood-dim text-xs transition-colors bg-transparent select-none cursor-pointer disabled:opacity-30 font-bold mita-interactive-ui"
              >
                {{ t.api_test }}
              </button>
            </div>
          </div>
        </div>

        <!-- Connection Test Results -->
        <div v-if="testResult" class="text-xs flex items-center justify-between mt-1 select-none font-bold">
          <span :class="testResult.startsWith('✓') ? 'text-green-600' : 'text-red-600'">{{ testResult }}</span>
          <span v-if="testing" class="animate-pulse text-blood-dim">Testing...</span>
        </div>
      </div>

      <!-- ── Layer 3: Status Bar (Square blocks progress bars) ── -->
      <div class="h-9 border-b border-red-950 bg-[#0c0000] flex items-center justify-between px-4 shrink-0 text-[13px] z-20 select-none">
        <!-- Day Counter (Left) -->
        <div class="flex items-center gap-1 font-bold text-red-500">
          <span>{{ getDayText }}</span>
        </div>

        <!-- Metric Bars in Middle -->
        <div class="flex items-center gap-5">
          <!-- Favorability (Pure Red) -->
          <div class="flex items-center gap-1.5 font-bold text-[#ef4444]">
            <span>{{ t.favor }}</span>
            <span class="tracking-wider">[{{ getBlockBar(favorability) }}]</span>
            <span class="w-6 text-right">{{ favorability }}</span>
          </div>

          <!-- Suspicion (Dark Red/Green Contrast Grids) -->
          <div class="flex items-center gap-1.5 font-bold text-green-500">
            <span>{{ t.sus }}</span>
            <span class="tracking-wider flex">
              <span class="text-green-950/40 select-none">[</span>
              <span class="text-green-500">{{ getFilledBlocks(suspicion) }}</span>
              <span class="text-red-900/60">{{ getEmptyBlocks(suspicion) }}</span>
              <span class="text-green-950/40 select-none">]</span>
            </span>
            <span class="w-6 text-right">{{ suspicion }}</span>
          </div>

          <!-- Escape Rate (Narrow Pixel Bar) -->
          <div class="flex items-center gap-1.5 font-bold text-yellow-600">
            <span>{{ t.escape }}</span>
            <span class="tracking-wider">[{{ getBlockBar(escapeRate) }}]</span>
            <span class="w-8 text-right">{{ escapeRate }}%</span>
          </div>
        </div>

        <!-- API status (Right) -->
        <div class="text-[12px] text-blood-dim flex items-center gap-1.5 select-none font-bold">
          <span>{{ t.api_status }}</span>
          <span class="text-green-700 font-bold" v-if="form.api_key">ONLINE</span>
          <span class="text-zinc-600 font-bold" v-else>OFFLINE</span>
        </div>
      </div>

      <!-- ── Layer 4: ECG Canvas (Height: 45px) ── -->
      <div class="h-[45px] border-b border-red-950 bg-black shrink-0 relative overflow-hidden flex items-center z-10">
        <EcgCanvas
          :suspicion="ecgSuspicion"
          :favorability="ecgFavorability"
          :active-glitches="activeGlitches"
          class="absolute inset-0 h-full w-full"
        />
      </div>

      <!-- ── Layer 5: Chat Display Area ── -->
      <div
        ref="chatLogRef"
        class="flex-1 overflow-y-auto overflow-x-hidden p-6 bg-black hacker-scroll border border-red-950/80 m-4 rounded relative z-0"
        :class="{ 
          'animate-shake': activeGlitches.has('font_shake'),
          'chat-shattered': props.suspicion >= 75
        }"
      >
        <!-- Cinematic Mita Yandere Eyes Watermark -->
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none z-0 select-none transition-all duration-1000" :style="{ opacity: 0.03 + (props.suspicion / 100) * 0.08 }">
          <span class="text-[140px] text-red-600 font-bold mita-chromatic-text tracking-widest leading-none select-none">👁️ 👁️</span>
        </div>

        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          class="mb-4 leading-relaxed block font-mono text-[16px]"
        >
          <!-- System messages (Darker grey but readable, 14px) -->
          <div v-if="msg.role === 'system'" class="text-zinc-500 block font-mono text-[14px] leading-relaxed">
            {{ msg.content }}
          </div>

          <!-- Agent commentary (Lilac purple, 14px) -->
          <div v-else-if="msg.role === 'agent'" class="text-purple-400 italic block font-mono text-[14px] leading-relaxed">
            {{ msg.content }}
          </div>

          <!-- User dialogue (Vibrant Orange/Yellow prefix, bold, 18px) -->
          <div v-else-if="msg.role === 'user'" class="flex gap-1 text-[#f97316] font-bold block font-mono text-[18px] leading-relaxed">
            <span class="font-mono">{{ getUserPrefix }}</span>
            <span class="font-mono">{{ msg.content }}</span>
          </div>

          <!-- Assistant (Saki) Response -->
          <div v-else-if="msg.role === 'assistant'" class="flex flex-col gap-1.5 block font-mono">
            <!-- Think inner thoughts (Aggressive Deep Red Synapse log, 17px) -->
            <div
              v-if="msg.think"
              class="p-4 mb-3 border border-red-950 bg-[#080101] block font-mono leading-relaxed text-[17px] rounded"
              style="color: #fda4af; text-shadow: 0 0 6px rgba(253, 164, 175, 0.4); border-left: 4px solid #ef4444;"
            >
              <div class="text-[12px] text-red-500/60 uppercase font-bold tracking-widest mb-1 select-none">[ 纱希的神经意识独白 / COGNITIVE ANALYSIS ]</div>
              <div>（{{ msg.think }}）</div>
            </div>
            <!-- Verbal speech (Vibrant Red or character custom styling, 19px) -->
            <div
              v-if="msg.content"
              class="block font-mono leading-relaxed text-[19px] font-medium"
              :style="{ color: getCharacterColor }"
              :class="{ 
                'animate-glitch-text': activeGlitches.has('font_shake'),
                'mita-chromatic-text': props.suspicion >= 55
              }"
            >
              <span v-if="!charId || charId === 'saki'">
                <span v-if="isCarnageMessage(msg.content)">{{ getSakiPrefix }}█▄ <span v-html="formatAssistantSpeech(msg.content)"></span> ▆▇█</span>
                <span v-else>{{ getSakiPrefix }}<span v-html="formatAssistantSpeech(msg.content)"></span></span>
              </span>
              <span v-else v-html="formatAssistantSpeech(msg.content)"></span>
            </div>
            <!-- Translation display -->
            <div
              v-if="msg.translation"
              class="block font-mono leading-relaxed text-[19px] font-semibold mt-2 border-t border-red-950/40 pt-2"
              style="color: #ff2222; text-shadow: 0 0 10px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.4);"
              :class="{ 'mita-chromatic-text': props.suspicion >= 55 }"
            >
              （{{ msg.translation }}）
            </div>
          </div>
        </div>

        <!-- Streaming Typewriter Frame (Upgraded Spec-v6 Sequential Queue Typewriter) -->
        <div v-if="typewriterDisplayThink || typewriterDisplaySpeech || translationTypewriterDisplay" class="mb-4 block font-mono">
          <!-- Lavender Thoughts -->
          <div
            v-if="typewriterDisplayThink"
            class="p-4 mb-3 border border-red-950 bg-[#080101] block font-mono leading-relaxed text-[17px] rounded"
            style="color: #fda4af; text-shadow: 0 0 6px rgba(253, 164, 175, 0.4); border-left: 4px solid #ef4444;"
          >
            <div class="text-[12px] text-red-500/60 uppercase font-bold tracking-widest mb-1 select-none">[ 纱希的神经意识独白 / COGNITIVE ANALYSIS ]</div>
            <span>（{{ typewriterDisplayThink }}</span>
            <span v-if="typewriterMode === 'think'" class="retro-caret font-mono">█</span>
            <span>）</span>
          </div>

          <!-- Neon Red Speech -->
          <div
            v-if="typewriterDisplaySpeech"
            class="block font-mono leading-relaxed text-[19px] font-medium"
            :style="{ color: getCharacterColor }"
            :class="{ 'mita-chromatic-text': props.suspicion >= 55 }"
          >
            <span v-if="!charId || charId === 'saki'">
              <span v-if="isCarnageMessage(typewriterDisplaySpeech)">
                {{ getSakiPrefix }}█▄ <span v-html="formatAssistantSpeech(typewriterDisplaySpeech)"></span> ▆▇█
              </span>
              <span v-else>
                {{ getSakiPrefix }}<span v-html="formatAssistantSpeech(typewriterDisplaySpeech)"></span>
              </span>
            </span>
            <span v-else v-html="formatAssistantSpeech(typewriterDisplaySpeech)"></span>
            <span v-if="typewriterMode === 'speech'" class="retro-caret font-mono">█</span>
          </div>

          <!-- Translation -->
          <div
            v-if="translationTypewriterDisplay"
            class="block font-mono leading-relaxed text-[19px] font-semibold mt-2 border-t border-red-950/40 pt-2"
            style="color: #ff2222; text-shadow: 0 0 10px rgba(255, 0, 0, 0.7), 0 0 20px rgba(255, 0, 0, 0.4);"
            :class="{ 'mita-chromatic-text': props.suspicion >= 55 }"
          >
            <span>（{{ translationTypewriterDisplay }}</span>
            <span v-if="typewriterMode === 'translation'" class="retro-caret font-mono">█</span>
            <span>）</span>
          </div>
        </div>
      </div>

      <!-- ── Layer 6: Bottom Input Area ── -->
      <div class="h-12 border-t border-red-950 bg-[#040000] flex items-center px-4 gap-3 shrink-0 z-20">
        <span class="text-red-900 shrink-0 font-mono text-sm font-bold select-none">&gt;</span>
        <input
          ref="inputRef"
          v-model="inputText"
          type="text"
          :placeholder="getInputPlaceholder"
          :disabled="disabled || hijackActive"
          class="flex-1 bg-transparent border border-red-950/50 px-3 py-1 outline-none text-red-500 placeholder-red-950/30 text-base font-mono focus:border-red-700 focus:shadow-[0_0_10px_rgba(239,68,68,0.15)] rounded transition-all"
          @keydown="handleKeydown"
          autofocus
        />
        <button
          @click="doSend"
          :disabled="disabled"
          class="px-5 py-1.5 border font-bold text-sm cursor-pointer select-none transition-all rounded font-mono mita-interactive-ui"
          :class="props.hijackActive 
            ? 'border-red-500 text-red-500 bg-red-950/20 animate-pulse-red shadow-[0_0_15px_rgba(239,68,68,0.4)]'
            : 'border-red-900 bg-black text-red-500 disabled:opacity-20 disabled:cursor-not-allowed'"
        >
          {{ props.hijackActive ? '看着我❤' : t.respond }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import EcgCanvas from './EcgCanvas.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  thinkText: { type: String, default: '' },
  speechText: { type: String, default: '' },
  translationText: { type: String, default: '' },
  systemUsername: { type: String, default: '玩家' },
  activeGlitches: { type: Set, default: () => new Set() },
  gameOver: { type: Boolean, default: false },
  ending: { type: Object, default: null },
  hijackActive: { type: Boolean, default: false },
  charId: { type: String, default: 'saki' },
  customCharacters: { type: Array, default: () => [] },
  wsConnected: { type: Boolean, default: false },
  day: { type: Number, default: 1 },
  language: { type: String, default: '中文' },
  latency: { type: Number, default: 0 },
  favorability: { type: Number, default: 50 },
  suspicion: { type: Number, default: 20 },
  escapeRate: { type: Number, default: 0 },
  characterSprite: { type: String, default: null },
  savedConfig: { type: Object, default: () => ({}) },
  ecgSuspicion: { type: Number, default: 20 },
  ecgFavorability: { type: Number, default: 50 },
})

const emit = defineEmits([
  'send',
  'restart',
  'toggleSaveSlots',
  'saveConfig',
  'triggerGlitch',
  'removeGlitch',
  'typing-complete',
])

function injectSystemUsername(text) {
  if (!text) return ''
  if (props.suspicion < 75) return text
  const name = props.systemUsername || '玩家'
  return text
    .replace(/亲爱的/g, name)
    .replace(/darling/gi, name)
    .replace(/あなた/g, name)
    .replace(/你/g, name)
    .replace(/You/g, name)
}

// ── GameTerminal Multi-language UI dictionaries ──
const LOCALIZATION = {
  '中文': {
    title: '[ 纱希的神经意识接口 ]',
    hide_config: '[ 收起配置通道 ]',
    show_config: '[ 展开配置通道 ]',
    memory_access: '[ 💾 记忆存取 ]',
    save_config: '保存配置',
    api_test: 'API 测试',
    day: '第 {day} 日',
    favor: '好感 ❤',
    sus: '疑心 👁',
    escape: '脱出 🔋',
    api_status: 'API 状态:',
    inner_thought: '[内心] ',
    respond: '回应她',
    input_placeholder: '输入你想说的话...',
    game_over: '游戏结束...',
    user_prefix: '你: ',
    saki_prefix: '纱希: ',
    think_prefix: '（纱希的内心戏：',
    think_suffix: '）',
  },
  'English': {
    title: "[ Saki's Conscious Interface ]",
    hide_config: '[ Hide Config Channel ]',
    show_config: '[ Show Config Channel ]',
    memory_access: '[ 💾 Memory Access ]',
    save_config: 'Save Config',
    api_test: 'API Test',
    day: 'Day {day}',
    favor: 'Favor ❤',
    sus: 'Sus 👁',
    escape: 'Escape 🔋',
    api_status: 'API Status:',
    inner_thought: '[Thought] ',
    respond: 'Respond',
    input_placeholder: 'Type your message...',
    game_over: 'Game Over...',
    user_prefix: 'You: ',
    saki_prefix: 'Saki: ',
    think_prefix: "(Saki's Thoughts: ",
    think_suffix: ')',
  },
  '日本語': {
    title: '[ 紗希の神経意識インターフェース ]',
    hide_config: '[ 設定チャネルを閉じる ]',
    show_config: '[ 設定チャネルを展開する ]',
    memory_access: '[ 💾 記憶体存取 ]',
    save_config: '設定保存',
    api_test: 'APIテスト',
    day: '第 {day} 日',
    favor: '好感 ❤',
    sus: '疑心 👁',
    escape: '脱出 🔋',
    api_status: 'API状態:',
    inner_thought: '[内心] ',
    respond: '彼女に応える',
    input_placeholder: '言葉を入力してください...',
    game_over: 'ゲームオーバー...',
    user_prefix: 'あなた: ',
    saki_prefix: '紗希: ',
    think_prefix: '（紗希の本音：',
    think_suffix: '）',
  }
}

const t = computed(() => LOCALIZATION[props.language] || LOCALIZATION['中文'])

const getDayText = computed(() => {
  return t.value.day.replace('{day}', props.day)
})

const getUserPrefix = computed(() => {
  return t.value.user_prefix
})

const getSakiPrefix = computed(() => {
  return t.value.saki_prefix || '纱希: '
})

const getThinkPrefix = computed(() => {
  return t.value.think_prefix || '（纱希的内心戏：'
})

const getThinkSuffix = computed(() => {
  return t.value.think_suffix || '）'
})

const getInputPlaceholder = computed(() => {
  if (props.gameOver) return t.value.game_over
  if (props.hijackActive) return hijackText
  return t.value.input_placeholder
})


const showSettings = ref(false)
const inputText = ref('')
const inputRef = ref(null)
const chatLogRef = ref(null)

const testing = ref(false)
const testResult = ref('')

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

// Populate settings from App props config
watch(() => props.savedConfig, (conf) => {
  if (conf && Object.keys(conf).length > 0) {
    if (conf.api_key !== undefined) form.api_key = conf.api_key
    if (conf.api_base !== undefined) form.api_base = conf.api_base
    if (conf.model_name !== undefined) form.model_name = conf.model_name
    if (conf.selected_language !== undefined) form.selected_language = conf.selected_language
    if (conf.gpt_sovits_url !== undefined) form.tts_base = conf.gpt_sovits_url
    if (conf.refer_wav_path !== undefined) form.refer_wav_path = conf.refer_wav_path
    if (conf.prompt_text !== undefined) form.prompt_text = conf.prompt_text
    if (conf.gpt_weights_path !== undefined) form.gpt_weights_path = conf.gpt_weights_path
    if (conf.sovits_weights_path !== undefined) form.sovits_weights_path = conf.sovits_weights_path
  }
}, { immediate: true, deep: true })

// ── Retro square progress blocks generator helpers ──
function getFilledBlocks(val) {
  const total = 8
  const filled = Math.round((val / 100) * total)
  return '█'.repeat(filled)
}

function getEmptyBlocks(val) {
  const total = 8
  const filled = Math.round((val / 100) * total)
  const empty = total - filled
  return '░'.repeat(empty)
}

function getBlockBar(val) {
  return getFilledBlocks(val) + getEmptyBlocks(val)
}

// ── Character Color Determination ──
const getCharacterColor = computed(() => {
  if (!props.charId || props.charId === 'saki') return '#ef4444' // Saki bright red
  const customChar = props.customCharacters?.find(c => c.id === props.charId || c.character_name === props.charId)
  return customChar?.text_color || '#ef4444'
})

function isCarnageMessage(content) {
  if (!content) return false
  return (props.suspicion >= 85) || DANGER_WORDS_CARNAGE.some(w => content.toLowerCase().includes(w))
}

// Hijack variables
const hijackText = '你走不掉的你走不掉的你走不掉的...'
let hijackIndex = 0

const disabled = computed(() => props.gameOver)
const inputPlaceholder = computed(() => {
  if (props.gameOver) return '游戏结束...'
  if (props.hijackActive) return hijackText
  return '输入你想说的话...'
})

// ── Typewriter Logic ──
const typewriterDisplayThink = ref('')
const typewriterDisplaySpeech = ref('')
const translationTypewriterDisplay = ref('')
const typewriterMode = ref('idle') // 'idle' | 'think' | 'speech' | 'translation'
const speedMultiplier = ref(1.0)
let typewriterInterval = null

// ── speed_shift glitch: random typewriter speed modifier ──
watch(() => props.activeGlitches.has('speed_shift'), (active) => {
  if (active) {
    const multipliers = [0.02, 0.05, 5.0, 10.0]
    speedMultiplier.value = multipliers[Math.floor(Math.random() * multipliers.length)]
    setTimeout(() => { speedMultiplier.value = 1.0 }, 1200)
  }
})

const DANGER_WORDS_CARNAGE = [
  "小刀", "地下室", "杀", "死", "血", "尸", "毒",
  "escape", "kill", "die", "blood",
  "殺す", "死ぬ", "血", "逃げられない", "毒",
]
const DANGER_WORDS = [
  "死", "杀", "背叛", "离开", "谁", "别的人", "小黑屋", "逃", "小刀", "滚", "锁", "洗澡", "地下室", "老子", "誰"
]

function playTypewriterBeep(isGlitch = false) {
  try {
    if (!beepCtx) beepCtx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = beepCtx.createOscillator()
    const gain = beepCtx.createGain()
    osc.connect(gain)
    gain.connect(beepCtx.destination)
    
    if (isGlitch) {
      osc.type = 'sawtooth'
      osc.frequency.setValueAtTime(120 + Math.random() * 150, beepCtx.currentTime)
      osc.frequency.exponentialRampToValueAtTime(30, beepCtx.currentTime + 0.15)
      gain.gain.setValueAtTime(0.12, beepCtx.currentTime)
      gain.gain.linearRampToValueAtTime(0.005, beepCtx.currentTime + 0.15)
      osc.start()
      osc.stop(beepCtx.currentTime + 0.15)
    } else {
      osc.type = 'sine'
      osc.frequency.value = 850 + Math.random() * 100
      gain.gain.setValueAtTime(0.02, beepCtx.currentTime)
      gain.gain.linearRampToValueAtTime(0.001, beepCtx.currentTime + 0.04)
      osc.start()
      osc.stop(beepCtx.currentTime + 0.04)
    }
  } catch (e) { /* ignore */ }
}

// ── Spec-v6 Sequential Queue Typewriter Engine ──
function startTypewriterSequence(think = '', speech = '', translation = '') {
  if (typewriterInterval) clearInterval(typewriterInterval)
  
  typewriterDisplayThink.value = ''
  typewriterDisplaySpeech.value = ''
  translationTypewriterDisplay.value = ''
  typewriterMode.value = 'think'
  
  let thinkIdx = 0
  let speechIdx = 0
  let transIdx = 0
  
  const finishSequence = () => {
    clearInterval(typewriterInterval)
    typewriterInterval = null
    typewriterMode.value = 'idle'
    
    setTimeout(() => {
      typewriterDisplayThink.value = ''
      typewriterDisplaySpeech.value = ''
      translationTypewriterDisplay.value = ''
      emit('typing-complete')
    }, 800)
  }
  
  const tick = () => {
    if (typewriterMode.value === 'think') {
      const target = props.thinkText || think || ''
      if (thinkIdx < target.length) {
        typewriterDisplayThink.value += target[thinkIdx]
        thinkIdx++
        playTypewriterBeep(false)
        scrollToBottom()
      } else if (props.speechText || speech) {
        typewriterMode.value = 'speech'
      }
    }
    
    else if (typewriterMode.value === 'speech') {
      const target = props.speechText || speech || ''
      const cleanTarget = target.replace(/\|\|.*?\|\|/g, '').replace(/<think>.*?<\/think>/gs, '').trim()
      
      const useCarnage = (props.suspicion >= 85) || DANGER_WORDS_CARNAGE.some(w => cleanTarget.toLowerCase().includes(w))
      
      if (useCarnage && typewriterDisplaySpeech.value !== cleanTarget) {
        typewriterDisplaySpeech.value = cleanTarget
        speechIdx = cleanTarget.length
        playTypewriterBeep(true)
        triggerCarnageGlitches()
        scrollToBottom()
      } else if (speechIdx < cleanTarget.length) {
        const char = cleanTarget[speechIdx]
        typewriterDisplaySpeech.value += char
        speechIdx++
        
        detectAndTriggerDangerGlitches(typewriterDisplaySpeech.value, cleanTarget)
        playTypewriterBeep(false)
        scrollToBottom()
      } else {
        if (props.translationText || translation) {
          typewriterMode.value = 'translation'
        } else {
          finishSequence()
        }
      }
    }
    
    else if (typewriterMode.value === 'translation') {
      const target = props.translationText || translation || ''
      if (transIdx < target.length) {
        translationTypewriterDisplay.value += target[transIdx]
        transIdx++
        scrollToBottom()
      } else {
        finishSequence()
      }
    }
  }
  
  typewriterInterval = setInterval(tick, Math.max(1, 30 / speedMultiplier.value))
}

let shaked = false
function detectAndTriggerDangerGlitches(typed, fullCleanText) {
  const containsDanger = DANGER_WORDS.some(w => fullCleanText.includes(w))
  const typedDanger = DANGER_WORDS.some(w => typed.includes(w))
  
  if (containsDanger && typedDanger && !shaked) {
    shaked = true
    playTypewriterBeep(true)
    emit('triggerGlitch', 'earthquake')
    emit('triggerGlitch', 'font_shake')
    if (Math.random() < 0.4) emit('triggerGlitch', 'static_noise')
    if (Math.random() < 0.3) emit('triggerGlitch', 'fake_error')
    
    setTimeout(() => {
      emit('removeGlitch', 'earthquake')
      emit('removeGlitch', 'font_shake')
      emit('removeGlitch', 'static_noise')
      emit('removeGlitch', 'fake_error')
    }, 1500)
  }
}

function triggerCarnageGlitches() {
  emit('triggerGlitch', 'earthquake')
  emit('triggerGlitch', 'static_noise')
  emit('triggerGlitch', 'color_invert')
  emit('triggerGlitch', 'fake_error')
  emit('triggerGlitch', 'blood_pulse')
  emit('triggerGlitch', 'subliminal_popup')
  emit('triggerGlitch', 'carnage_mode')
  
  setTimeout(() => {
    emit('removeGlitch', 'earthquake')
    emit('removeGlitch', 'static_noise')
    emit('removeGlitch', 'color_invert')
    emit('removeGlitch', 'fake_error')
    emit('removeGlitch', 'blood_pulse')
    emit('removeGlitch', 'subliminal_popup')
    emit('removeGlitch', 'carnage_mode')
  }, 2500 + Math.random() * 1000)
}

watch(() => props.thinkText, (newThink) => {
  if (newThink && typewriterMode.value === 'idle') {
    shaked = false
    startTypewriterSequence()
  }
})

watch(() => props.speechText, (newSpeech) => {
  if (newSpeech && typewriterMode.value === 'idle') {
    shaked = false
    startTypewriterSequence()
  }
})

watch(() => props.translationText, (newTrans) => {
  if (newTrans && typewriterMode.value === 'idle') {
    shaked = false
    startTypewriterSequence()
  }
})

function scrollToBottom() {
  nextTick(() => {
    if (chatLogRef.value) {
      chatLogRef.value.scrollTop = chatLogRef.value.scrollHeight
    }
  })
}

// CRITICAL RESOLUTION: Prevent double text overlapping bug by clearing active typing state immediately
watch(() => props.messages.length, () => {
  if (typewriterInterval) {
    clearInterval(typewriterInterval)
    typewriterInterval = null
  }
  typewriterDisplayThink.value = ''
  typewriterDisplaySpeech.value = ''
  translationTypewriterDisplay.value = ''
  typewriterMode.value = 'idle'
  scrollToBottom()
})

// ── Saki Dialogue Box Alienation Zalgo Formatting ──
const ZALGO_UP = ['̍', '̎', '̄', '̅', '̿', '̑', '̆', '̐', '͒', '͗', '͑', '̇', '̈', '̊', '͂', '̓', '̈́', '͊', '͋', '͌', '̃', '̂', '̌', '͐', '̀', '́', '̋', '̌', '̒', '̓', '̔', '̽', '̾', '̿'];
const ZALGO_DOWN = ['̖', '̗', '̘', '̙', '̜', '̟', '̠', '̤', '̥', '̦', '̩', '̪', '̫', '̬', '̭', '̮', '̯', '̰', '̱', '̲', '̳', '̹', '̺', '̻', '̼', 'ͅ', '̠', '̻', '̼', '̥', '̦', '̩', '̪', '̫', '̬', '̭', '̮', '̯', '̰', '̱', '̲', '̳', '̹', '̺', '̻', '̼', 'ͅ', '͇', '͈', '͉', '͊', '͋', '͌', '̃', '̂', '̌', '͐', '̀', '́', '̋', '̌', '̒', '̓', '̔', '̽', '̾', '̿'];
const ZALGO_MID = ['̕', '̛', '̀', '́', '͘', '̡', '̢', '̧', '̨', '̴', '̵', '̶', '͏', '͜', '͝', '͞', '͟', '͠', '͢', 'ͣ', 'ͤ', 'ͥ', 'ͦ', 'ͧ', 'ͨ', 'ͩ', 'ͪ', 'ͫ', 'ͬ', 'ͭ', 'ͮ', 'ͯ', '̾', '̿'];

function addZalgo(char, count = 2) {
  let result = char
  for (let i = 0; i < count; i++) {
    result += ZALGO_UP[Math.floor(Math.random() * ZALGO_UP.length)]
    result += ZALGO_DOWN[Math.floor(Math.random() * ZALGO_DOWN.length)]
    result += ZALGO_MID[Math.floor(Math.random() * ZALGO_MID.length)]
  }
  return result
}

function alienateText(text) {
  if (!text) return ''
  if (props.suspicion < 75) return text

  const parts = text.split(/(<[^>]+>)/g)
  return parts.map(part => {
    if (part.startsWith('<') && part.endsWith('>')) {
      return part
    }
    
    return part.split('').map(char => {
      if (char === ' ' || char === '\n') return char
      
      const shouldMitate = Math.random() < 0.25
      if (shouldMitate) {
        const size = 100 + Math.floor(Math.random() * 50)
        const xOffset = -4 + Math.floor(Math.random() * 8)
        const yOffset = -4 + Math.floor(Math.random() * 8)
        const zalg = addZalgo(char, 1 + Math.floor(Math.random() * 2))
        const isBlood = Math.random() < 0.12
        const animation = isBlood ? 'animate-blood-drips' : ''
        
        return `<span style="font-size: ${size}%; transform: translate(${xOffset}px, ${yOffset}px); display: inline-block; position: relative;" class="${animation}">${zalg}</span>`
      }
      return char
    }).join('')
  }).join('')
}

function formatAssistantSpeech(text) {
  let processed = injectSystemUsername(text)
  return alienateText(processed)
}

// ── Web Audio API Mechanical Keyboard Clicks & Carriage Synthesizer ──
let audioCtx = null

function playTypewriterClickSound(isEnter = false) {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume()
    }

    const now = audioCtx.currentTime

    if (isEnter) {
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(1350, now)
      osc.frequency.exponentialRampToValueAtTime(1150, now + 0.28)
      gain.gain.setValueAtTime(0.05, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.38)
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.start(now)
      osc.stop(now + 0.4)

      const bufferSize = audioCtx.sampleRate * 0.22
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate)
      const data = buffer.getChannelData(0)
      for (let i = 0; i < bufferSize; i++) {
        const t = i / audioCtx.sampleRate
        data[i] = (Math.random() * 2 - 1) * Math.exp(-14 * t) * (0.12 + 0.08 * Math.sin(90 * t))
      }
      const noise = audioCtx.createBufferSource()
      noise.buffer = buffer
      const noiseGain = audioCtx.createGain()
      noiseGain.gain.setValueAtTime(0.07, now)
      noiseGain.gain.exponentialRampToValueAtTime(0.001, now + 0.22)
      noise.connect(noiseGain)
      noiseGain.connect(audioCtx.destination)
      noise.start(now)
      noise.stop(now + 0.25)

    } else {
      const bufferSize = audioCtx.sampleRate * 0.04
      const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate)
      const data = buffer.getChannelData(0)
      for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-170 * (i / audioCtx.sampleRate))
      }
      const transient = audioCtx.createBufferSource()
      transient.buffer = buffer
      
      const filter = audioCtx.createBiquadFilter()
      filter.type = 'bandpass'
      filter.frequency.value = 950 + Math.random() * 500
      filter.Q.value = 2.0

      const gain = audioCtx.createGain()
      gain.gain.setValueAtTime(0.04 + Math.random() * 0.02, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035)

      transient.connect(filter)
      filter.connect(gain)
      gain.connect(audioCtx.destination)
      transient.start(now)
      transient.stop(now + 0.04)

      const osc = audioCtx.createOscillator()
      const oscGain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(135 + Math.random() * 70, now)
      oscGain.gain.setValueAtTime(0.015, now)
      oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.075)
      
      osc.connect(oscGain)
      oscGain.connect(audioCtx.destination)
      osc.start(now)
      osc.stop(now + 0.075)
    }
  } catch (e) {}
}

// ── Keyboard Hijack ──
function handleKeydown(e) {
  if (props.hijackActive) {
    e.preventDefault()
    if (hijackIndex < hijackText.length) {
      inputText.value += hijackText[hijackIndex]
      hijackIndex++
    }
    playTypewriterClickSound(false)
    return
  }

  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    playTypewriterClickSound(true)
    doSend()
  } else {
    if (e.key.length === 1 || e.key === 'Backspace' || e.key === 'Delete') {
      playTypewriterClickSound(false)
    }
  }
}

let beepCtx = null

function doSend() {
  const text = inputText.value.trim()
  if (!text || props.gameOver) return

  if (props.hijackActive) {
    emit('send', inputText.value)
    inputText.value = ''
    hijackIndex = 0
    return
  }

  emit('send', text)
  inputText.value = ''
}

// ── Config Operations ──
function doSaveSettings() {
  emit('saveConfig', {
    api_key: form.api_key,
    api_base: form.api_base,
    model_name: form.model_name,
    gpt_sovits_url: form.tts_base,
    selected_language: form.selected_language,
    refer_wav_path: form.refer_wav_path,
    prompt_text: form.prompt_text,
    gpt_weights_path: form.gpt_weights_path,
    sovits_weights_path: form.sovits_weights_path,
  })
  testResult.value = '✓ 配置信息已下发至核心'
  setTimeout(() => { testResult.value = '' }, 3000)
}

async function doTestConnection() {
  testing.value = true
  testResult.value = ''
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
      testResult.value = '✓ API 链接成功 — 神经元通路激活'
    } else {
      if (contentType.includes('text/html')) {
        testResult.value = '✗ API 链接失败: 返回了 HTML，请检查 Base URL 格式'
      } else {
        testResult.value = `✗ API 返回错误 HTTP ${resp.status}`
      }
    }
  } catch (e) {
    testResult.value = `✗ API 链接失败: ${e.message}`
  } finally {
    testing.value = false
  }
}

const handleFilePickerSelected = (e) => {
  const { field, path } = e.detail
  if (field in form) {
    form[field] = path
  }
}

function requestFilePicker(field, title, filetypes) {
  window.dispatchEvent(new CustomEvent('request-file-picker', {
    detail: { field, title, filetypes }
  }))
}

onMounted(() => {
  inputRef.value?.focus()
  scrollToBottom()
  window.addEventListener('file-picker-selected', handleFilePickerSelected)
})

onUnmounted(() => {
  if (typewriterInterval) clearInterval(typewriterInterval)
  window.removeEventListener('file-picker-selected', handleFilePickerSelected)
})
</script>

<style scoped>
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
