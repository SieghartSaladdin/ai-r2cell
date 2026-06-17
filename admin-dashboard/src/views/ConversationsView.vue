<template>
  <main class="flex-1 flex overflow-hidden bg-zinc-50 dark:bg-zinc-950 transition-colors duration-250 font-sans relative h-[calc(100vh-4rem)] lg:h-[calc(100vh-5rem)]">
    <!-- Sidebar: Contacts/Threads List -->
    <div 
      class="w-full md:w-80 lg:w-96 border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col shrink-0 transition-all duration-300"
      :class="[ isMobileChatActive ? 'hidden md:flex' : 'flex' ]"
    >
      <div class="p-5 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <div>
          <h2 class="text-xl font-bold text-zinc-900 dark:text-zinc-100">Customer Chats</h2>
          <p class="text-xs text-zinc-500 mt-0.5">Select a thread to view chat logs</p>
        </div>
        <button 
          @click="fetchThreads" 
          class="p-2 rounded-lg hover:bg-zinc-50 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 cursor-pointer transition-colors"
          title="Refresh active list"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isFetchingThreads }" />
        </button>
      </div>

      <!-- Conversations List -->
      <div class="flex-1 overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800/60 scrollbar-hide">
        <div v-if="isFetchingThreads && threads.length === 0" class="p-10 flex flex-col items-center justify-center text-center space-y-3">
          <Loader2 class="w-8 h-8 animate-spin text-zinc-400" />
          <span class="text-xs text-zinc-400">Loading active threads...</span>
        </div>
        
        <div v-else-if="threads.length === 0" class="p-10 flex flex-col items-center justify-center text-center space-y-4">
          <div class="w-12 h-12 rounded-xl bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center text-zinc-400 border border-zinc-200 dark:border-zinc-800">
            <MessageSquare class="w-6 h-6" />
          </div>
          <div>
            <h4 class="text-sm font-semibold text-zinc-800 dark:text-zinc-200">No active threads</h4>
            <p class="text-xs text-zinc-500 mt-1 max-w-[200px] mx-auto">
              Conversations will appear here once customers contact your WhatsApp bot.
            </p>
          </div>
        </div>

        <div 
          v-else
          v-for="thread in threads" 
          :key="thread.thread_id"
          @click="selectThread(thread)"
          class="p-4 flex items-start gap-3 cursor-pointer hover:bg-zinc-50/80 dark:hover:bg-zinc-800/10 transition-colors"
          :class="[ activeThread?.thread_id === thread.thread_id ? 'bg-zinc-50 dark:bg-zinc-800/30 border-l-2 border-zinc-900 dark:border-zinc-100' : '' ]"
        >
          <!-- Avatar Icon -->
          <div class="w-10 h-10 rounded-full bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 flex items-center justify-center text-zinc-600 dark:text-zinc-300 font-bold text-xs shrink-0 uppercase">
            {{ thread.thread_id.substring(0, 2) }}
          </div>
          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="flex justify-between items-baseline mb-1">
              <h4 class="text-sm font-bold text-zinc-800 dark:text-zinc-200 truncate">
                {{ thread.thread_id.split('@')[0] }}
              </h4>
              <span class="text-3xs text-zinc-450 dark:text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded border border-zinc-200 dark:border-zinc-750 font-semibold">
                {{ thread.message_count }} turns
              </span>
            </div>
            <p class="text-xs text-zinc-550 dark:text-zinc-400 truncate" :title="thread.last_message">
              {{ thread.last_message || 'Empty thread' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Chat History Box -->
    <div 
      class="flex-1 flex flex-col bg-zinc-50 dark:bg-zinc-950 transition-all duration-300"
      :class="[ !isMobileChatActive ? 'hidden md:flex' : 'flex' ]"
    >
      <!-- Chat Header -->
      <div v-if="activeThread" class="h-16 lg:h-20 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 px-6 flex items-center justify-between sticky top-0 z-10">
        <div class="flex items-center gap-3 min-w-0">
          <!-- Back button on mobile viewports -->
          <button 
            @click="isMobileChatActive = false"
            class="md:hidden p-2 -ml-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 cursor-pointer shrink-0 transition-colors"
          >
            <ChevronLeft class="w-5 h-5" />
          </button>
          
          <div class="min-w-0">
            <h3 class="font-bold text-zinc-900 dark:text-zinc-100 truncate text-sm sm:text-base">
              {{ activeThread.thread_id.split('@')[0] }}
            </h3>
            <p class="text-xs text-zinc-400">WhatsApp Contact Session</p>
          </div>
        </div>

        <button 
          @click="resetMemory"
          :disabled="isResetting"
          class="text-xs font-semibold px-3.5 py-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 hover:bg-red-50 dark:hover:bg-red-950/20 text-zinc-605 dark:text-zinc-400 hover:text-red-655 dark:hover:text-red-400 cursor-pointer transition-all flex items-center gap-1.5 disabled:opacity-40"
        >
          <Loader2 v-if="isResetting" class="w-3.5 h-3.5 animate-spin" />
          <Trash2 v-else class="w-3.5 h-3.5" />
          Reset AI Memory
        </button>
      </div>

      <!-- Chat Empty State -->
      <div v-if="!activeThread" class="flex-1 flex flex-col items-center justify-center text-center p-8 bg-zinc-50 dark:bg-zinc-950">
        <div class="w-20 h-20 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 flex items-center justify-center shadow-xs text-zinc-400 mb-4 animate-bounce duration-1000">
          <MessageSquare class="w-10 h-10 text-zinc-350 dark:text-zinc-650" />
        </div>
        <h3 class="text-lg font-bold text-zinc-800 dark:text-zinc-200 mb-1">Select a Conversation</h3>
        <p class="text-sm text-zinc-500 max-w-sm">
          Click any active client connection thread from the sidebar to inspect their dialogue history and manage memory status.
        </p>
      </div>

      <!-- Messages History -->
      <div 
        v-else 
        ref="chatContainer"
        class="flex-grow overflow-y-auto p-6 space-y-4 bg-zinc-50 dark:bg-zinc-950/40"
      >
        <div v-if="isLoadingMessages" class="flex flex-col items-center justify-center h-full text-zinc-400 space-y-3">
          <Loader2 class="w-8 h-8 animate-spin" />
          <span class="text-xs">Fetching conversation log...</span>
        </div>

        <div v-else-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-zinc-500 space-y-2">
          <AlertCircle class="w-6 h-6 text-zinc-400" />
          <span class="text-sm">This conversation has no message checkpoints.</span>
        </div>

        <template v-else>
          <div 
            v-for="(msg, idx) in messages" 
            :key="idx" 
            class="flex items-start gap-3 max-w-[85%] md:max-w-[70%]"
            :class="[ msg.sender === 'user' ? 'ml-auto flex-row-reverse' : '' ]"
          >
            <!-- Avatar -->
            <div 
              class="w-8.5 h-8.5 rounded-lg flex items-center justify-center border shrink-0 shadow-2xs"
              :class="[ msg.sender === 'user' ? 'bg-zinc-100 border-zinc-300 dark:bg-zinc-800 dark:border-zinc-700 text-zinc-650 dark:text-zinc-300' : 'bg-zinc-900 border-zinc-950 text-white dark:bg-white dark:border-zinc-200 dark:text-zinc-900' ]"
            >
              <User v-if="msg.sender === 'user'" class="w-4.5 h-4.5" />
              <Bot v-else class="w-4.5 h-4.5" />
            </div>

            <!-- Bubble -->
            <div 
              class="rounded-2xl p-4 text-sm shadow-2xs leading-relaxed break-words"
              :class="[ msg.sender === 'user' ? 'bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200 rounded-tr-none' : 'bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200 rounded-tl-none' ]"
            >
              <p class="whitespace-pre-wrap">{{ msg.text }}</p>
            </div>
          </div>
        </template>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { 
  MessageSquare, 
  Trash2, 
  ChevronLeft, 
  User, 
  Bot, 
  Loader2, 
  AlertCircle, 
  RefreshCw 
} from 'lucide-vue-next'

const threads = ref([])
const activeThread = ref(null)
const messages = ref([])

const isFetchingThreads = ref(false)
const isLoadingMessages = ref(false)
const isResetting = ref(false)
const isMobileChatActive = ref(false)

const chatContainer = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// Fetch all conversation threads from SQLite checkpoints
const fetchThreads = async () => {
  isFetchingThreads.value = true
  try {
    const res = await fetch('http://localhost:8000/api/chat/threads')
    if (!res.ok) throw new Error('Failed to retrieve active contact list')
    threads.value = await res.json()
    
    // Refresh turns / last active info on selected thread if it exists
    if (activeThread.value) {
      const refreshed = threads.value.find(t => t.thread_id === activeThread.value.thread_id)
      if (refreshed) {
        activeThread.value = refreshed
      } else {
        // Active thread was deleted by another browser or action
        activeThread.value = null
        messages.value = []
        isMobileChatActive.value = false
      }
    }
  } catch (err) {
    console.error('Error loading chat contacts list:', err)
  } finally {
    isFetchingThreads.value = false
  }
}

// Select a contact and load message logs
const selectThread = async (thread) => {
  activeThread.value = thread
  isMobileChatActive.value = true
  isLoadingMessages.value = true
  messages.value = []
  
  try {
    const res = await fetch(`http://localhost:8000/api/chat/threads/${encodeURIComponent(thread.thread_id)}/messages`)
    if (!res.ok) throw new Error('Failed to retrieve chat log history')
    messages.value = await res.json()
    scrollToBottom()
  } catch (err) {
    console.error(err)
    alert(`Could not load chat history: ${err.message}`)
  } finally {
    isLoadingMessages.value = false
  }
}

// Reset memory for current contact
const resetMemory = async () => {
  if (!activeThread.value) return
  
  const threadId = activeThread.value.thread_id
  const cleanedName = threadId.split('@')[0]
  const confirmMsg = `Are you sure you want to reset the AI memory for "${cleanedName}"?\n\nThis will permanently clear all past conversation history for this WhatsApp contact.`
  if (!confirm(confirmMsg)) return

  isResetting.value = true
  try {
    const res = await fetch(`http://localhost:8000/api/chat/threads/${encodeURIComponent(threadId)}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to clear session memory')
    
    // Success: clear UI and reload lists
    activeThread.value = null
    messages.value = []
    isMobileChatActive.value = false
    await fetchThreads()
  } catch (err) {
    console.error(err)
    alert(`Failed to reset memory: ${err.message}`)
  } finally {
    isResetting.value = false
  }
}

onMounted(() => {
  fetchThreads()
})
</script>

<style scoped>
/* Scoped custom utilities for scrollbar hide in conversation panel */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>
