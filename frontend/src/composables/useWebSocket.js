/**
 * WebSocket composable — manages the /ws/game connection lifecycle,
 * auto-reconnect, message dispatch, and send helpers.
 */
import { ref, reactive, onUnmounted } from 'vue'

const WS_URL = `ws://${window.location.hostname}:9876/ws/game`

export function useWebSocket() {
  const connected = ref(false)
  const error = ref(null)
  const latency = ref(0)

  let ws = null
  let reconnectTimer = null
  let pingTimer = null
  let pingSent = 0

  // Message handlers registered by components
  const handlers = reactive({})

  function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }

    try {
      ws = new WebSocket(WS_URL)
    } catch (e) {
      error.value = 'Failed to create WebSocket'
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      connected.value = true
      error.value = null
      startPing()
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        const type = msg.type
        const payload = msg.payload || {}

        // PONG handler
        if (type === 'PONG') {
          latency.value = Date.now() - pingSent
          return
        }

        // Dispatch to registered handler
        if (handlers[type]) {
          handlers[type](payload)
        }

        // Wildcard handler
        if (handlers['*']) {
          handlers['*'](type, payload)
        }
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    ws.onclose = () => {
      connected.value = false
      stopPing()
      scheduleReconnect()
    }

    ws.onerror = (e) => {
      error.value = 'WebSocket error'
      console.error('[WS] Error:', e)
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    stopPing()
    if (ws) {
      ws.close()
      ws = null
    }
    connected.value = false
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, 2000)
  }

  function startPing() {
    stopPing()
    pingTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        pingSent = Date.now()
        send('PING', {})
      }
    }, 10000)
  }

  function stopPing() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function send(type, payload = {}) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type, payload, ts: Date.now() }))
    }
  }

  function on(messageType, callback) {
    handlers[messageType] = callback
  }

  function off(messageType) {
    delete handlers[messageType]
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    error,
    latency,
    connect,
    disconnect,
    send,
    on,
    off,
  }
}
