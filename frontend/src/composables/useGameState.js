/**
 * Reactive game state — mirrors the backend GameState values.
 * Updated via WebSocket STATE_SYNC / STAT_UPDATE / DELTA_UPDATE messages.
 */
import { reactive, ref, computed } from 'vue'

export function useGameState() {
  const state = reactive({
    day: 1,
    favorability: 50,
    suspicion: 20,
    escapeRate: 0,
    language: '中文',
    charId: 'saki',
    gameOver: false,
    ending: null,
    systemUsername: '玩家',
  })

  const chatMessages = ref([])
  const thinkText = ref('')
  const speechText = ref('')
  const translationText = ref('')
  const ttsAudioUrl = ref(null)

  // Save slots
  const slots = ref([])

  // Custom characters from backend
  const customCharacters = ref([])

  // API test result from backend
  const apiTestResult = ref(null)

  // Glitch effects active set
  const activeGlitches = ref(new Set())

  // ECG params
  const ecgParams = reactive({
    suspicion: 20,
    favorability: 50,
  })

  // Typewriter state
  const typewriterActive = ref(false)
  const typewriterTarget = ref('')
  const typewriterDisplay = ref('')
  const typewriterMode = ref('think') // 'think' | 'speech' | 'translation'

  // ── computed ──────────────────────────────────────────────────

  const suspicionLevel = computed(() => {
    const s = state.suspicion
    if (s >= 85) return 'carnage'
    if (s >= 75) return 'severe'
    if (s >= 55) return 'moderate'
    if (s >= 35) return 'mild'
    return 'normal'
  })

  const glitchIntensity = computed(() => {
    const s = state.suspicion
    if (s >= 85) return 3
    if (s >= 55) return 2
    if (s >= 35) return 1
    return 0
  })

  // ── actions ───────────────────────────────────────────────────

  function applyStateSync(payload) {
    if (payload.day !== undefined) state.day = payload.day
    if (payload.favorability !== undefined) state.favorability = payload.favorability
    if (payload.suspicion !== undefined) state.suspicion = payload.suspicion
    if (payload.escape_rate !== undefined) state.escapeRate = payload.escape_rate
    if (payload.language) state.language = payload.language
    if (payload.char_id) state.charId = payload.char_id
    if (payload.game_over !== undefined) state.gameOver = payload.game_over
    if (payload.system_username) state.systemUsername = payload.system_username
    ecgParams.suspicion = state.suspicion
    ecgParams.favorability = state.favorability
  }

  function applyStatUpdate(payload) {
    if (payload.favorability !== undefined) state.favorability = payload.favorability
    if (payload.suspicion !== undefined) state.suspicion = payload.suspicion
    if (payload.escape_rate !== undefined) state.escapeRate = payload.escape_rate
    ecgParams.suspicion = state.suspicion
    ecgParams.favorability = state.favorability
  }

  function applyDelta(payload) {
    if (payload.favorability !== undefined) state.favorability += payload.favorability
    if (payload.suspicion !== undefined) state.suspicion += payload.suspicion
    if (payload.escape_rate !== undefined) state.escapeRate += payload.escape_rate
    // Clamp to valid ranges
    state.favorability = Math.max(-25, Math.min(100, state.favorability))
    state.suspicion = Math.max(0, Math.min(100, state.suspicion))
    state.escapeRate = Math.max(0, Math.min(100, state.escapeRate))
    ecgParams.suspicion = state.suspicion
    ecgParams.favorability = state.favorability
  }

  function applyGlitch(effect) {
    activeGlitches.value.add(effect)
  }

  function removeGlitch(effect) {
    activeGlitches.value.delete(effect)
  }

  function reset() {
    state.day = 1
    state.favorability = 50
    state.suspicion = 20
    state.escapeRate = 0
    state.gameOver = false
    state.ending = null
    chatMessages.value = []
    thinkText.value = ''
    speechText.value = ''
    translationText.value = ''
    activeGlitches.value = new Set()
    ecgParams.suspicion = 20
    ecgParams.favorability = 50
  }

  return {
    state,
    chatMessages,
    thinkText,
    speechText,
    translationText,
    ttsAudioUrl,
    slots,
    customCharacters,
    apiTestResult,
    activeGlitches,
    ecgParams,
    typewriterActive,
    typewriterTarget,
    typewriterDisplay,
    typewriterMode,
    suspicionLevel,
    glitchIntensity,
    applyStateSync,
    applyStatUpdate,
    applyDelta,
    applyGlitch,
    removeGlitch,
    reset,
  }
}
