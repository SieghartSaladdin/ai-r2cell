<template>
  <div class="flex-1 flex flex-col h-[calc(100vh-64px)] lg:h-[calc(100vh-80px)] overflow-hidden bg-zinc-50 dark:bg-zinc-950 text-zinc-800 dark:text-zinc-100 font-sans transition-colors duration-250">
    <!-- View Header -->
    <div class="h-16 lg:h-20 border-b border-zinc-200 dark:border-zinc-900 px-6 lg:px-10 flex items-center justify-between shrink-0 bg-white dark:bg-zinc-950/50">
      <div class="flex items-center gap-3">
        <div class="p-2.5 bg-emerald-500/10 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-2xl">
          <Smartphone class="w-5 h-5 lg:w-6 lg:h-6" />
        </div>
        <div>
          <h1 class="text-base lg:text-lg font-bold tracking-wide">WhatsApp Gateway</h1>
          <p class="text-[10px] lg:text-xs text-zinc-400 dark:text-zinc-500">Manage your WhatsApp bot link session and service logs</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <!-- Live status badge -->
        <span 
          class="px-3 py-1 lg:py-1.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-1.5 shadow-sm border border-zinc-200/50 dark:border-zinc-800"
          :class="statusClasses"
        >
          <span class="h-2 w-2 rounded-full" :class="statusDotClass"></span>
          {{ displayState }}
        </span>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 p-4 lg:p-8 overflow-y-auto space-y-6 lg:space-y-0 lg:grid lg:grid-cols-12 lg:gap-8 lg:overflow-hidden h-full">
      
      <!-- Left Column: Status, Scan QR, Details -->
      <div class="lg:col-span-5 lg:flex lg:flex-col lg:h-full lg:overflow-y-auto space-y-6 scrollbar-hide">
        
        <!-- Connection Card -->
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 shadow-sm flex flex-col items-center text-center relative overflow-hidden transition-all duration-300">
          <div class="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-400"></div>

          <!-- Connecting State Loader -->
          <div v-if="state === 'CONNECTING'" class="my-6 flex flex-col items-center gap-4">
            <div class="w-48 h-48 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-150 dark:border-zinc-800 flex items-center justify-center relative">
              <div class="w-12 h-12 border-4 border-emerald-500/10 border-t-emerald-500 rounded-full animate-spin"></div>
            </div>
            <div>
              <h3 class="text-sm font-bold">Initializing session...</h3>
              <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1">Starting the WhatsApp gateway service</p>
            </div>
          </div>

          <!-- Need Scan State (QR Code) -->
          <div v-else-if="needScan && qr_base64" class="my-4 flex flex-col items-center gap-4">
            <div class="bg-zinc-50 dark:bg-zinc-950 p-4 border border-zinc-200/60 dark:border-zinc-800 rounded-2xl shadow-inner relative group">
              <img :src="qr_base64" alt="Scan QR Code" class="w-48 h-48 rounded-xl object-contain block bg-white p-1" />
              <!-- Hover Overlay for QR Expiration Timer -->
              <div class="absolute bottom-2 right-2 bg-zinc-900/80 backdrop-blur text-white font-mono text-[9px] px-2 py-0.5 rounded-full">
                Refresh in: {{ countdown }}s
              </div>
            </div>
            <div class="px-4">
              <h3 class="text-sm font-bold text-zinc-800 dark:text-zinc-100">Link Device Required</h3>
              <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1.5 max-w-xs leading-relaxed">
                Open WhatsApp on your phone, navigate to <b>Linked Devices</b>, and scan the QR code to connect.
              </p>
            </div>
          </div>

          <!-- Connected State -->
          <div v-else-if="state === 'CONNECTED' || state === 'AUTHENTICATED'" class="my-6 flex flex-col items-center gap-4">
            <div class="w-48 h-48 rounded-2xl bg-emerald-50/40 dark:bg-emerald-950/10 border border-emerald-100 dark:border-emerald-900/30 flex flex-col items-center justify-center gap-3">
              <div class="p-3.5 bg-emerald-500 dark:bg-emerald-600 text-white rounded-full shadow-lg shadow-emerald-500/20 animate-bounce">
                <Check class="w-8 h-8" />
              </div>
              <span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 font-mono tracking-wider">{{ cleanJid(phone) }}</span>
            </div>
            <div>
              <h3 class="text-sm font-bold text-zinc-800 dark:text-zinc-100">Gateway is Connected</h3>
              <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1">Ready to receive and respond to WhatsApp messages</p>
            </div>
          </div>

          <!-- Disconnected / Error State -->
          <div v-else class="my-6 flex flex-col items-center gap-4">
            <div class="w-48 h-48 rounded-2xl bg-red-50/40 dark:bg-red-950/10 border border-red-100 dark:border-red-900/30 flex flex-col items-center justify-center gap-3">
              <div class="p-3.5 bg-red-500 dark:bg-red-600 text-white rounded-full shadow-lg shadow-red-500/20">
                <AlertCircle class="w-8 h-8" />
              </div>
              <span class="text-xs font-bold text-red-600 dark:text-red-400">OFFLINE</span>
            </div>
            <div class="px-4">
              <h3 class="text-sm font-bold text-zinc-800 dark:text-zinc-100">Gateway Offline</h3>
              <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-1 max-w-xs leading-relaxed">
                {{ error || 'WhatsApp integration process is not running.' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Details & Session Controls Card -->
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-6 shadow-sm flex flex-col gap-5 transition-all duration-300">
          <h2 class="text-xs font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest flex items-center gap-2">
            <Activity class="w-4.5 h-4.5" />
            Gateway Statistics
          </h2>
          
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-zinc-50 dark:bg-zinc-950 border border-zinc-150 dark:border-zinc-900 p-4 rounded-2xl flex flex-col gap-0.5">
              <span class="text-[9px] text-zinc-400 dark:text-zinc-500 font-bold uppercase tracking-wider">Gateway Uptime</span>
              <span class="text-sm font-extrabold text-zinc-800 dark:text-zinc-100 font-mono mt-1">{{ formattedUptime }}</span>
            </div>
            <div class="bg-zinc-50 dark:bg-zinc-950 border border-zinc-150 dark:border-zinc-900 p-4 rounded-2xl flex flex-col gap-0.5">
              <span class="text-[9px] text-zinc-400 dark:text-zinc-500 font-bold uppercase tracking-wider">Messages Checked</span>
              <span class="text-sm font-extrabold text-zinc-800 dark:text-zinc-100 font-mono mt-1">{{ message_count }}</span>
            </div>
          </div>

          <div class="w-full h-px bg-zinc-150 dark:bg-zinc-800"></div>

          <!-- Session control actions -->
          <div class="flex flex-col gap-3">
            <button 
              @click="resetSession"
              :disabled="isResetting"
              class="w-full flex items-center justify-center gap-2 py-3 bg-red-500 hover:bg-red-600 disabled:bg-zinc-400 dark:disabled:bg-zinc-800 text-white rounded-xl text-xs font-bold shadow-md hover:shadow-lg disabled:shadow-none active:scale-98 transition-all cursor-pointer"
            >
              <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isResetting }" />
              {{ isResetting ? 'Resetting Session...' : 'Reset Session / Logout' }}
            </button>
            <p class="text-[9px] text-center text-zinc-400 dark:text-zinc-500 leading-relaxed">
              Resetting will terminate the active WhatsApp process, delete all session authentication files, and request a fresh login scan.
            </p>
          </div>
        </div>
      </div>

      <!-- Right Column: Live Logs Terminal -->
      <div class="lg:col-span-7 lg:flex lg:flex-col lg:h-full overflow-hidden">
        <div class="bg-zinc-950 border border-zinc-900 rounded-3xl flex-1 flex flex-col overflow-hidden shadow-2xl relative">
          <!-- Terminal Header -->
          <div class="h-12 border-b border-zinc-900 px-5 flex items-center justify-between bg-zinc-950 shrink-0">
            <div class="flex items-center gap-2">
              <!-- Window dots -->
              <span class="h-3 w-3 rounded-full bg-red-500/80"></span>
              <span class="h-3 w-3 rounded-full bg-amber-500/80"></span>
              <span class="h-3 w-3 rounded-full bg-emerald-500/80"></span>
              <span class="text-[10px] font-mono text-zinc-500 ml-2 uppercase tracking-widest font-bold">whatsapp-gateway-stream</span>
            </div>
            <button 
              @click="clearTerminal" 
              class="p-1 rounded hover:bg-zinc-900 text-zinc-500 hover:text-zinc-300 transition-colors text-[9px] font-mono font-bold uppercase tracking-wider cursor-pointer"
              title="Clear Logs Screen"
            >
              Clear
            </button>
          </div>
          <!-- Terminal Body -->
          <div 
            ref="terminalBody"
            class="flex-1 p-5 overflow-y-auto font-mono text-[10px] lg:text-xs text-zinc-300 leading-relaxed scrollbar-hide space-y-1 selection:bg-zinc-800 selection:text-white"
          >
            <div v-for="(log, idx) in logs" :key="idx" class="whitespace-pre-wrap word-break-all">
              <span class="text-zinc-600 mr-2">[{{ idx + 1 }}]</span>{{ log }}
            </div>
            <div v-if="logs.length === 0" class="text-zinc-600 italic py-12 text-center">
              Awaiting connection to WhatsApp gateway log stream...
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import { 
  Smartphone, 
  Check, 
  AlertCircle, 
  Activity, 
  RefreshCw 
} from 'lucide-vue-next'

const state = ref('DISCONNECTED')
const qr_base64 = ref('')
const uptime = ref(0)
const message_count = ref(0)
const error = ref('')
const logs = ref([])
const isResetting = ref(false)
const countdown = ref(60)

let pollInterval = null
let countdownInterval = null
let logsSource = null
const terminalBody = ref(null)

const cleanJid = (jid) => {
  if (!jid) return ''
  return jid.split('@')[0]
}

const needScan = computed(() => {
  const upper = state.value.toUpperCase()
  return upper === 'QR_PENDING' || upper === 'NEED SCAN' || upper === 'NEED_SCAN'
})

const displayState = computed(() => {
  const s = state.value.toUpperCase()
  if (s === 'AUTHENTICATED' || s === 'CONNECTED') return 'Online'
  if (s === 'QR_PENDING' || s === 'NEED SCAN' || s === 'NEED_SCAN') return 'Scanning Required'
  if (s === 'CONNECTING') return 'Connecting'
  return 'Offline'
})

const statusClasses = computed(() => {
  const s = state.value.toUpperCase()
  if (s === 'AUTHENTICATED' || s === 'CONNECTED') {
    return 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/20 dark:text-emerald-400 border-emerald-200/50 dark:border-emerald-900/50'
  }
  if (s === 'QR_PENDING' || s === 'NEED SCAN' || s === 'NEED_SCAN') {
    return 'bg-blue-50 text-blue-600 dark:bg-blue-950/20 dark:text-blue-400 border-blue-200/50 dark:border-blue-900/50'
  }
  if (s === 'CONNECTING') {
    return 'bg-amber-50 text-amber-600 dark:bg-amber-950/20 dark:text-amber-400 border-amber-200/50 dark:border-amber-900/50'
  }
  return 'bg-red-50 text-red-600 dark:bg-red-950/20 dark:text-red-400 border-red-200/50 dark:border-red-900/50'
})

const statusDotClass = computed(() => {
  const s = state.value.toUpperCase()
  if (s === 'AUTHENTICATED' || s === 'CONNECTED') return 'bg-emerald-500'
  if (s === 'QR_PENDING' || s === 'NEED SCAN' || s === 'NEED_SCAN') return 'bg-blue-500'
  if (s === 'CONNECTING') return 'bg-amber-500 animate-ping'
  return 'bg-red-500'
})

const formattedUptime = computed(() => {
  const sec = uptime.value
  if (!sec || sec <= 0) return '00:00:00'
  const d = Math.floor(sec / (3600 * 24))
  const h = Math.floor((sec % (3600 * 24)) / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = Math.floor(sec % 60)

  const pad = (num) => String(num).padStart(2, '0')
  if (d > 0) {
    return `${d}d ${pad(h)}:${pad(m)}:${pad(s)}`
  }
  return `${pad(h)}:${pad(m)}:${pad(s)}`
})

// Fetch status from backend
const fetchStatus = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/wa/status')
    state.value = res.data.state
    uptime.value = res.data.uptime
    message_count.value = res.data.message_count
    error.value = res.data.error

    if (res.data.qr_base64) {
      if (qr_base64.value !== res.data.qr_base64) {
        qr_base64.value = res.data.qr_base64
        countdown.value = 60 // reset timer on QR change
      }
    } else {
      qr_base64.value = ''
    }
  } catch (err) {
    state.value = 'DISCONNECTED'
    qr_base64.value = ''
    uptime.value = 0
    error.value = 'Failed to communicate with API backend'
  }
}

// Reset session
const resetSession = async () => {
  if (isResetting.value) return
  isResetting.value = true
  try {
    logs.value.push('>>> Wiping WhatsApp session and initiating reset...')
    scrollToBottom()
    await axios.post('http://127.0.0.1:8000/wa/reset-session')
    logs.value.push('>>> Session reset successfully. Spawning new login gateway process...')
    scrollToBottom()
    await fetchStatus()
  } catch (err) {
    logs.value.push(`>>> Error resetting session: ${err.message}`)
    scrollToBottom()
  } finally {
    isResetting.value = false
  }
}

// Stream live logs via EventSource
const connectLogsStream = () => {
  if (logsSource) {
    logsSource.close()
  }

  logsSource = new EventSource('http://127.0.0.1:8000/logs/baileys')

  logsSource.onmessage = (event) => {
    logs.value.push(event.data)
    if (logs.value.length > 300) {
      logs.value.shift()
    }
    scrollToBottom()
  }

  logsSource.onerror = () => {
    logs.value.push('>>> Log stream disconnected. Reconnecting...')
    scrollToBottom()
    logsSource.close()
    setTimeout(connectLogsStream, 4000)
  }
}

const clearTerminal = () => {
  logs.value = []
}

const scrollToBottom = () => {
  nextTick(() => {
    if (terminalBody.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight
    }
  })
}

// QR Expiration Countdown
const runCountdown = () => {
  countdownInterval = setInterval(() => {
    if (needScan.value) {
      countdown.value--
      if (countdown.value <= 0) {
        countdown.value = 60
        fetchStatus()
      }
    }
  }, 1000)
}

onMounted(() => {
  fetchStatus()
  pollInterval = setInterval(fetchStatus, 2000)
  connectLogsStream()
  runCountdown()
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
  if (countdownInterval) clearInterval(countdownInterval)
  if (logsSource) logsSource.close()
})
</script>
