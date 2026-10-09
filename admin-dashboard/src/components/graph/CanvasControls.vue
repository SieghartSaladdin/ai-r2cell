<template>
  <div class="absolute top-4 right-4 z-10 flex gap-1.5 pointer-events-auto">
    <button 
      @click="$emit('zoom-in')"
      class="p-2 bg-white/90 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl text-zinc-600 dark:text-zinc-300 transition-all shadow-md active:scale-90 backdrop-blur-sm cursor-pointer"
      title="Zoom In"
    >
      <Plus class="w-4 h-4" />
    </button>
    <button 
      @click="$emit('zoom-out')"
      class="p-2 bg-white/90 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl text-zinc-600 dark:text-zinc-300 transition-all shadow-md active:scale-90 backdrop-blur-sm cursor-pointer"
      title="Zoom Out"
    >
      <Minus class="w-4 h-4" />
    </button>
    <button 
      @click="$emit('fit-view')"
      class="p-2 bg-white/90 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl text-zinc-600 dark:text-zinc-300 transition-all shadow-md active:scale-90 backdrop-blur-sm cursor-pointer"
      title="Fit View"
    >
      <Maximize2 class="w-4 h-4" />
    </button>
    <button 
      @click="$emit('toggle-interactive')"
      class="p-2 border rounded-xl transition-all shadow-md active:scale-90 backdrop-blur-sm cursor-pointer"
      :class="[
        isInteractive 
          ? 'bg-white/90 dark:bg-zinc-900/90 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-300'
          : 'bg-amber-50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-900/60 text-amber-600 dark:text-amber-400'
      ]"
      :title="isInteractive ? 'Lock Board (Disable drag/zoom)' : 'Unlock Board (Enable drag/zoom)'"
    >
      <component :is="isInteractive ? Unlock : Lock" class="w-4 h-4" />
    </button>
  </div>
</template>

<script setup>
import { Plus, Minus, Maximize2, Lock, Unlock } from 'lucide-vue-next'

defineProps({
  isInteractive: {
    type: Boolean,
    default: true
  }
})

defineEmits(['zoom-in', 'zoom-out', 'fit-view', 'toggle-interactive'])
</script>
