<template>
  <div 
    v-if="previewUrl"
    class="fixed inset-0 bg-black/50 dark:bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 sm:p-10 transition-colors"
    @click.self="$emit('close')"
  >
    <div class="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-850 rounded-2xl w-full max-w-6xl h-full max-h-[calc(100vh-2rem)] sm:max-h-[calc(100vh-5rem)] flex flex-col overflow-hidden shadow-lg animate-in fade-in duration-200">
      <!-- Modal Header -->
      <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-zinc-200 dark:border-zinc-850 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <FileText class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          <h3 class="font-semibold text-zinc-900 dark:text-zinc-200 truncate max-w-[150px] xs:max-w-xs sm:max-w-md" :title="previewFilename">{{ previewFilename }}</h3>
        </div>
        <button 
          @click="$emit('close')"
          class="p-1.5 rounded-lg bg-zinc-100 dark:bg-zinc-900 hover:bg-zinc-200 dark:hover:bg-zinc-850 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Modal Body (PDF Viewer) -->
      <div class="flex-1 bg-zinc-100 dark:bg-zinc-900 relative">
        <iframe 
          :src="previewUrl" 
          class="w-full h-full border-0" 
          title="PDF Preview"
        ></iframe>
      </div>
    </div>
  </div>
</template>

<script setup>
import { FileText, X } from 'lucide-vue-next'

const props = defineProps({
  previewUrl: {
    type: String,
    default: null
  },
  previewFilename: {
    type: String,
    default: ''
  }
})

defineEmits(['close'])
</script>
