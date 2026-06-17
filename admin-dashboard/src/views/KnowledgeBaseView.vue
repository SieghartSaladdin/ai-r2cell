<template>
  <main class="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 scrollbar-hide transition-colors duration-250">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">Knowledge Base & RAG</h2>
        <p class="text-zinc-500 dark:text-zinc-400">Manage PDF documents and ChromaDB vector embeddings for the AI.</p>
      </div>
      
      <!-- Upload Trigger Button -->
      <div>
        <button 
          @click="triggerFileInput"
          class="w-full sm:w-auto bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm flex items-center justify-center gap-2 cursor-pointer"
        >
          <UploadCloud class="w-5 h-5" />
          Upload PDF Document
        </button>
        <input 
          type="file" 
          ref="fileInput" 
          class="hidden" 
          accept=".pdf" 
          @change="handleFileUpload" 
        />
      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Total Documents -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <FileText class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <FileText class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Active Documents</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ docs.length }}</p>
          <span class="text-sm text-zinc-500 mb-1">PDF{{ docs.length !== 1 ? 's' : '' }}</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Available for semantic search</p>
      </div>

      <!-- Vector Store Status -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Database class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Database class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Database Index</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-3xl font-bold text-zinc-800 dark:text-zinc-100">ChromaDB</p>
        </div>
        <p class="text-xs text-zinc-500 dark:text-zinc-450 mt-3 flex items-center gap-1.5">
          <span class="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse"></span>
          Ready & Connected
        </p>
      </div>

      <!-- Total Memory / Space Used -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <HardDrive class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <HardDrive class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Total Size</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ formatSize(totalStorageSize) }}</p>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Space occupied in src/data</p>
      </div>
    </div>

    <!-- main Documents Explorer -->
    <div v-if="isLoading" class="p-20 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col items-center justify-center space-y-4">
      <Loader2 class="w-10 h-10 text-zinc-500 animate-spin" />
      <p class="text-zinc-400 text-sm">Loading document list...</p>
    </div>
    
    <DocumentTable 
      v-else 
      :documents="docs" 
      :is-deleting="isDeleting"
      @preview="openPreview"
      @delete="deleteDoc"
    />

    <!-- Upload Overlay Loading Spinner -->
    <div 
      v-if="isUploading"
      class="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4"
    >
      <div class="bg-white dark:bg-zinc-900 p-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 flex flex-col items-center max-w-sm text-center shadow-lg transition-all mx-4">
        <Loader2 class="w-12 h-12 text-zinc-500 dark:text-zinc-450 animate-spin mb-4" />
        <h3 class="text-lg font-semibold text-zinc-900 dark:text-zinc-150 mb-2">Ingesting Document</h3>
        <p class="text-sm text-zinc-500 dark:text-zinc-450">
          We are analyzing, splitting, and uploading your PDF to ChromaDB vector store...
        </p>
      </div>
    </div>

    <!-- PDF Preview Modal -->
    <PdfPreviewModal 
      :preview-url="previewUrl"
      :preview-filename="previewFilename"
      @close="closePreview"
    />
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { 
  Database, 
  UploadCloud, 
  FileText, 
  Loader2, 
  HardDrive 
} from 'lucide-vue-next'
import DocumentTable from '../components/DocumentTable.vue'
import PdfPreviewModal from '../components/PdfPreviewModal.vue'

const docs = ref([])
const fileInput = ref(null)
const isLoading = ref(true)

const isUploading = ref(false)
const isDeleting = ref(null) // Stores filename of doc being deleted

// Preview Modal State
const previewUrl = ref(null)
const previewFilename = ref('')

const totalStorageSize = computed(() => {
  return docs.value.reduce((total, doc) => total + (doc.size || 0), 0)
})

const fetchDocs = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/docs')
    if (!res.ok) throw new Error('Failed to fetch document list')
    docs.value = await res.json()
  } catch (err) {
    console.error('Error fetching docs:', err)
  } finally {
    isLoading.value = false
  }
}

const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click()
  }
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    alert('Please upload PDF files only.')
    return
  }

  isUploading.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetch('http://localhost:8000/upload-doc', {
      method: 'POST',
      body: formData
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Upload failed')
    }
    
    await fetchDocs()
    
    // Reset file input
    if (fileInput.value) {
      fileInput.value.value = ''
    }
  } catch (err) {
    console.error(err)
    alert(`Failed to upload document: ${err.message}`)
  } finally {
    isUploading.value = false
  }
}

const deleteDoc = async (filename) => {
  const confirmMsg = `Are you sure you want to delete "${filename}"?\n\nThis will remove it from disk and delete its RAG vector embeddings.`
  if (!confirm(confirmMsg)) return
  
  isDeleting.value = filename
  try {
    const res = await fetch(`http://localhost:8000/api/docs/${encodeURIComponent(filename)}`, {
      method: 'DELETE'
    })
    
    if (!res.ok) {
      const errData = await res.json()
      throw new Error(errData.detail || 'Deletion failed')
    }
    
    await fetchDocs()
  } catch (err) {
    console.error(err)
    alert(`Failed to delete document: ${err.message}`)
  } finally {
    isDeleting.value = null
  }
}

const openPreview = async (filename) => {
  previewFilename.value = filename
  try {
    const nameWithoutExt = filename.replace(/\.pdf$/i, '')
    const res = await fetch(`http://localhost:8000/api/docs/preview-json/${encodeURIComponent(nameWithoutExt)}`)
    if (!res.ok) throw new Error('Failed to retrieve PDF data')
    
    const json = await res.json()
    
    // Decode Base64 string to Blob
    const byteString = atob(json.data)
    const ab = new ArrayBuffer(byteString.length)
    const ia = new Uint8Array(ab)
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i)
    }
    const blob = new Blob([ab], { type: 'application/pdf' })
    
    // Create a local blob URL in browser memory. 
    // This bypasses IDM extension interception completely.
    const blobUrl = URL.createObjectURL(blob)
    previewUrl.value = blobUrl
  } catch (err) {
    console.error(err)
    alert(`Failed to load PDF preview: ${err.message}`)
  }
}

const closePreview = () => {
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = null
  previewFilename.value = ''
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  fetchDocs()
})
</script>
