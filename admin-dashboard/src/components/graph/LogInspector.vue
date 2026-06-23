<template>
  <aside 
    class="w-80 bg-white/95 dark:bg-zinc-900/90 backdrop-blur-md border-l border-zinc-200 dark:border-zinc-800 flex flex-col z-45 lg:z-10 transition-transform duration-300 lg:translate-x-0 lg:relative lg:h-full"
    :class="[
      lgScreen ? 'translate-x-0' : 'fixed inset-y-0 right-0 h-screen',
      (!lgScreen && isOpen) ? 'translate-x-0 shadow-2xl' : (!lgScreen ? 'translate-x-full' : '')
    ]"
  >
    <div class="p-6 border-b border-zinc-200 dark:border-zinc-800/80 flex justify-between items-center bg-zinc-50/40 dark:bg-zinc-900/40">
      <h2 class="text-sm font-bold flex items-center gap-2 text-zinc-800 dark:text-zinc-200">
        <Activity class="w-4.5 h-4.5 text-emerald-500" />
        Log Inspector
      </h2>
      <button 
        v-if="!lgScreen"
        @click="$emit('close')" 
        class="p-1.5 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg text-zinc-400 hover:text-zinc-600 transition-all cursor-pointer"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
    
    <div class="p-6 flex-1 flex flex-col overflow-hidden">
      <div v-if="selectedThread" class="bg-zinc-50 dark:bg-zinc-950 p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-900 mb-5 transition-all duration-300">
        <span class="text-[9px] text-zinc-400 dark:text-zinc-500 font-bold uppercase tracking-wider block mb-1">Inspecting Thread</span>
        <span class="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold truncate block">{{ cleanJid(selectedThread) }}</span>
      </div>

      <!-- Logs -->
      <h3 class="text-[9px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-widest mb-3">Session Logs</h3>
      <div class="flex-1 space-y-3 overflow-y-auto scrollbar-hide text-sm pr-1">
        <div 
          v-for="(log, idx) in activeLogs" 
          :key="idx" 
          class="p-3 bg-zinc-50/80 dark:bg-zinc-950/80 border border-zinc-200 dark:border-zinc-900 rounded-xl font-mono text-xs flex flex-col gap-1 transition-all duration-200"
        >
          <div class="flex justify-between items-center mb-1">
            <span class="text-zinc-400 dark:text-zinc-650 text-[10px]">{{ log.time }}</span>
            <span 
              class="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wide"
              :class="log.status === 'running' ? 'bg-amber-500/10 text-amber-500 dark:text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-650 dark:text-emerald-400 border border-emerald-500/20'"
            >
              {{ log.status }}
            </span>
          </div>
          <div class="text-zinc-600 dark:text-zinc-300">
            Node: <span class="text-zinc-800 dark:text-zinc-100 font-bold">{{ log.nodeName }}</span>
          </div>
        </div>
        <div v-if="activeLogs.length === 0" class="text-zinc-400 dark:text-zinc-500 text-center py-12 flex flex-col items-center gap-2">
          <Cpu class="w-8 h-8 text-zinc-300 dark:text-zinc-800" :class="{ 'animate-pulse': selectedThread }" />
          <p class="text-xs font-semibold">No logs for this session.</p>
          <p class="text-[9px] text-zinc-400 dark:text-zinc-600">Select a thread and send a chat message to start logging.</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { Activity, Cpu, X } from 'lucide-vue-next'

defineProps({
  activeLogs: {
    type: Array,
    required: true
  },
  selectedThread: {
    type: String,
    default: null
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

defineEmits(['close'])

const cleanJid = (jid) => {
  if (!jid) return ''
  return jid.split('@')[0]
}
</script>
