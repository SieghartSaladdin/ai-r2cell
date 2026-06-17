<template>
  <main class="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 scrollbar-hide transition-colors duration-250">
    <!-- Welcome Header -->
    <div class="flex items-end justify-between">
      <div>
        <h2 class="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">Service Dashboard</h2>
        <p class="text-zinc-500 dark:text-zinc-400">Monitor LangGraph AI agent and WhatsApp Gateway performance.</p>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Stat Card 1: WhatsApp Status -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <MessageCircle class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <MessageCircle class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Gateway Status</h3>
        </div>
        <div class="flex items-end gap-3">
          <p class="text-2xl font-bold" :class="statusData?.baileys?.state === 'AUTHENTICATED' || statusData?.baileys?.state === 'CONNECTED' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-500 dark:text-zinc-400'">
            {{ statusData?.baileys?.state || 'OFFLINE' }}
          </p>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">
          Uptime: {{ formatUptime(statusData?.baileys?.uptime) }}
        </p>
      </div>

      <!-- Stat Card 2: AI Messages -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Bot class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Bot class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">AI Replies Sent</h3>
        </div>
        <div class="flex items-end gap-3">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ statusData?.baileys?.message_count || 0 }}</p>
        </div>
        <p class="text-xs text-zinc-450 dark:text-zinc-500 mt-2">Powered by Ollama</p>
      </div>

      <!-- Stat Card 3: RAG Documents -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Database class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Database class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">RAG Vector DB</h3>
        </div>
        <div class="flex items-end gap-3">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">34</p>
          <span class="text-sm text-zinc-450 dark:text-zinc-500 mb-1">Docs</span>
        </div>
        <p class="text-xs text-zinc-450 dark:text-zinc-500 mt-2">ChromaDB Synced</p>
      </div>

      <!-- Stat Card 4: FastAPI Status -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Activity class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Activity class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">FastAPI Requests</h3>
        </div>
        <div class="flex items-end gap-3">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ statusData?.fastapi?.request_count || 0 }}</p>
        </div>
        <p class="text-xs text-zinc-450 dark:text-zinc-500 mt-2">Last req: {{ statusData?.fastapi?.last_request || 'never' }}</p>
      </div>
    </div>

    <!-- Main Dashboard Area -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
      
      <!-- Conversations Table -->
      <div class="xl:col-span-2 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden transition-all duration-250 flex flex-col">
        <div class="p-6 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center gap-4">
          <div>
            <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Active Conversations</h3>
            <p class="text-xs text-zinc-555 dark:text-zinc-400 mt-0.5">Real-time memory states extracted from LangGraph SQLite checkpointer.</p>
          </div>
          <button 
            v-if="chatThreads.length > 0"
            @click="resetAllMemories" 
            :disabled="isResettingAll"
            class="text-xs font-semibold px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:bg-red-50 dark:hover:bg-red-950/20 text-zinc-600 dark:text-zinc-400 hover:text-red-655 dark:hover:text-red-400 cursor-pointer transition-all flex items-center gap-1.5 disabled:opacity-40"
          >
            <Loader2 v-if="isResettingAll" class="w-3.5 h-3.5 animate-spin" />
            <Trash2 v-else class="w-3.5 h-3.5" />
            Clear All Memory
          </button>
        </div>

        <!-- Empty State -->
        <div v-if="chatThreads.length === 0" class="p-20 flex flex-col items-center justify-center text-center flex-grow">
          <div class="w-16 h-16 rounded-2xl bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/60 flex items-center justify-center mb-4 text-zinc-400 dark:text-zinc-550">
            <MessageCircle class="w-8 h-8" />
          </div>
          <h4 class="text-lg font-medium text-zinc-800 dark:text-zinc-200 mb-1">No active chats</h4>
          <p class="text-zinc-500 dark:text-zinc-450 text-sm max-w-sm">
            When customers message your WhatsApp bot, their chat history and memory states will appear here.
          </p>
        </div>

        <template v-else>
          <!-- Desktop Table View -->
          <div class="hidden md:block overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-zinc-50/50 dark:bg-zinc-950/30 text-zinc-500 dark:text-zinc-400 text-xs font-semibold uppercase tracking-wider border-b border-zinc-200 dark:border-zinc-800">
                  <th class="px-6 py-4 pl-6">Contact / JID</th>
                  <th class="px-6 py-4">Turns</th>
                  <th class="px-6 py-4">Last Message</th>
                  <th class="px-6 py-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody class="text-sm divide-y divide-zinc-200 dark:divide-zinc-800">
                <tr v-for="thread in chatThreads" :key="thread.thread_id" class="hover:bg-zinc-50 dark:hover:bg-zinc-800/10 transition-colors">
                  <td class="px-6 py-4 pl-6 font-mono text-zinc-800 dark:text-zinc-250 font-medium">
                    {{ thread.thread_id.split('@')[0] }}
                  </td>
                  <td class="px-6 py-4 text-zinc-600 dark:text-zinc-350">
                    {{ thread.message_count }}
                  </td>
                  <td class="px-6 py-4 max-w-xs lg:max-w-md">
                    <div class="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400">
                      <span class="text-2xs px-1.5 py-0.5 rounded-md bg-zinc-105 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-semibold shrink-0 border border-zinc-200 dark:border-zinc-700/60">
                        {{ thread.last_message_sender }}
                      </span>
                      <span class="truncate text-sm text-zinc-700 dark:text-zinc-300" :title="thread.last_message">
                        {{ thread.last_message }}
                      </span>
                    </div>
                  </td>
                  <td class="px-6 py-4 pr-6 text-right">
                    <button 
                      @click="resetThreadMemory(thread.thread_id)"
                      :disabled="isResettingThread === thread.thread_id"
                      class="p-2 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-500 dark:text-zinc-400 hover:bg-red-50 hover:text-red-650 dark:hover:bg-red-950/20 dark:hover:text-red-400 transition-all cursor-pointer disabled:opacity-40"
                      title="Reset conversation memory"
                    >
                      <Loader2 v-if="isResettingThread === thread.thread_id" class="w-4 h-4 animate-spin text-zinc-400" />
                      <Trash2 v-else class="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile Card List View -->
          <div class="md:hidden divide-y divide-zinc-200 dark:divide-zinc-800">
            <div v-for="thread in chatThreads" :key="thread.thread_id" class="p-5 flex flex-col gap-3 hover:bg-zinc-50/50 dark:hover:bg-zinc-800/10 transition-colors">
              <div class="flex items-center justify-between">
                <span class="font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-250">
                  {{ thread.thread_id.split('@')[0] }}
                </span>
                <span class="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100 dark:bg-zinc-850 px-2 py-0.5 rounded-full border border-zinc-200 dark:border-zinc-750">
                  {{ thread.message_count }} turns
                </span>
              </div>
              <div class="bg-zinc-50 dark:bg-zinc-950/50 p-3 rounded-xl border border-zinc-200 dark:border-zinc-800/80">
                <div class="text-2xs text-zinc-400 dark:text-zinc-500 font-semibold mb-1 uppercase tracking-wider">
                  Last message ({{ thread.last_message_sender }})
                </div>
                <p class="text-sm text-zinc-700 dark:text-zinc-300 break-words line-clamp-2" :title="thread.last_message">
                  {{ thread.last_message }}
                </p>
              </div>
              <div class="flex justify-end pt-1">
                <button 
                  @click="resetThreadMemory(thread.thread_id)"
                  :disabled="isResettingThread === thread.thread_id"
                  class="flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-655 dark:hover:text-red-400 transition-all cursor-pointer disabled:opacity-40"
                >
                  <Loader2 v-if="isResettingThread === thread.thread_id" class="w-3.5 h-3.5 animate-spin" />
                  <Trash2 v-else class="w-3.5 h-3.5" />
                  Reset Memory
                </button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Server Status Card (REAL JSON) -->
      <div class="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm p-6 flex flex-col h-[420px] transition-all duration-250">
        <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-6 flex items-center gap-2">
          <Server class="w-5 h-5 text-zinc-400" />
          Raw Backend Data
        </h3>
        
        <div class="flex-1 bg-zinc-950 rounded-xl border border-zinc-200 dark:border-zinc-800 p-4 font-mono text-sm overflow-hidden relative group">
          <div class="absolute top-0 left-0 w-full h-[1px] bg-zinc-200 dark:bg-zinc-800"></div>
          
          <div v-if="isLoading && !statusData" class="flex flex-col items-center justify-center h-full text-zinc-500 gap-3">
            <Activity class="w-6 h-6 animate-pulse text-zinc-400" />
            <span>Pinging server...</span>
          </div>
          
          <div v-else-if="statusData" class="h-full">
            <div class="flex items-center justify-between mb-3 pb-3 border-b border-zinc-200 dark:border-zinc-800">
              <span class="text-zinc-300 flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-zinc-400 animate-pulse"></span>
                200 OK
              </span>
              <span class="text-zinc-500 text-xs">/api/internal/status</span>
            </div>
            <pre class="text-zinc-300 overflow-x-auto text-xs leading-relaxed whitespace-pre-wrap break-words h-[calc(100%-40px)] scrollbar-hide">{{ JSON.stringify(statusData, null, 2) }}</pre>
          </div>

          <div v-else class="flex flex-col items-center justify-center h-full text-zinc-500 gap-3">
            <ShieldAlert class="w-6 h-6" />
            <span class="text-center text-xs">Failed to connect to backend.<br>Is FastAPI running?</span>
          </div>
        </div>
        
        <div class="mt-6 flex items-center justify-between text-xs text-zinc-500">
          <span>Last checked: {{ lastChecked }}</span>
          <button @click="fetchServerInfo" class="hover:text-zinc-800 dark:hover:text-zinc-300 transition-colors flex items-center gap-1 cursor-pointer">
            <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
            Refresh
          </button>
        </div>
      </div>

    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  Activity, 
  Bot, 
  Database, 
  Server,
  ShieldAlert,
  CheckCircle,
  RefreshCw,
  QrCode,
  MessageCircle,
  Trash2,
  Loader2
} from 'lucide-vue-next'

const statusData = ref(null)
const isLoading = ref(true)
const lastChecked = ref('Never')
let pollingInterval = null

// Chat Threads state
const chatThreads = ref([])
const isFetchingThreads = ref(true)
const isResettingThread = ref(null) // thread_id of the thread being reset
const isResettingAll = ref(false)

const formatUptime = (seconds) => {
  if (!seconds) return '0s'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  
  if (h > 0) return `${h}h ${m}m ${s}s`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

const fetchServerInfo = async () => {
  isLoading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/internal/status')
    if (!res.ok) throw new Error('Network response was not ok')
    const data = await res.json()
    statusData.value = data
    lastChecked.value = new Date().toLocaleTimeString()
  } catch (err) {
    console.error('Error fetching server info:', err)
  } finally {
    isLoading.value = false
  }
}

// Fetch active chat threads
const fetchChatThreads = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/chat/threads')
    if (!res.ok) throw new Error('Failed to fetch chat threads')
    const data = await res.json()
    chatThreads.value = data
  } catch (err) {
    console.error('Error fetching chat threads:', err)
  } finally {
    isFetchingThreads.value = false
  }
}

// Reset memory for a single thread_id
const resetThreadMemory = async (threadId) => {
  const confirmMsg = `Are you sure you want to reset the conversation memory for this chat?\n\nContact: "${threadId.split('@')[0]}"\n\nAll checkpoints and history will be permanently deleted.`
  if (!confirm(confirmMsg)) return

  isResettingThread.value = threadId
  try {
    const res = await fetch(`http://localhost:8000/api/chat/threads/${encodeURIComponent(threadId)}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to reset memory')
    await fetchChatThreads()
  } catch (err) {
    console.error(err)
    alert(`Failed to reset conversation memory: ${err.message}`)
  } finally {
    isResettingThread.value = null
  }
}

// Reset memory for all threads
const resetAllMemories = async () => {
  const confirmMsg = `WARNING: Are you sure you want to wipe ALL conversation memories?\n\nThis will permanently delete history for every active chat session.`
  if (!confirm(confirmMsg)) return

  isResettingAll.value = true
  try {
    const res = await fetch('http://localhost:8000/api/chat/threads', {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to reset all memories')
    await fetchChatThreads()
  } catch (err) {
    console.error(err)
    alert(`Failed to reset all memories: ${err.message}`)
  } finally {
    isResettingAll.value = false
  }
}

onMounted(() => {
  fetchServerInfo()
  fetchChatThreads()
  
  // Poll every 5 seconds
  pollingInterval = setInterval(() => {
    fetchServerInfo()
    fetchChatThreads()
  }, 5000)
})

onUnmounted(() => {
  if (pollingInterval) clearInterval(pollingInterval)
})
</script>
