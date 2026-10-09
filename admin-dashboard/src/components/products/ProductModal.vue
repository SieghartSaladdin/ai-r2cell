<template>
  <!-- Add/Edit Modal Overlay -->
  <Transition
    enter-active-class="transition duration-200 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition duration-150 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div @click="$emit('close')" class="absolute inset-0 bg-zinc-950/40 backdrop-blur-xs transition-opacity"></div>
      
      <!-- Modal Card -->
      <div 
        class="relative bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl p-6 w-full max-w-lg overflow-y-auto max-h-[90vh] transform flex flex-col z-10 cursor-grab active:cursor-grabbing"
        :class="{ 'select-none': isDragging }"
        :style="{ transform: `translate(${offsetX}px, ${offsetY}px)` }"
        @mousedown="onMouseDown"
      >
        <!-- Close Button -->
        <button 
          @click="$emit('close')" 
          class="absolute top-4 right-4 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>

        <h3 class="text-xl font-bold text-zinc-900 dark:text-zinc-100 mb-1 flex items-center gap-2">
          <Edit3 v-if="form.isEditing" class="w-5 h-5 text-zinc-500" />
          <Plus v-else class="w-5 h-5 text-zinc-500" />
          {{ form.isEditing ? 'Edit Product Details' : 'Add New Inventory' }}
        </h3>
        <p class="text-xs text-zinc-500 mb-6">
          {{ form.isEditing ? 'Modify price and stock level of an existing grade combination.' : 'Create a brand new device or stock configuration.' }}
        </p>

        <form @submit.prevent="submitForm" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Brand</label>
            <input 
              type="text" 
              v-model="form.brand"
              required
              :disabled="form.isEditing"
              placeholder="e.g., Apple, Samsung, Google"
              class="w-full px-3.5 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 disabled:opacity-50"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Model Name</label>
            <input 
              type="text" 
              v-model="form.model"
              required
              :disabled="form.isEditing"
              placeholder="e.g., iPhone 15 Pro Max"
              class="w-full px-3.5 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 disabled:opacity-50"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Storage</label>
              <input 
                type="text" 
                v-model="form.storage"
                required
                :disabled="form.isEditing"
                placeholder="e.g., 256 GB, 128 GB"
                class="w-full px-3.5 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 disabled:opacity-50"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Grade</label>
              <select 
                v-model="form.grade"
                required
                :disabled="form.isEditing"
                class="w-full px-3 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 disabled:opacity-50"
              >
                <option value="Like New">Like New</option>
                <option value="Grade A">Grade A</option>
                <option value="Grade B">Grade B</option>
                <option value="Grade C+">Grade C+</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Price (USD)</label>
              <input 
                type="number" 
                v-model.number="form.price"
                required
                min="1"
                placeholder="e.g., 999"
                class="w-full px-3.5 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Stock Level</label>
              <input 
                type="number" 
                v-model.number="form.stock"
                required
                min="0"
                placeholder="e.g., 10"
                class="w-full px-3.5 py-2.5 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100"
              />
            </div>
          </div>

          <div class="flex items-center gap-3 pt-4">
            <button 
              type="button"
              @click="$emit('close')"
              class="flex-1 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800/50 text-zinc-700 dark:text-zinc-300 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer text-center"
            >
              Cancel
            </button>
            <button 
              type="submit"
              :disabled="isSubmitting"
              class="flex-1 bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Loader2 v-if="isSubmitting" class="w-4 h-4 animate-spin" />
              {{ form.isEditing ? 'Update Stock' : 'Create Record' }}
            </button>
          </div>
        </form>

        <!-- Feedback Messages -->
        <p v-if="formMessage.content" :class="formMessage.isError ? 'text-rose-500' : 'text-emerald-500'" class="text-xs font-semibold mt-4 text-center">
          {{ formMessage.content }}
        </p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { Plus, Edit3, X, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    required: true
  },
  product: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

const form = ref({
  isEditing: false,
  brand: '',
  model: '',
  storage: '',
  grade: 'Like New',
  price: null,
  stock: null
})

const formMessage = ref({
  content: '',
  isError: false
})

const isSubmitting = ref(false)

const offsetX = ref(0)
const offsetY = ref(0)
const isDragging = ref(false)
let startX = 0
let startY = 0

const onMouseDown = (event) => {
  if (event.button !== 0) return
  if (event.target.closest('button, input, select, textarea, label')) return
  
  isDragging.value = true
  startX = event.clientX - offsetX.value
  startY = event.clientY - offsetY.value
  
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

const onMouseMove = (event) => {
  if (!isDragging.value) return
  offsetX.value = event.clientX - startX
  offsetY.value = event.clientY - startY
}

const onMouseUp = () => {
  isDragging.value = false
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', onMouseUp)
})

const resetForm = () => {
  form.value = {
    isEditing: false,
    brand: '',
    model: '',
    storage: '',
    grade: 'Like New',
    price: null,
    stock: null
  }
  formMessage.value = { content: '', isError: false }
  offsetX.value = 0
  offsetY.value = 0
}

watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    offsetX.value = 0
    offsetY.value = 0
    if (props.product) {
      form.value = {
        isEditing: true,
        brand: props.product.brand,
        model: props.product.model,
        storage: props.product.storage,
        grade: props.product.grade,
        price: props.product.price,
        stock: props.product.stock
      }
    } else {
      resetForm()
    }
  } else {
    resetForm()
  }
}, { immediate: true })

watch(() => props.product, (newProduct) => {
  if (props.isOpen) {
    if (newProduct) {
      form.value = {
        isEditing: true,
        brand: newProduct.brand,
        model: newProduct.model,
        storage: newProduct.storage,
        grade: newProduct.grade,
        price: newProduct.price,
        stock: newProduct.stock
      }
    } else {
      resetForm()
    }
  }
})

const submitForm = async () => {
  isSubmitting.value = true
  formMessage.value = { content: '', isError: false }
  
  try {
    const res = await fetch('http://localhost:8000/api/products', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        brand: form.value.brand.trim(),
        model: form.value.model.trim(),
        storage: form.value.storage.trim(),
        grade: form.value.grade,
        price: form.value.price,
        stock: form.value.stock
      })
    })
    
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Failed to save product')
    }
    
    formMessage.value = {
      content: form.value.isEditing ? 'Product stock updated successfully!' : 'New product SKU added successfully!',
      isError: false
    }
    
    emit('saved')
    emit('close')
  } catch (error) {
    formMessage.value = {
      content: error.message || 'Database error occurred.',
      isError: true
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>
