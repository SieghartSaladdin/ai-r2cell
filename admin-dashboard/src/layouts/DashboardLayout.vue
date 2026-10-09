<template>
  <div class="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-800 dark:text-zinc-100 flex font-sans overflow-hidden transition-colors duration-250">
    <!-- Mobile Sidebar Backdrop Overlay -->
    <div 
      v-if="isSidebarOpen"
      class="fixed inset-0 bg-black/40 dark:bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity duration-200"
      @click="isSidebarOpen = false"
    ></div>

    <Sidebar :is-open="isSidebarOpen" @close="isSidebarOpen = false" />
    
    <div class="flex-1 flex flex-col relative h-screen overflow-hidden bg-zinc-50 dark:bg-zinc-950 transition-colors duration-250">
      <Navbar @toggle-sidebar="isSidebarOpen = !isSidebarOpen" />
      
      <!-- Main view content will go here based on router -->
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import Navbar from '../components/Navbar.vue'

const isSidebarOpen = ref(false)
</script>

<style>
/* Custom Scrollbar for a sleeker look */
.scrollbar-hide::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.scrollbar-hide::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-hide::-webkit-scrollbar-thumb {
  background: #27272a;
  border-radius: 10px;
}
.scrollbar-hide::-webkit-scrollbar-thumb:hover {
  background: #3f3f46;
}
</style>
