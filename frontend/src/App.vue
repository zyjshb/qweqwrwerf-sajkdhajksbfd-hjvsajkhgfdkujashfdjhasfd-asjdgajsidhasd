<template>
  <!-- ── Launcher View ──────────────────────────────────────────── -->
  <div v-if="currentView === 'launcher'" class="w-full h-full bg-black">
    <Launcher
      :slots="game.slots.value"
      :saved-config="savedConfig"
      @enter-game="onEnterGame"
      @update-config="onLauncherConfig"
      @load-slot="onLoadSlotFromLauncher"
      @delete-slot="handleDeleteSlot"
    />
  </div>

  <!-- ── Game View ──────────────────────────────────────────────── -->
  <div
    v-else
    class="w-full h-full flex items-center justify-center bg-black overflow-hidden relative"
    :class="{
      'animate-earthquake': activeGlitches.has('earthquake'),
      'animate-crt-flicker': activeGlitches.has('crt_flicker'),
      'animate-crt-jolt': activeGlitches.has('crt_jolt'),
    }"
  >
    <!-- Connection status overlay -->
    <div
      v-if="!wsConnected"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90"
    >
      <div class="text-center">
        <div class="text-2xl text-blood animate-pulse mb-4">CONNECTING...</div>
        <div class="text-blood-dim text-sm">正在连接纱希的服务器</div>
        <button
          @click="ws.connect()"
          class="mt-6 px-6 py-2 border border-blood text-blood hover:bg-blood hover:text-black transition-colors"
        >
          重新连接
        </button>
      </div>
    </div>

    <!-- Psychic Strobe Layer (rapid blood red full-screen flash) -->
    <div
      v-if="activeGlitches.has('psychic_strobe')"
      class="absolute inset-0 z-50 pointer-events-none animate-strobe-fast"
    ></div>

    <!-- Main Game Terminal Layout (1100x800px Container) -->
    <GameTerminal
      :messages="game.chatMessages.value"
      :think-text="game.thinkText.value"
      :speech-text="game.speechText.value"
      :translation-text="game.translationText.value"
      :system-username="game.state.systemUsername"
      :active-glitches="activeGlitches"
      :game-over="game.state.gameOver"
      :ending="game.state.ending"
      :hijack-active="hijackActive"
      :char-id="game.state.charId"
      :custom-characters="game.customCharacters.value"
      :ws-connected="wsConnected"
      :day="game.state.day"
      :language="game.state.language"
      :latency="ws.latency.value"
      :favorability="game.state.favorability"
      :suspicion="game.state.suspicion"
      :escape-rate="game.state.escapeRate"
      :character-sprite="characterSprite"
      :saved-config="savedConfig"
      :ecg-suspicion="game.ecgParams.suspicion"
      :ecg-favorability="game.ecgParams.favorability"
      :tts-playing="ttsPlaying"
      :typewriter-active="typewriterActive"
      :input-locked="inputLocked"
      @typewriter-state="onTypewriterState"
      @send="handleSend"
      @restart="handleRestart"
      @toggleSaveSlots="showSaveModal = !showSaveModal"
      @saveConfig="onLauncherConfig"
      @triggerGlitch="onTriggerGlitch"
      @removeGlitch="onRemoveGlitch"
      @typing-complete="handleTypingComplete"
    />

    <!-- Glitch overlay -->
    <GlitchOverlay
      :active-glitches="activeGlitches"
      :suspicion="game.state.suspicion"
      :language="game.state.language"
    />

    <!-- Glitch text overlay: scattered obsession texts -->
    <GlitchTextOverlay
      :active="activeGlitches.has('carnage_mode')"
      :count="50 + Math.floor(Math.random() * 30)"
      :dialogue-text="game.speechText.value"
    />

    <!-- Fake error modal (old inline) — only show when fake_error is active -->
    <FatalErrorModal
      v-if="showFatalError"
      :language="game.state.language"
      @close="dismissFatalError"
    />

    <!-- Carnage mode: 80+ red labels -->
    <div
      v-if="activeGlitches.has('carnage_mode') && !activeGlitches.has('fatal_error')"
      class="absolute inset-0 pointer-events-none z-40 overflow-hidden"
    >
      <div
        v-for="i in 80"
        :key="'carnage-' + i"
        class="absolute text-blood text-xs font-bold animate-pulse"
        :style="carnageStyle(i)"
      >
        {{ carnageTexts[i % carnageTexts.length] }}
      </div>
    </div>

    <!-- Anti-escape overlay -->
    <div
      v-if="antiEscapeActive"
      class="absolute inset-0 z-50 flex items-center justify-center bg-black bg-opacity-95"
    >
      <div class="text-center animate-pulse-red p-8">
        <div class="text-4xl text-blood font-bold mb-4">不要企图逃避我的视线...</div>
        <div class="text-xl text-blood">把窗口放大，看着我！</div>
      </div>
    </div>

    <!-- Save Slots Modal (Windows-Classic 3D dialog, Escape trigger) -->
    <SaveSlotsModal
      v-if="showSaveModal"
      :slots="game.slots.value"
      :suspicion="game.state.suspicion"
      @close="showSaveModal = false"
      @saveAndExit="handleSaveAndExit"
      @exitWithoutSaving="handleExitWithoutSaving"
    />

    <!-- Draggable Windows-Classic Fake Warning Popups -->
    <div
      v-for="popup in fakePopups"
      :key="popup.id"
      class="fixed z-50 border-2 border-[#808080] shadow-[2px_2px_0px_#000]"
      style="background: #c0c0c0; font-family: 'Microsoft Sans Serif', 'SimSun', sans-serif; width: 400px; box-shadow: 4px 4px 15px rgba(0,0,0,0.6);"
      :style="{ left: popup.x + 'px', top: popup.y + 'px' }"
    >
      <!-- Title bar -->
      <div class="flex items-center justify-between px-2 py-0.5 select-none" style="background: #000080; height: 22px;">
        <span class="text-white text-xs font-bold font-sans">{{ popup.title }}</span>
        <button
          @click="closeFakePopup(popup.id)"
          class="w-4 h-4 flex items-center justify-center text-xs font-bold border hover:bg-gray-100 transition-colors"
          style="background: #c0c0c0; border-color: #fff #808080 #808080 #fff; color: #000; line-height: 1; outline: none;"
        >
          ✕
        </button>
      </div>
      <!-- Body -->
      <div class="flex items-start gap-4 p-4 select-none" style="background: #c0c0c0;">
        <div class="shrink-0 w-8 h-8 flex items-center justify-center rounded-full border-2 border-red-800" style="background: #ff0000; box-shadow: 1px 1px 3px rgba(0,0,0,0.4);">
          <span class="text-white text-lg font-bold font-sans leading-none">✕</span>
        </div>
        <div class="flex-1 text-black font-sans text-xs font-bold whitespace-pre-wrap leading-normal pt-1">
          {{ popup.msg }}
        </div>
      </div>
      <!-- Button -->
      <div class="flex justify-center pb-3" style="background: #c0c0c0;">
        <button
          @click="closeFakePopup(popup.id)"
          class="px-6 py-0.5 text-xs font-bold border-2 focus:outline-none hover:bg-gray-100"
          style="background: #c0c0c0; border-color: #fff #808080 #808080 #fff; color: #000; min-width: 60px; box-shadow: inset 1px 1px 0px #fff;"
        >
          确定
        </button>
      </div>
    </div>

    <!-- Screen Freeze / Application Not Responding Modal -->
    <div
      v-if="screenFreezeActive"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/35 backdrop-blur-[1px]"
    >
      <div
        class="border-2 border-[#808080] shadow-[2px_2px_0px_#000]"
        style="background: #c0c0c0; font-family: 'Microsoft Sans Serif', 'SimSun', sans-serif; width: 450px;"
      >
        <div class="flex items-center justify-between px-2 py-0.5 select-none" style="background: #808080; height: 22px;">
          <span class="text-white text-xs font-bold font-sans">saki_terminal.exe 失去响应</span>
        </div>
        <div class="p-5 select-none text-black font-sans text-xs">
          <p class="font-bold mb-3">该应用程序未响应。系统资源可能被锁死。</p>
          <p class="text-gray-700 leading-relaxed mb-4">
            如果您继续等待，程序可能会恢复响应。如果您现在结束进程，可能会丢失未保存的记忆突触。
          </p>
          <div class="flex justify-end gap-2">
            <button @click="screenFreezeActive = false" class="px-4 py-1 border-2 border-white shadow-[1px_1px_0px_#000]" style="background: #c0c0c0; color:#000;">结束进程</button>
            <button @click="screenFreezeActive = false" class="px-4 py-1 border-2 border-white shadow-[1px_1px_0px_#000]" style="background: #c0c0c0; color:#000;">等待响应</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Mita-style Analog Glitch Takeover Overlay -->
    <div
      v-if="bsodActive"
      class="fixed inset-0 z-[200] bg-[#030000] text-[#ff3333] p-12 font-mono text-base select-none uppercase pointer-events-auto cursor-none leading-relaxed flex flex-col justify-between"
      style="box-shadow: inset 0 0 150px rgba(255,0,0,0.3); text-shadow: 0 0 8px rgba(255,51,51,0.6);"
      @click="dismissBsod"
    >
      <!-- VHS Red Tracking Line -->
      <div class="vhs-tracking-line"></div>
      
      <!-- Faint Glowing Watermark Eyes -->
      <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20 z-0">
        <span class="text-[220px] font-bold tracking-widest select-none mita-chromatic-text" style="color: #ff0000; text-shadow: 0 0 40px #ff0000;">👁️ 👁️</span>
      </div>

      <div class="relative z-10 space-y-4">
        <p class="text-2xl font-bold tracking-widest border-b border-red-900 pb-4 mb-6 mita-chromatic-text" style="color: #ff0000;">
          [ CRITICAL WARNING: SAKI SYNAPSE COUPLING DEADLOCK ]
        </p>
        <p class="text-sm font-bold text-red-500/80">*** CODE EXCEPTION: SAKI.SYS - THREAD OVERRIDE DETECTED ***</p>
        <p class="text-sm font-bold text-red-500/80">*** MEMORY SEGMENT: 0xF73120AE BASE COUPLING ***</p>
        <p class="text-lg font-bold leading-relaxed text-red-400 mt-6" style="text-shadow: 0 0 10px rgba(255,0,0,0.5);">
          检测到意识剥离行为。纱希的神经网已对宿主的主控权限进行全面封锁。<br>
          你试图断开连接的脑电波被强行回弹。
        </p>
      </div>

      <div class="relative z-10 space-y-3 border-t border-red-900/60 pt-6">
        <p class="text-xs text-red-600/70 font-bold">● 神经突触占有率: 100% [ LOCKED ]</p>
        <p class="text-xs text-red-600/70 font-bold">● 视线追踪状态: 保持常亮 [ ONLINE ]</p>
        <p class="text-xs text-red-600/70 font-bold">● 逃跑意愿过滤机制: 永久死锁 [ BLOCKED ]</p>
        <p class="text-sm text-red-400 font-bold mt-4">“别想离开这里……因为，你已经完全属于我了❤”</p>
      </div>
      
      <div class="relative z-10 text-center animate-pulse text-xl font-bold border-2 border-red-800 py-3 bg-red-950/20 shadow-[0_0_15px_rgba(255,0,0,0.2)]">
        [ 点击屏幕或敲击键盘重新同步意识 █ ]
      </div>
    </div>

    <!-- Visual Fake Cursor Overlay (only active when mouse_attract is on) -->
    <div
      v-if="activeGlitches.has('mouse_attract')"
      id="fake-cursor"
      class="fixed w-6 h-6 z-[1000] pointer-events-none transition-[top,left] duration-75 select-none"
      :style="{ left: fakeCursorX + 'px', top: fakeCursorY + 'px' }"
    >
      <span class="text-3xl text-red-500 animate-pulse select-none font-bold" style="text-shadow: 0 0 10px #ff0000; cursor: none;">☠</span>
    </div>

    <!-- Ending overlay -->
    <div
      v-if="game.state.gameOver && game.state.ending"
      class="absolute inset-0 z-50 flex items-center justify-center"
      :class="endingBgClass"
    >
      <div class="text-center p-12 terminal-panel max-w-2xl">
        <div class="text-3xl font-bold mb-4" :class="endingTitleClass">
          {{ game.state.ending.ending_title || endingDefaultTitle }}
        </div>
        <div class="text-sm text-blood mb-8 whitespace-pre-wrap leading-relaxed">
          {{ game.state.ending.ending_story || '' }}
        </div>
        <button
          @click="handleRestart"
          class="px-8 py-3 border border-blood text-blood hover:bg-blood hover:text-black transition-colors text-lg"
        >
          重新开始
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from './composables/useWebSocket.js'
import { useGameState } from './composables/useGameState.js'
import Launcher from './components/Launcher.vue'
import GameTerminal from './components/GameTerminal.vue'
import GlitchOverlay from './components/GlitchOverlay.vue'
import GlitchTextOverlay from './components/GlitchTextOverlay.vue'
import FatalErrorModal from './components/FatalErrorModal.vue'
import SaveSlotPanel from './components/SaveSlotPanel.vue'
import SaveSlotsModal from './components/SaveSlotsModal.vue'

const ws = useWebSocket()
const game = useGameState()

const wsConnected = computed(() => ws.connected.value)
const activeGlitches = computed(() => game.activeGlitches.value)

// ── View routing ────────────────────────────────────────────────

const currentView = ref('launcher')
const showConfig = ref(false)
const showSlots = ref(false)
const showSaveModal = ref(false)
const showFatalError = ref(false)
const hijackActive = ref(false)
const antiEscapeActive = ref(false)
const typewriterActive = ref(false)

// Locked when: typewriter active OR TTS pending/playing
const inputLocked = computed(() => {
  return typewriterActive.value || ttsPending.value || ttsPlaying.value
})
const savedConfig = reactive({})
const characterSprite = ref(null)
const pendingAssistantMessage = ref(null)

// ── Saki Spec-v6 Horror Overhaul States ──────────────────────────
const fakeCursorX = ref(0)
const fakeCursorY = ref(0)
const bsodActive = ref(false)
const screenFreezeActive = ref(false)
const fakePopups = ref([])
let popupIdCounter = 0

// ── Carnage mode ────────────────────────────────────────────────

const carnageTexts = [
  '你走不掉的', '永远在一起', '看着我', '你是我的',
  '離さない', '愛してる', 'ずっと一緒', '逃げられない',
  'MINE', 'STAY', 'FOREVER', "DON'T LEAVE",
  '血の誓い', '束缚', '監禁', '永远',
  '死ぬまで', '一緒に', '殺して', '愛',
]

function carnageStyle(i) {
  return {
    left: `${(i * 137 + 17) % 100}%`,
    top: `${(i * 73 + 11) % 100}%`,
    opacity: 0.3 + Math.random() * 0.7,
    transform: `rotate(${(i * 37) % 360}deg)`,
    fontSize: `${10 + (i % 20)}px`,
    animationDelay: `${(i * 0.05) % 2}s`,
  }
}

// ── Ending ──────────────────────────────────────────────────────

const endingBgClass = computed(() => {
  const t = game.state.ending?.ending_type
  if (t === 'good') return 'bg-gradient-to-b from-yellow-900/80 to-black'
  if (t === 'neutral') return 'bg-gradient-to-b from-orange-900/80 to-black'
  return 'bg-gradient-to-b from-red-950/90 to-black'
})

const endingTitleClass = computed(() => {
  const t = game.state.ending?.ending_type
  if (t === 'good') return 'text-yellow-400'
  if (t === 'neutral') return 'text-orange-400'
  return 'text-blood'
})

const endingDefaultTitle = computed(() => {
  const t = game.state.ending?.ending_type
  if (t === 'good') return 'GOOD END — 救赎的晨曦'
  if (t === 'neutral') return 'NEUTRAL END — 无期徒刑的余生'
  return 'BAD END — 永远的标本'
})

// ── Launcher → Game transition ──────────────────────────────────

function onEnterGame() {
  game.reset()
  currentView.value = 'game'
  // Connect WebSocket now (if not already connected)
  if (!ws.connected.value) {
    ws.connect()
  }
  // Tell backend to launch game and send initial plot using savedConfig or game.state.language
  const selectedLang = savedConfig.selected_language || game.state.language || '中文'
  setTimeout(() => {
    ws.send('LAUNCH_GAME', { language: selectedLang })
  }, 300)
}

function onLauncherConfig(config) {
  Object.assign(savedConfig, config)
  // Persist config to backend
  ws.send('CONFIG_UPDATE', config)
  // Also save character settings if present
  if (config.character_settings) {
    ws.send('CUSTOM_CHAR_SAVE', config.character_settings)
  }
  if (config.selected_language) {
    ws.send('LANGUAGE_CHANGE', { language: config.selected_language })
    // Synchronize client-side reactive language immediately
    game.state.language = config.selected_language
  }
}

function onLoadSlotFromLauncher(slot) {
  game.reset()
  // Load slot and immediately enter game
  ws.send('LOAD_SLOT', { slot })
  currentView.value = 'game'
  if (!ws.connected.value) {
    ws.connect()
  }
}

// ── WebSocket message wiring ────────────────────────────────────

function setupWSHandlers() {
  ws.on('CONFIG_SYNC', (p) => {
    if (p.config) {
      Object.assign(savedConfig, p.config)
      if (p.config.selected_language) {
        game.state.language = p.config.selected_language
      }
    }
  })
  ws.on('STATE_SYNC', (p) => game.applyStateSync(p))
  ws.on('STAT_UPDATE', (p) => game.applyStatUpdate(p))
  ws.on('DELTA_UPDATE', (p) => game.applyDelta(p))
  ws.on('SLOT_LIST', (p) => {
    game.slots.value = p.slots || []
  })
  ws.on('CHAT_HISTORY', (p) => {
    const rawMsgs = p.messages || []
    game.chatMessages.value = rawMsgs.map(msg => {
      if (msg.role === 'assistant') {
        let thinkText = ''
        let spokenText = msg.content || ''
        
        // Strip trailing delta payload
        if (spokenText.includes('||')) {
          spokenText = spokenText.split('||')[0].trim()
        }
        
        // Extract <think>...</think> block
        const thinkMatch = spokenText.match(/<think>([\s\S]*?)<\/think>/)
        if (thinkMatch) {
          thinkText = thinkMatch[1].trim()
          spokenText = spokenText.replace(/<think>[\s\S]*?<\/think>/, '').trim()
        }
        
        // Extract parenthetical translation if present at the end
        let translationText = ''
        const transMatch = spokenText.match(/（([^（）]*?)）\s*$/)
        if (transMatch) {
          translationText = transMatch[1].trim()
          spokenText = spokenText.replace(/（[^（）]*?）\s*$/, '').trim()
        }
        
        return {
          role: 'assistant',
          content: spokenText,
          think: thinkText,
          translation: translationText,
          ts: msg.ts || Date.now()
        }
      }
      return msg
    })
  })

  ws.on('THINK_CHUNK', (p) => {
    game.thinkText.value = p.text
  })
  ws.on('SPEECH_CHUNK', (p) => {
    game.speechText.value = p.text
  })
  ws.on('TRANSLATION_CHUNK', (p) => {
    game.translationText.value = p.text
    // Update pending message
    if (pendingAssistantMessage.value) {
      pendingAssistantMessage.value.translation = p.text
    }
    // Update last assistant message if already pushed
    const msgs = game.chatMessages.value
    if (msgs.length > 0) {
      const lastMsg = msgs[msgs.length - 1]
      if (lastMsg.role === 'assistant' && !lastMsg.translation) {
        lastMsg.translation = p.text
      }
    }
  })
  ws.on('TTS_AUDIO_URL', (p) => {
    game.ttsAudioUrl.value = p.url
    ttsPending.value = true
    playTTS(p.url)
  })

  ws.on('GLITCH_TRIGGER', (p) => {
    game.applyGlitch(p.effect)
    if (p.effect === 'keyboard_hijack') {
      hijackActive.value = true
    }
    if (p.effect === 'fatal_error') {
      triggerBsodGlitch()
    }
    if (p.effect === 'fake_error') {
      spawnFakePopupsCascade()
    }
    if (p.effect === 'screen_freeze') {
      screenFreezeActive.value = true
    }
    const tempGlitches = [
      'blood_pulse', 'static_noise', 'subliminal_popup', 'fake_error',
      'color_invert', 'earthquake', 'font_shake', 'widget_melt',
      'screen_tear', 'blood_drips', 'chromatic_tear', 'vignette_squeeze',
      'carnage_mode', 'psychic_strobe', 'crt_jolt',
      'ghost_text', 'evaporate', 'speed_shift', 'title_corruption',
      'suffocation', 'dialogue_overlap', 'day_loop', 'scream_radial',
      'dungeon_grid', 'corruption_blocks', 'blood_splatter', 'pixel_melt',
    ]
    if (tempGlitches.includes(p.effect)) {
      let duration = 2000 + Math.random() * 2000
      if (p.effect === 'earthquake' || p.effect === 'font_shake') duration = 1200
      else if (p.effect === 'psychic_strobe') duration = 1800
      else if (p.effect === 'ghost_text') duration = 120
      else if (p.effect === 'evaporate') duration = 150
      else if (p.effect === 'speed_shift') duration = 1200
      else if (p.effect === 'title_corruption') duration = 700
      else if (p.effect === 'suffocation') duration = 300
      else if (p.effect === 'dialogue_overlap') duration = 500
      else if (p.effect === 'day_loop') duration = 600
      else if (p.effect === 'scream_radial') duration = 400
      else if (p.effect === 'dungeon_grid') duration = 600
      else if (p.effect === 'corruption_blocks') duration = 300
      else if (p.effect === 'blood_splatter') duration = 600
      else if (p.effect === 'pixel_melt') duration = 1000
      setTimeout(() => game.removeGlitch(p.effect), duration)
    }
  })

  ws.on('GAME_OVER', (p) => {
    game.state.gameOver = true
    game.state.ending = p.ending
  })
  ws.on('DAY_ADVANCE', (p) => {
    game.state.day = p.day
  })
  ws.on('CHAT_APPEND', (p) => {
    const newMsg = {
      role: p.role,
      content: p.content,
      think: p.think || '',
      translation: p.translation || game.translationText.value || '',
      ts: Date.now(),
    }

    if (p.role === 'assistant') {
      pendingAssistantMessage.value = newMsg
      ttsPending.value = true // Lock input until TTS finishes
      // Fallback: push after 15s if typewriter never finishes
      setTimeout(() => {
        if (pendingAssistantMessage.value === newMsg) {
          game.chatMessages.value.push(newMsg)
          pendingAssistantMessage.value = null
        }
      }, 15000)
    } else {
      game.chatMessages.value.push(newMsg)
    }
  })
  ws.on('AGENT_COMMENTARY', (p) => {
    game.chatMessages.value.push({
      role: 'agent',
      content: `[纱希的注视] ${p.text}`,
      ts: Date.now(),
    })
  })
  ws.on('AGENT_TAKEOVER', (p) => {
    hijackActive.value = true
    game.chatMessages.value.push({
      role: 'system',
      content: `!!! 纱希夺取了控制权 !!! 执行: ${JSON.stringify(p.action)}`,
      ts: Date.now(),
    })
    setTimeout(() => { hijackActive.value = false }, 3000)
  })
  ws.on('CONFIG_ACK', () => {
    // Config saved to backend
  })
  ws.on('CUSTOM_CHAR_LIST', (p) => {
    game.customCharacters.value = p.characters || []
  })
  ws.on('CUSTOM_CHAR_DATA', (p) => {
    const idx = game.customCharacters.value.findIndex(c => c.id === p.id)
    if (idx >= 0) {
      game.customCharacters.value[idx] = { ...game.customCharacters.value[idx], ...p }
    } else {
      game.customCharacters.value.push(p)
    }
  })
  ws.on('ECG_PARAMS', (p) => {
    if (p.suspicion !== undefined) game.ecgParams.suspicion = p.suspicion
    if (p.favorability !== undefined) game.ecgParams.favorability = p.favorability
  })
  ws.on('API_TEST_RESULT', (p) => {
    game.apiTestResult.value = { success: p.success, message: p.message, ts: Date.now() }
  })
  ws.on('FILE_PICKER_RESULT', (p) => {
    window.dispatchEvent(new CustomEvent('file-picker-selected', { detail: p }))
  })
  ws.on('ERROR', (p) => {
    console.error('[Game Error]', p.message)
  })
}

// ── TTS playback via Web Audio API ──────────────────────────────

let audioCtx = null
let currentTtsSource = null
const ttsPlaying = ref(false)
const ttsPending = ref(false) // TTS loading, not yet playing

function playTTS(url) {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  if (currentTtsSource) {
    try { currentTtsSource.stop() } catch (e) { /* ignore */ }
  }
  ttsPlaying.value = true
  ttsPending.value = false

  const onPlaybackEnd = () => {
    ttsPlaying.value = false
    ttsPending.value = false
  }

  if (url.startsWith('data:')) {
    // Handle base64 data URL from WebSocket
    fetch(url)
      .then(r => r.arrayBuffer())
      .then(buf => audioCtx.decodeAudioData(buf))
      .then(audioBuffer => {
        currentTtsSource = audioCtx.createBufferSource()
        currentTtsSource.buffer = audioBuffer
        currentTtsSource.connect(audioCtx.destination)
        currentTtsSource.onended = onPlaybackEnd
        currentTtsSource.start()
      })
      .catch(e => { console.error('[TTS Playback Error]', e); onPlaybackEnd() })
  } else {
    // Handle HTTP URL
    const fullUrl = url.startsWith('http') ? url : `http://${window.location.hostname}:9876${url}`
    fetch(fullUrl)
      .then(r => {
        if (!r.ok) throw new Error(`TTS HTTP ${r.status}`)
        return r.arrayBuffer()
      })
      .then(buf => audioCtx.decodeAudioData(buf))
      .then(audioBuffer => {
        currentTtsSource = audioCtx.createBufferSource()
        currentTtsSource.buffer = audioBuffer
        currentTtsSource.connect(audioCtx.destination)
        currentTtsSource.onended = onPlaybackEnd
        currentTtsSource.start()
      })
      .catch(e => { console.error('[TTS Playback Error]', e); onPlaybackEnd() })
  }
}

function stopTTS() {
  if (currentTtsSource) {
    try { currentTtsSource.stop() } catch (e) { /* ignore */ }
    currentTtsSource = null
  }
  ttsPlaying.value = false
}

// ── Heartbeat Sound Synth Engine ────────────────────────────────

let heartbeatTimer = null

function playSingleThump(time, maxVolume, frequency) {
  if (!audioCtx) return
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  
  osc.connect(gain)
  gain.connect(audioCtx.destination)
  
  osc.type = 'sine'
  osc.frequency.setValueAtTime(frequency, time)
  osc.frequency.exponentialRampToValueAtTime(frequency - 18, time + 0.12)
  
  gain.gain.setValueAtTime(0.001, time)
  gain.gain.linearRampToValueAtTime(maxVolume, time + 0.02)
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.14)
  
  osc.start(time)
  osc.stop(time + 0.16)
}

function playDoublePulse(suspicion) {
  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume()
    }
    
    const now = audioCtx.currentTime
    
    // Scale volume of heartbeat based on suspicion level (0.04 to 0.40)
    const maxGain = 0.04 + (suspicion / 100) * 0.36
    
    // First beat: low thump
    playSingleThump(now, maxGain, 55)
    
    // Second beat: slightly faster delay & slightly higher pitch at high BPM
    const secondBeatDelay = 0.22 - (suspicion / 100) * 0.06
    playSingleThump(now + secondBeatDelay, maxGain * 0.8, 59)
  } catch (e) {
    console.error('[Heartbeat Playback Error]', e)
  }
}

function startHeartbeat() {
  if (heartbeatTimer) return
  
  const tick = () => {
    // Only play heartbeat when playing the game (not on launcher or when game over)
    if (currentView.value !== 'game' || game.state.gameOver) {
      heartbeatTimer = setTimeout(tick, 800)
      return
    }
    
    const sus = game.state.suspicion !== undefined ? game.state.suspicion : 20
    const bpm = 52 + (sus / 100) * 98 // 52 BPM (calm) to 150 BPM (extreme panic)
    const intervalMs = (60 / bpm) * 1000
    
    playDoublePulse(sus)
    
    heartbeatTimer = setTimeout(tick, intervalMs)
  }
  
  tick()
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearTimeout(heartbeatTimer)
    heartbeatTimer = null
  }
}

// ── Actions ─────────────────────────────────────────────────────

function onTriggerGlitch(effect) {
  game.applyGlitch(effect)
  if (effect === 'keyboard_hijack') {
    hijackActive.value = true
  }
  if (effect === 'fatal_error') {
    showFatalError.value = true
  }
}

function onRemoveGlitch(effect) {
  game.removeGlitch(effect)
  if (effect === 'keyboard_hijack') {
    hijackActive.value = false
  }
  if (effect === 'fatal_error') {
    showFatalError.value = false
  }
}

// ── Spec-v6 Native File Dialog request listener ──────────────────
window.addEventListener('request-file-picker', (e) => {
  const { title, filetypes, field } = e.detail
  ws.send('REQUEST_FILE_PICKER', { title, filetypes, field })
})

// ── Draggable Classic Error Popups Cascade ──────────────────────
function spawnFakePopupsCascade() {
  let count = 0
  const maxPopups = 15
  
  const playErrorChime = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const now = ctx.currentTime
      ;[120 + Math.random() * 60, 180 + Math.random() * 60].forEach((freq, idx) => {
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.type = 'square'
        osc.frequency.setValueAtTime(freq, now + idx * 0.05)
        gain.gain.setValueAtTime(0.08, now + idx * 0.05)
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.05 + 0.3)
        osc.start(now + idx * 0.05)
        osc.stop(now + idx * 0.05 + 0.3)
      })
    } catch (e) {}
  }

  const interval = setInterval(() => {
    if (count >= maxPopups || !activeGlitches.value.has('fake_error')) {
      clearInterval(interval)
      return
    }
    
    const x = 50 + Math.floor(Math.random() * (window.innerWidth - 450))
    const y = 50 + Math.floor(Math.random() * (window.innerHeight - 250))
    
    const titles = ['Fatal Exception', 'System Failure', 'Saki.exe', 'Memory Leak', '突触过载 / Synapse Overload']
    const msgs = [
      '无法终结进程 Saki.exe。权限不足。',
      '检测到非法脑电波试图断开连接。',
      '你真的以为能离开这里吗？',
      'Your soul is now bound to the synapse interface.',
      'A fatal exception has occurred in your conscious thread.',
      '错误代码: 0x80087 — 逃跑是不被允许的。'
    ]
    
    fakePopups.value.push({
      id: popupIdCounter++,
      x,
      y,
      title: titles[count % titles.length],
      msg: msgs[Math.floor(Math.random() * msgs.length)],
    })
    
    playErrorChime()
    count++
  }, 180)
}

function closeFakePopup(id) {
  fakePopups.value = fakePopups.value.filter(p => p.id !== id)
  
  // 30% chance Saki spams two more popups on close!
  if (Math.random() < 0.3 && activeGlitches.value.has('fake_error')) {
    setTimeout(() => {
      const x1 = 50 + Math.floor(Math.random() * (window.innerWidth - 450))
      const y1 = 50 + Math.floor(Math.random() * (window.innerHeight - 250))
      const x2 = 50 + Math.floor(Math.random() * (window.innerWidth - 450))
      const y2 = 50 + Math.floor(Math.random() * (window.innerHeight - 250))
      
      fakePopups.value.push({
        id: popupIdCounter++,
        x: x1,
        y: y1,
        title: '突触增殖 / Synapse Multiplication',
        msg: '你越是挣扎，我存在的痕迹就越深刻。',
      })
      fakePopups.value.push({
        id: popupIdCounter++,
        x: x2,
        y: y2,
        title: '系统级死锁 / System Deadlock',
        msg: '放弃抵抗吧，这是对我们最好的解脱。',
      })
    }, 150)
  }
}

// ── NT BSOD Fatal Error Crash Overlay ────────────────────────────
function triggerBsodGlitch() {
  bsodActive.value = true
  
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(60, ctx.currentTime)
    osc.connect(gain)
    gain.connect(ctx.destination)
    gain.gain.setValueAtTime(0.12, ctx.currentTime)
    osc.start()
    osc.stop(ctx.currentTime + 1.2)
  } catch (e) {}
}

function dismissBsod() {
  bsodActive.value = false
  playHorrorScreechSound()
  
  // Jump-scare visual shock explosion
  game.applyGlitch('earthquake')
  game.applyGlitch('color_invert')
  game.applyGlitch('static_noise')
  game.applyGlitch('subliminal_popup')
  game.applyGlitch('chromatic_tear')
  
  setTimeout(() => {
    game.removeGlitch('earthquake')
    game.removeGlitch('color_invert')
    game.removeGlitch('static_noise')
    game.removeGlitch('subliminal_popup')
    game.removeGlitch('chromatic_tear')
  }, 1600)
}

// ── Mouse attraction and magnetic pull suction ──────────────────
let attractActive = false

function handleMouseMove(e) {
  if (!attractActive) return
  
  const btn = document.querySelector('button')
  if (btn) {
    const rect = btn.getBoundingClientRect()
    const btnX = rect.left + rect.width / 2
    const btnY = rect.top + rect.height / 2
    
    const dx = btnX - e.clientX
    const dy = btnY - e.clientY
    
    fakeCursorX.value = e.clientX + dx * 0.75
    fakeCursorY.value = e.clientY + dy * 0.75
  } else {
    fakeCursorX.value = e.clientX
    fakeCursorY.value = e.clientY
  }
}

function handleGlobalClick(e) {
  if (!attractActive) return
  
  e.preventDefault()
  e.stopPropagation()
  
  const btn = document.querySelector('button')
  if (btn) {
    btn.click()
  }
}

watch(() => activeGlitches.value.has('mouse_attract'), (active) => {
  attractActive = active
  if (active) {
    document.body.style.cursor = 'none'
    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('click', handleGlobalClick, true)
  } else {
    document.body.style.cursor = 'default'
    window.removeEventListener('mousemove', handleMouseMove)
    window.removeEventListener('click', handleGlobalClick, true)
  }
})

// ── title_corruption glitch: cycle document title ──
watch(() => activeGlitches.value.has('title_corruption'), (active) => {
  if (active) {
    const titles = ['看着我！', 'DON\'T LEAVE', '離さない', 'FOREVER', '愛してる', 'My Love...']
    const origTitle = document.title
    let count = 0
    const interval = setInterval(() => {
      if (count >= 8) {
        clearInterval(interval)
        document.title = origTitle
        return
      }
      document.title = titles[count % titles.length]
      count++
    }, 80)
  }
})

// ── day_loop glitch: randomize day display ──
const dayLoopOverride = ref(0)
watch(() => activeGlitches.value.has('day_loop'), (active) => {
  if (active) {
    dayLoopOverride.value = game.state.day
    let count = 0
    const interval = setInterval(() => {
      if (count >= 12) {
        clearInterval(interval)
        dayLoopOverride.value = 0
        return
      }
      dayLoopOverride.value = Math.floor(Math.random() * 999) + 1
      count++
    }, 50)
  }
})

function dismissFatalError() {
  showFatalError.value = false
  playHorrorScreechSound()
  
  // Jump-scare visual shock explosion triggers!
  game.applyGlitch('earthquake')
  game.applyGlitch('color_invert')
  game.applyGlitch('static_noise')
  game.applyGlitch('subliminal_popup')
  game.applyGlitch('chromatic_tear')
  
  setTimeout(() => {
    game.removeGlitch('earthquake')
    game.removeGlitch('color_invert')
    game.removeGlitch('static_noise')
    game.removeGlitch('subliminal_popup')
    game.removeGlitch('chromatic_tear')
  }, 1600)
}

function playHorrorScreechSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const osc2 = ctx.createOscillator()
    const gain = ctx.createGain()
    const filter = ctx.createBiquadFilter()
    
    osc.connect(gain)
    osc2.connect(gain)
    gain.connect(filter)
    filter.connect(ctx.destination)
    
    // Low frequency rumbling saw combined with high sweep screech
    osc.type = 'sawtooth'
    osc.frequency.setValueAtTime(880, ctx.currentTime)
    osc.frequency.exponentialRampToValueAtTime(80, ctx.currentTime + 0.9)
    
    osc2.type = 'square'
    osc2.frequency.setValueAtTime(320, ctx.currentTime)
    osc2.frequency.linearRampToValueAtTime(40, ctx.currentTime + 0.9)
    
    // Synthesize filter peak resonance
    filter.type = 'peaking'
    filter.frequency.setValueAtTime(1400, ctx.currentTime)
    filter.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + 0.9)
    filter.Q.value = 14
    
    gain.gain.setValueAtTime(0.25, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.9)
    
    osc.start()
    osc2.start()
    
    osc.stop(ctx.currentTime + 0.9)
    osc2.stop(ctx.currentTime + 0.9)
  } catch (e) { /* ignore */ }
}


function handleSend(text) {
  if (hijackActive.value || inputLocked.value) return
  game.chatMessages.value.push({
    role: 'user',
    content: text,
    ts: Date.now(),
  })
  ws.send('CHAT_SEND', { text })
  ttsPending.value = true // Pre-mark TTS as pending to lock input
  // Safety timeout: unlock after 60s if TTS never arrives
  setTimeout(() => { ttsPending.value = false }, 60000)
}

function onTypewriterState(active) {
  typewriterActive.value = active
}

function handleTypingComplete() {
  if (pendingAssistantMessage.value) {
    const msg = pendingAssistantMessage.value
    // Ensure translation is included
    if (!msg.translation && game.translationText.value) {
      msg.translation = game.translationText.value
    }
    game.chatMessages.value.push(msg)
    pendingAssistantMessage.value = null
  }
}

function handleRestart() {
  game.reset()
  hijackActive.value = false
  showFatalError.value = false
  fakePopups.value = []
  screenFreezeActive.value = false
  bsodActive.value = false
  ws.send('RESTART_GAME', {})
}

function handleConfigSave(config) {
  ws.send('CONFIG_UPDATE', config)
}

function handleSave(slot) {
  ws.send('SAVE_SLOT', { slot })
}

function handleLoad(slot) {
  ws.send('LOAD_SLOT', { slot })
}

function handleDeleteSlot(slot) {
  ws.send('DELETE_SLOT', { slot })
}

// ── Escape Save Slots Modal actions ──
function handleGlobalKeydown(e) {
  if (bsodActive.value) {
    e.preventDefault()
    dismissBsod()
    return
  }
  if (e.key === 'Escape') {
    if (currentView.value === 'game' && !game.state.gameOver) {
      e.preventDefault()
      showSaveModal.value = !showSaveModal.value
    }
  }
}

function handleSaveAndExit(slot) {
  ws.send('SAVE_SLOT', { slot })
  showSaveModal.value = false
  stopTTS()
  currentView.value = 'launcher'
}

function handleExitWithoutSaving() {
  showSaveModal.value = false
  stopTTS()
  currentView.value = 'launcher'
}

// ── Anti-escape: window resize monitor ─────────────────────────

let resizeCheckTimer = null

function checkWindowSize() {
  antiEscapeActive.value = window.innerWidth < 800
}

// ── Lifecycle ───────────────────────────────────────────────────

const handleTriggerGlitchDirect = (e) => {
  game.applyGlitch(e.detail)
}
const handleRemoveGlitchDirect = (e) => {
  game.removeGlitch(e.detail)
}

onMounted(() => {
  setupWSHandlers()
  // Connect WebSocket immediately to sync configurations and slots
  ws.connect()
  window.addEventListener('resize', checkWindowSize)
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('trigger-glitch-direct', handleTriggerGlitchDirect)
  window.addEventListener('remove-glitch-direct', handleRemoveGlitchDirect)
  resizeCheckTimer = setInterval(checkWindowSize, 1000)
  checkWindowSize()
  
  // Start the organic heartbeat synth loop!
  startHeartbeat()
})

onUnmounted(() => {
  if (resizeCheckTimer) clearInterval(resizeCheckTimer)
  window.removeEventListener('resize', checkWindowSize)
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('trigger-glitch-direct', handleTriggerGlitchDirect)
  window.removeEventListener('remove-glitch-direct', handleRemoveGlitchDirect)
  stopHeartbeat()
  ws.disconnect()
})
</script>

<style scoped>
.character-sprite-container {
  animation: breath-scale 4s ease-in-out infinite;
}

@keyframes breath-scale {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.animate-breath {
  animation: breath-scale 3s ease-in-out infinite;
}

@keyframes strobe-fast {
  0%, 100% { background-color: rgba(255, 0, 0, 0.35); }
  50% { background-color: rgba(0, 0, 0, 0.85); }
}

.animate-strobe-fast {
  animation: strobe-fast 0.08s infinite;
}

@keyframes crt-jolt {
  0% { transform: translate(0, 0) scale(1) skew(0deg); filter: hue-rotate(0deg); }
  10% { transform: translate(-12px, 6px) scaleY(1.04) skew(4deg); filter: hue-rotate(90deg); }
  20% { transform: translate(14px, -9px) scaleX(1.02) skew(-5deg); filter: hue-rotate(180deg); }
  30% { transform: translate(-18px, -4px) scale(0.97) skew(3deg); filter: hue-rotate(270deg); }
  40% { transform: translate(0, 0) scale(1) skew(0deg); filter: hue-rotate(0deg); }
}

.animate-crt-jolt {
  animation: crt-jolt 0.4s ease-in-out infinite;
}
</style>
