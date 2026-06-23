<template>
  <main class="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 scrollbar-hide transition-colors duration-250">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">Smartphone Inventory</h2>
        <p class="text-zinc-500 dark:text-zinc-400">View and manage device stock, grades, and prices in the database.</p>
      </div>
      
      <div>
        <button 
          @click="openAddModal"
          class="w-full sm:w-auto bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-900 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm flex items-center justify-center gap-2 cursor-pointer"
        >
          <Plus class="w-5 h-5" />
          Add New Device
        </button>
      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Smartphone class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Smartphone class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Total Unique SKUs</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ products.length }}</p>
          <span class="text-sm text-zinc-500 mb-1">items</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Active devices in database</p>
      </div>

      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Package class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Package class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Total Total Stock</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ totalStock }}</p>
          <span class="text-sm text-zinc-500 mb-1">units</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Sum of all inventory levels</p>
      </div>

      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden group transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <AlertCircle class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <AlertCircle class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Low Stock SKUs</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold" :class="lowStockCount > 0 ? 'text-amber-500' : 'text-zinc-900 dark:text-zinc-100'">{{ lowStockCount }}</p>
          <span class="text-sm text-zinc-500 mb-1">items</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Having stock level &le; 2</p>
      </div>
    </div>

    <!-- Filter and Management Section -->
    <div class="w-full">
      <!-- Products Table (Full-Width) -->
      <div class="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col">
        <!-- Filters Bar -->
        <div class="p-5 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/10 flex flex-wrap gap-4 items-center justify-between">
          <div class="flex flex-wrap items-center gap-3 flex-1">
            <div class="relative min-w-[150px]">
              <select 
                v-model="filters.brand"
                class="w-full pl-3 pr-8 py-2 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100"
              >
                <option value="">All Brands</option>
                <option v-for="b in uniqueBrands" :key="b" :value="b">{{ b }}</option>
              </select>
            </div>
            
            <div class="relative min-w-[150px]">
              <select 
                v-model="filters.grade"
                class="w-full pl-3 pr-8 py-2 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100"
              >
                <option value="">All Grades</option>
                <option value="Like New">Like New</option>
                <option value="Grade A">Grade A</option>
                <option value="Grade B">Grade B</option>
                <option value="Grade C+">Grade C+</option>
              </select>
            </div>

            <div class="relative flex-1 max-w-xs">
              <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-zinc-400">
                <Search class="w-4 h-4" />
              </span>
              <input 
                type="text" 
                v-model="filters.search"
                placeholder="Search model or specs..."
                class="w-full pl-9 pr-3 py-2 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100"
              />
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button 
              @click="clearFilters"
              class="px-3.5 py-2 text-xs font-semibold text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>

        <!-- Table Content -->
        <div v-if="isLoading" class="p-20 flex flex-col items-center justify-center space-y-4 flex-1">
          <Loader2 class="w-10 h-10 text-zinc-500 animate-spin" />
          <p class="text-zinc-400 text-sm">Loading inventory list...</p>
        </div>

        <div v-else-if="filteredProducts.length === 0" class="p-20 text-center flex-1">
          <PackageOpen class="w-12 h-12 text-zinc-300 mx-auto mb-4" />
          <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1">No products found</h3>
          <p class="text-xs text-zinc-500">Try adjusting your filters or search keywords.</p>
        </div>

        <div v-else class="overflow-x-auto flex-1">
          <table class="w-full border-collapse text-left">
            <thead>
              <tr class="border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/20 dark:bg-zinc-800/10 text-zinc-400 text-xs font-semibold uppercase tracking-wider">
                <th class="px-6 py-4 hidden sm:table-cell">Brand</th>
                <th class="px-6 py-4">Model & Specs</th>
                <th class="px-6 py-4 hidden md:table-cell">Storage</th>
                <th class="px-6 py-4 hidden sm:table-cell">Grade</th>
                <th class="px-6 py-4">Price (USD)</th>
                <th class="px-6 py-4">Stock Level</th>
                <th class="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800 text-sm">
              <tr 
                v-for="p in filteredProducts" 
                :key="p.id" 
                class="hover:bg-zinc-50/50 hover:dark:bg-zinc-800/20 transition-colors text-zinc-800 dark:text-zinc-200"
              >
                <td class="px-6 py-4 font-semibold hidden sm:table-cell">{{ p.brand }}</td>
                <td class="px-6 py-4 font-medium text-zinc-900 dark:text-zinc-100">
                  <div>{{ p.model }}</div>
                  <div class="flex flex-wrap gap-1.5 mt-1 md:hidden">
                    <span class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] text-zinc-500 dark:text-zinc-400 font-medium sm:hidden">
                      {{ p.brand }}
                    </span>
                    <span class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] font-mono text-zinc-600 dark:text-zinc-300 md:hidden">
                      {{ p.storage }}
                    </span>
                    <span 
                      class="px-1.5 py-0.5 rounded-full text-[10px] font-semibold sm:hidden"
                      :class="{
                        'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400': p.grade === 'Like New',
                        'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400': p.grade === 'Grade A',
                        'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400': p.grade === 'Grade B',
                        'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400': p.grade === 'Grade C+',
                      }"
                    >
                      {{ p.grade }}
                    </span>
                  </div>
                </td>
                <td class="px-6 py-4 hidden md:table-cell"><span class="px-2 py-0.5 rounded-md bg-zinc-100 dark:bg-zinc-800 text-xs font-mono text-zinc-600 dark:text-zinc-300">{{ p.storage }}</span></td>
                <td class="px-6 py-4 hidden sm:table-cell">
                  <span 
                    class="px-2.5 py-0.5 rounded-full text-xs font-semibold"
                    :class="{
                      'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400': p.grade === 'Like New',
                      'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400': p.grade === 'Grade A',
                      'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-400': p.grade === 'Grade B',
                      'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400': p.grade === 'Grade C+',
                    }"
                  >
                    {{ p.grade }}
                  </span>
                </td>
                <td class="px-6 py-4 font-semibold">${{ p.price }}</td>
                <td class="px-6 py-4">
                  <div class="flex items-center gap-2">
                    <span 
                      class="w-2.5 h-2.5 rounded-full"
                      :class="p.stock > 2 ? 'bg-emerald-500' : p.stock > 0 ? 'bg-amber-500 animate-pulse' : 'bg-rose-500'"
                    ></span>
                    <span class="font-medium" :class="p.stock <= 2 ? 'text-amber-600 font-semibold' : ''">{{ p.stock }} units</span>
                  </div>
                </td>
                <td class="px-6 py-4 text-right">
                  <button 
                    @click="editProduct(p)"
                    class="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all inline-flex items-center gap-1 cursor-pointer"
                  >
                    <Edit3 class="w-4 h-4" />
                    <span class="text-xs">Edit</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal Component -->
    <ProductModal 
      :is-open="isModalOpen"
      :product="selectedProduct"
      @close="closeModal"
      @saved="fetchProducts"
    />
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { 
  Smartphone, 
  Package, 
  AlertCircle, 
  Plus, 
  Search, 
  Loader2, 
  Edit3, 
  PackageOpen
} from 'lucide-vue-next'
import ProductModal from '../components/products/ProductModal.vue'

const products = ref([])
const isLoading = ref(true)
const isModalOpen = ref(false)
const selectedProduct = ref(null)

const filters = ref({
  brand: '',
  grade: '',
  search: ''
})

// Load products
const fetchProducts = async () => {
  isLoading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/products')
    if (!res.ok) throw new Error('Failed to fetch products')
    products.value = await res.json()
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchProducts()
})

// Unique brands for filtering
const uniqueBrands = computed(() => {
  const brands = products.value.map(p => p.brand)
  return [...new Set(brands)].sort()
})

// Computed stats
const totalStock = computed(() => {
  return products.value.reduce((sum, p) => sum + p.stock, 0)
})

const lowStockCount = computed(() => {
  return products.value.filter(p => p.stock <= 2).length
})

// Filtered products list
const filteredProducts = computed(() => {
  return products.value.filter(p => {
    const matchesBrand = !filters.value.brand || p.brand === filters.value.brand
    const matchesGrade = !filters.value.grade || p.grade === filters.value.grade
    const searchLower = filters.value.search.toLowerCase()
    const matchesSearch = !filters.value.search || 
                          p.model.toLowerCase().includes(searchLower) || 
                          p.brand.toLowerCase().includes(searchLower) ||
                          p.storage.toLowerCase().includes(searchLower)
    
    return matchesBrand && matchesGrade && matchesSearch
  })
})

const clearFilters = () => {
  filters.value.brand = ''
  filters.value.grade = ''
  filters.value.search = ''
}

const openAddModal = () => {
  selectedProduct.value = null
  isModalOpen.value = true
}

const closeModal = () => {
  isModalOpen.value = false
  selectedProduct.value = null
}

// Edit handler
const editProduct = (product) => {
  selectedProduct.value = product
  isModalOpen.value = true
}
</script>
