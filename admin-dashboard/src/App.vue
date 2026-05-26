<template>
  <div class="min-h-screen bg-gray-100 flex font-sans">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r border-gray-200">
      <div class="h-16 flex items-center px-6 border-b border-gray-200">
        <h1 class="text-xl font-bold text-gray-800">ai-r2cell Admin</h1>
      </div>
      <nav class="p-4 space-y-2">
        <a href="#" class="block px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg">Dashboard</a>
        <a href="#" class="block px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg">Knowledge Base</a>
        <a href="#" class="block px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 rounded-lg">Logs</a>
      </nav>
    </aside>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col">
      <!-- Topbar -->
      <header class="h-16 bg-white border-b border-gray-200 flex items-center px-8 justify-between">
        <h2 class="text-xl font-semibold text-gray-800">Dashboard Overview</h2>
        <div class="flex items-center gap-4">
          <span class="text-sm font-medium text-gray-600">Admin</span>
          <div class="w-8 h-8 rounded-full bg-blue-500 text-white flex flex-col items-center justify-center font-bold">
            A
          </div>
        </div>
      </header>

      <!-- Stats / Content -->
      <main class="p-8 flex-1 overflow-y-auto">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 class="text-sm font-medium text-gray-500 mb-1">Total Users</h3>
            <p class="text-3xl font-bold text-gray-900">1,248</p>
          </div>
          <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 class="text-sm font-medium text-gray-500 mb-1">Active Sessions</h3>
            <p class="text-3xl font-bold text-gray-900">42</p>
          </div>
          <div class="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 class="text-sm font-medium text-gray-500 mb-1">System Status</h3>
            <p class="text-3xl font-bold text-green-600">Online</p>
          </div>
        </div>

        <div class="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">Recent Server Info</h3>
          <div class="p-4 border border-gray-100 rounded-lg bg-gray-50 text-sm text-gray-600 font-mono">
            {{ serverInfo }}
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const serverInfo = ref('Loading server status...')

onMounted(async () => {
  try {
    const res = await fetch('http://localhost:8000/')
    const data = await res.json()
    serverInfo.value = JSON.stringify(data, null, 2)
  } catch (err) {
    serverInfo.value = 'Failed to connect to FastAPI backend. Is it running?'
  }
})
</script>
