<template>
  <main class="flex-1 overflow-y-auto p-6 lg:p-10 space-y-8 scrollbar-hide transition-colors duration-250">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h2 class="text-3xl font-bold text-zinc-900 dark:text-zinc-100 mb-2">COD Meetup Bookings</h2>
        <p class="text-zinc-500 dark:text-zinc-400">View and manage customer Cash-on-Delivery appointments scheduled via WhatsApp.</p>
      </div>
      
      <div>
        <button 
          @click="fetchBookings"
          class="w-full sm:w-auto border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm flex items-center justify-center gap-2 cursor-pointer"
        >
          <RefreshCw :class="{ 'animate-spin': isLoading }" class="w-4 h-4" />
          Refresh List
        </button>
      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <!-- Total Bookings -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden transition-all duration-250">
        <div class="absolute top-0 right-0 p-4 opacity-5">
          <Calendar class="w-16 h-16 text-zinc-400" />
        </div>
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-zinc-50 dark:bg-zinc-800 flex items-center justify-center border border-zinc-200 dark:border-zinc-700/60">
            <Calendar class="w-5 h-5 text-zinc-500 dark:text-zinc-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Total Bookings</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-zinc-900 dark:text-zinc-100">{{ bookings.length }}</p>
          <span class="text-sm text-zinc-500 mb-1">meetups</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">All recorded COD requests</p>
      </div>

      <!-- Pending -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden transition-all duration-250">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center border border-amber-200 dark:border-amber-500/20">
            <Clock class="w-5 h-5 text-amber-600 dark:text-amber-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Pending Validation</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-amber-600">{{ pendingCount }}</p>
          <span class="text-sm text-zinc-500 mb-1">meetups</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Awaiting customer confirmation</p>
      </div>

      <!-- Confirmed -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden transition-all duration-250">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center border border-blue-200 dark:border-blue-500/20">
            <CheckCircle2 class="w-5 h-5 text-blue-600 dark:text-blue-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Confirmed Meetups</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-blue-600">{{ confirmedCount }}</p>
          <span class="text-sm text-zinc-500 mb-1">scheduled</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Scheduled for delivery/pickup</p>
      </div>

      <!-- Completed -->
      <div class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm relative overflow-hidden transition-all duration-250">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center border border-emerald-200 dark:border-emerald-500/20">
            <CheckCircle2 class="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <h3 class="text-sm font-medium text-zinc-500 dark:text-zinc-400">Completed Sales</h3>
        </div>
        <div class="flex items-end gap-2">
          <p class="text-4xl font-bold text-emerald-600">{{ completedCount }}</p>
          <span class="text-sm text-zinc-500 mb-1">deals</span>
        </div>
        <p class="text-xs text-zinc-400 dark:text-zinc-500 mt-2">Paid and products delivered</p>
      </div>
    </div>

    <!-- Bookings Explorer -->
    <div v-if="isLoading" class="p-20 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col items-center justify-center space-y-4">
      <Loader2 class="w-10 h-10 text-zinc-500 animate-spin" />
      <p class="text-zinc-400 text-sm">Loading bookings list...</p>
    </div>

    <div v-else-if="bookings.length === 0" class="p-20 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm text-center">
      <Calendar class="w-12 h-12 text-zinc-300 mx-auto mb-4" />
      <h3 class="text-sm font-semibold text-zinc-900 dark:text-zinc-100 mb-1">No bookings found</h3>
      <p class="text-xs text-zinc-500">Bookings scheduled by the AI assistant will show up here.</p>
    </div>

    <div v-else class="space-y-4">
      <div 
        v-for="b in bookings" 
        :key="b.id" 
        class="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col lg:flex-row lg:items-center justify-between gap-6 transition-all duration-250 hover:shadow-md"
      >
        <!-- Booking Core Details -->
        <div class="space-y-4 flex-1">
          <div class="flex flex-wrap items-center gap-3">
            <span class="text-xs font-mono text-zinc-400 dark:text-zinc-500 font-bold uppercase">Booking ID: #{{ b.id }}</span>
            <span 
              class="px-2.5 py-0.5 rounded-full text-xs font-semibold"
              :class="{
                'bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400': b.status === 'Pending',
                'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400': b.status === 'Confirmed',
                'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400': b.status === 'Completed',
                'bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400': b.status === 'Cancelled',
              }"
            >
              {{ b.status }}
            </span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Customer -->
            <div>
              <h4 class="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-1">Customer</h4>
              <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{{ b.customer_name }}</p>
              <p class="text-xs text-zinc-500 font-mono">{{ b.customer_phone }}</p>
            </div>

            <!-- Device specs & price -->
            <div>
              <h4 class="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-1">Selected Device</h4>
              <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{{ b.model_storage_grade }}</p>
              <p class="text-sm font-bold text-zinc-900 dark:text-zinc-100 mt-0.5">${{ b.price }} USD</p>
            </div>

            <!-- Meetup Schedule & Location -->
            <div>
              <h4 class="text-xs font-semibold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider mb-1">Meetup Details</h4>
              <p class="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{{ b.appointment_date }} @ {{ b.appointment_time }}</p>
              <p class="text-xs text-zinc-500 truncate" :title="b.location">{{ b.location }}</p>
            </div>
          </div>
        </div>

        <!-- Action / Status Management -->
        <div class="border-t lg:border-t-0 lg:border-l border-zinc-100 dark:border-zinc-800 pt-4 lg:pt-0 lg:pl-6 flex flex-col sm:flex-row items-center gap-3">
          <div class="w-full lg:w-44">
            <label class="block lg:hidden text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-1.5">Change Status</label>
            <select 
              :value="b.status"
              @change="updateStatus(b.id, $event.target.value)"
              class="w-full px-3 py-2 rounded-xl text-sm border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-zinc-100 cursor-pointer"
            >
              <option value="Pending">Pending</option>
              <option value="Confirmed">Confirmed</option>
              <option value="Completed">Completed</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { 
  Calendar, 
  Clock, 
  CheckCircle2, 
  Loader2, 
  RefreshCw 
} from 'lucide-vue-next'

const bookings = ref([])
const isLoading = ref(true)

const fetchBookings = async () => {
  isLoading.value = true
  try {
    const res = await fetch('http://localhost:8000/api/bookings')
    if (!res.ok) throw new Error('Failed to fetch bookings')
    bookings.value = await res.json()
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchBookings()
})

// Counts
const pendingCount = computed(() => {
  return bookings.value.filter(b => b.status === 'Pending').length
})

const confirmedCount = computed(() => {
  return bookings.value.filter(b => b.status === 'Confirmed').length
})

const completedCount = computed(() => {
  return bookings.value.filter(b => b.status === 'Completed').length
})

// Update status PATCH handler
const updateStatus = async (bookingId, newStatus) => {
  try {
    const res = await fetch(`http://localhost:8000/api/bookings/${bookingId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        status: newStatus
      })
    })
    
    if (!res.ok) throw new Error('Failed to update status')
    
    // Update local list state
    const index = bookings.value.findIndex(b => b.id === bookingId)
    if (index !== -1) {
      const updated = await res.json()
      bookings.value[index] = updated
    }
  } catch (error) {
    console.error(error)
    alert('Failed to update booking status. Please try again.')
  }
}
</script>
