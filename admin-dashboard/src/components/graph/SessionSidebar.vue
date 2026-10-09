<template>
  <aside 
    class="w-72 bg-white/95 dark:bg-zinc-900/90 backdrop-blur-md border-r border-zinc-200 dark:border-zinc-800 flex flex-col z-45 lg:z-10 transition-transform duration-300 lg:translate-x-0 lg:relative lg:h-full"
    :class="[
      lgScreen ? 'translate-x-0' : 'fixed inset-y-0 left-0 h-screen',
      (!lgScreen && isOpen) ? 'translate-x-0 shadow-2xl' : (!lgScreen ? '-translate-x-full' : '')
    ]"
  >
    <div class="p-4 border-b border-zinc-200 dark:border-zinc-800/80 flex justify-between items-center bg-zinc-50/40 dark:bg-zinc-900/40">
      <h3 class="text-xs font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-widest flex items-center gap-2">
        <MessageSquare class="w-4 h-4" />
        Active Sessions
      </h3>
      <div class="flex items-center gap-1">
        <button 
          @click="$emit('refresh-threads')" 
          class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-all active:scale-95 cursor-pointer"
          title="Refresh Session List"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isRefreshing }" />
        </button>
        <button 
          v-if="!lgScreen"
          @click="$emit('close')" 
          class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-zinc-600 transition-all cursor-pointer"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-hide">
      <div 
        v-for="thread in threads" 
        :key="thread"
        @click="$emit('select-thread', thread)"
        class="w-full flex items-center justify-between p-3 rounded-xl border text-left cursor-pointer transition-all duration-200"
        :class="selectedThread === thread 
          ? 'bg-zinc-100 dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700/60 shadow-sm text-zinc-900 dark:text-white font-bold' 
          : 'bg-white/40 dark:bg-zinc-950/40 border-zinc-200/60 dark:border-zinc-900/60 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-200 hover:bg-zinc-100/30 hover:dark:bg-zinc-900/30 hover:border-zinc-200 hover:dark:border-zinc-800'"
      >
        <div class="flex-1 min-w-0">
          <span class="text-xs font-semibold font-mono truncate block">{{ cleanJid(thread) }}</span>
          <span class="text-[9px] text-zinc-400 dark:text-zinc-500 truncate block mt-0.5">WhatsApp Client Session</span>
        </div>
        
        <!-- Execution indicator -->
        <div v-if="backgroundExecuting[thread]" class="flex h-2 w-2 relative ml-2 shrink-0">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </div>
      </div>

      <div v-if="threads.length === 0" class="text-zinc-400 dark:text-zinc-500 text-center py-12 text-xs flex flex-col items-center gap-1.5">
        <MessageSquare class="w-6 h-6 text-zinc-300 dark:text-zinc-800" />
        No active threads found.
      </div>
    </div>
  </aside>
</template>

<script setup>
import { MessageSquare, RefreshCw, X } from 'lucide-vue-next'

defineProps({
  threads: {
    type: Array,
    required: true
  },
  selectedThread: {
    type: String,
    default: null
  },
  isRefreshing: {
    type: Boolean,
    default: false
  },
  backgroundExecuting: {
    type: Object,
    default: () => ({})
  },
  lgScreen: {
    type: Boolean,
    default: true
  },
  isOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select-thread', 'refresh-threads', 'close'])

const cleanJid = (jid) => {
  if (!jid) return ''
  return jid.split('@')[0]
}
</script>
