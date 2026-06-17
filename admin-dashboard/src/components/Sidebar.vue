<template>
  <aside 
    class="w-72 bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col fixed inset-y-0 left-0 lg:relative z-40 lg:z-20 transform lg:transform-none transition-transform duration-300 ease-in-out"
    :class="isOpen ? 'translate-x-0 shadow-2xl lg:shadow-none' : '-translate-x-full lg:translate-x-0'"
  >
    <div class="h-20 flex items-center justify-between px-8 border-b border-zinc-200 dark:border-zinc-800">
      <h1 class="text-xl font-bold tracking-wide text-zinc-900 dark:text-zinc-100">R2CELL Admin</h1>
      <!-- Close button visible only on mobile -->
      <button 
        @click="$emit('close')" 
        class="lg:hidden p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors"
      >
        <X class="w-5 h-5" />
      </button>
    </div>
    
    <nav class="p-6 flex-1 space-y-2 overflow-y-auto">
      <div class="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-4 mt-2">Main Menu</div>
      
      <router-link :to="{ name: 'dashboard' }" @click="$emit('close')" class="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all" :class="[ $route.name === 'dashboard' ? 'text-zinc-900 dark:text-white bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 shadow-sm' : 'text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50' ]">
        <LayoutDashboard class="w-5 h-5" :class="$route.name === 'dashboard' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-405'" />
        Overview
      </router-link>

      <router-link :to="{ name: 'knowledge' }" @click="$emit('close')" class="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all" :class="[ $route.name === 'knowledge' ? 'text-zinc-900 dark:text-white bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 shadow-sm' : 'text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50' ]">
        <BookOpen class="w-5 h-5" :class="$route.name === 'knowledge' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-405'" />
        Knowledge Base
      </router-link>

      <router-link :to="{ name: 'conversations' }" @click="$emit('close')" class="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all" :class="[ $route.name === 'conversations' ? 'text-zinc-900 dark:text-white bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 shadow-sm' : 'text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50' ]">
        <MessageSquare class="w-5 h-5" :class="$route.name === 'conversations' ? 'text-zinc-900 dark:text-zinc-100' : 'text-zinc-405'" />
        Conversations
      </router-link>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50 rounded-xl transition-all">
        <Smartphone class="w-5 h-5" />
        WhatsApp Gateway
      </a>
      
      <div class="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-4 mt-8">System</div>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50 rounded-xl transition-all">
        <Server class="w-5 h-5" />
        Service Logs
      </a>
      <a href="#" class="flex items-center gap-3 px-4 py-3 text-sm font-medium text-zinc-550 dark:text-zinc-400 hover:text-zinc-900 hover:dark:text-zinc-100 hover:bg-zinc-100/50 hover:dark:bg-zinc-800/50 rounded-xl transition-all">
        <Settings class="w-5 h-5" />
        Settings
      </a>
    </nav>

    <div class="p-6 border-t border-zinc-200 dark:border-zinc-800">
      <div class="bg-zinc-50 dark:bg-zinc-800/40 rounded-xl p-4 flex items-center gap-4 border border-zinc-200 dark:border-zinc-800">
        <div class="w-10 h-10 rounded-full bg-zinc-205 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 flex items-center justify-center font-bold text-zinc-600 dark:text-zinc-300">
          SA
        </div>
        <div class="flex-1">
          <h4 class="text-sm font-semibold text-zinc-800 dark:text-zinc-200">System Admin</h4>
          <p class="text-xs text-zinc-500">R2CELL Bot Ops</p>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { 
  LayoutDashboard, 
  MessageSquare, 
  BookOpen, 
  Smartphone, 
  Settings, 
  Server,
  X
} from 'lucide-vue-next'

defineProps({
  isOpen: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>
