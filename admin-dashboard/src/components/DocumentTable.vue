<template>
  <div class="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden transition-all duration-250">
    <!-- Actions Bar -->
    <div class="p-6 border-b border-zinc-200 dark:border-zinc-800 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Ingested Files</h3>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">Vector database retrieves context from these items.</p>
      </div>
      <!-- Search Input -->
      <div class="relative w-full sm:w-72">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="Search documents..." 
          class="w-full bg-zinc-50 dark:bg-zinc-950 text-zinc-850 dark:text-zinc-100 pl-4 pr-10 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-700 transition-colors text-sm"
        />
        <span class="absolute right-3 top-3 text-zinc-400 dark:text-zinc-500">
          <Search class="w-4 h-4" />
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="filteredDocs.length === 0" class="p-20 flex flex-col items-center justify-center text-center">
      <div class="w-16 h-16 rounded-2xl bg-zinc-50 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-700/60 flex items-center justify-center mb-4 text-zinc-400 dark:text-zinc-550">
        <FileText class="w-8 h-8" />
      </div>
      <h4 class="text-lg font-medium text-zinc-800 dark:text-zinc-200 mb-1">No documents found</h4>
      <p class="text-zinc-500 dark:text-zinc-455 text-sm max-w-sm">
        {{ searchQuery ? 'Try adjusting your search query.' : 'Upload PDFs to embed training context for your customer service bot.' }}
      </p>
    </div>

    <!-- Document List Wrapper -->
    <div v-else>
      <!-- Desktop Table View -->
      <div class="hidden md:block overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/30">
              <th class="p-4 pl-6 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Name</th>
              <th class="p-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Size</th>
              <th class="p-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Ingested At</th>
              <th class="p-4 pr-6 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-200 dark:divide-zinc-800">
            <tr v-for="doc in filteredDocs" :key="doc.filename" class="hover:bg-zinc-50 dark:hover:bg-zinc-800/10 transition-colors">
              <td class="p-4 pl-6 font-medium text-zinc-800 dark:text-zinc-200">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-lg bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 flex items-center justify-center shrink-0">
                    <FileText class="w-4.5 h-4.5 text-zinc-550 dark:text-zinc-400" />
                  </div>
                  <span class="truncate max-w-[280px] sm:max-w-md" :title="doc.filename">
                    {{ doc.filename }}
                  </span>
                </div>
              </td>
              <td class="p-4 text-sm text-zinc-600 dark:text-zinc-300">
                {{ formatSize(doc.size) }}
              </td>
              <td class="p-4 text-sm text-zinc-550 dark:text-zinc-400">
                {{ formatDate(doc.modified_at) }}
              </td>
              <td class="p-4 pr-6 text-right">
                <div class="flex items-center justify-end gap-2">
                  <!-- Preview -->
                  <button 
                    @click="$emit('preview', doc.filename)"
                    class="p-2 rounded-lg hover:bg-zinc-150 dark:hover:bg-zinc-800 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors cursor-pointer"
                    title="Preview PDF"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  
                  <!-- Delete -->
                  <button 
                    @click="$emit('delete', doc.filename)"
                    :disabled="isDeleting === doc.filename"
                    class="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/20 text-zinc-500 dark:text-zinc-400 hover:text-red-650 dark:hover:text-red-400 transition-colors cursor-pointer disabled:opacity-40"
                    title="Delete File & Embeddings"
                  >
                    <Loader2 v-if="isDeleting === doc.filename" class="w-4 h-4 animate-spin text-zinc-400" />
                    <Trash2 v-else class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Mobile Card View -->
      <div class="md:hidden divide-y divide-zinc-200 dark:divide-zinc-800">
        <div v-for="doc in filteredDocs" :key="doc.filename" class="p-5 flex flex-col gap-3 hover:bg-zinc-50/50 dark:hover:bg-zinc-800/10 transition-colors">
          <div class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-lg bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 flex items-center justify-center shrink-0">
              <FileText class="w-4.5 h-4.5 text-zinc-550 dark:text-zinc-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-zinc-800 dark:text-zinc-200 break-all" :title="doc.filename">
                {{ doc.filename }}
              </h4>
              <div class="flex items-center gap-3 mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                <span>{{ formatSize(doc.size) }}</span>
                <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></span>
                <span>{{ formatDate(doc.modified_at) }}</span>
              </div>
            </div>
          </div>
          
          <div class="flex items-center justify-end gap-3 pt-2 border-t border-zinc-100 dark:border-zinc-800/60">
            <button 
              @click="$emit('preview', doc.filename)"
              class="flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors cursor-pointer"
            >
              <Eye class="w-3.5 h-3.5" />
              Preview
            </button>
            
            <button 
              @click="$emit('delete', doc.filename)"
              :disabled="isDeleting === doc.filename"
              class="flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-655 dark:hover:text-red-400 transition-colors cursor-pointer disabled:opacity-40"
            >
              <Loader2 v-if="isDeleting === doc.filename" class="w-3.5 h-3.5 animate-spin" />
              <Trash2 v-else class="w-3.5 h-3.5" />
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { FileText, Eye, Trash2, Loader2, Search } from 'lucide-vue-next'

const props = defineProps({
  documents: {
    type: Array,
    required: true
  },
  isDeleting: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['preview', 'delete'])

const searchQuery = ref('')

const filteredDocs = computed(() => {
  if (!searchQuery.value) return props.documents
  const query = searchQuery.value.toLowerCase()
  return props.documents.filter(doc => doc.filename.toLowerCase().includes(query))
})

const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp * 1000).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>
