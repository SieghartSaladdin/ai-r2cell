<template>
  <header class="h-16 lg:h-20 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md border-b border-zinc-200 dark:border-zinc-800 flex items-center px-4 lg:px-10 justify-between sticky top-0 z-10 transition-colors duration-250">
    <div class="flex items-center gap-2 sm:gap-3 flex-grow max-w-xs sm:max-w-md mr-2">
      <!-- Hamburger Menu Button visible only on mobile -->
      <button 
        @click="$emit('toggle-sidebar')" 
        class="lg:hidden p-2 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors shrink-0 cursor-pointer"
        title="Toggle Menu"
      >
        <Menu class="w-5 h-5" />
      </button>

      <div class="flex items-center gap-2 bg-zinc-50 dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 px-2.5 py-1.5 sm:px-3 sm:py-2 rounded-xl w-full transition-all focus-within:border-zinc-400 dark:focus-within:border-zinc-700 focus-within:ring-1 focus-within:ring-zinc-300 dark:focus-within:ring-zinc-800">
        <Search class="w-4 h-4 text-zinc-400 dark:text-zinc-500 shrink-0" />
        <input type="text" placeholder="Search cell signatures..." class="bg-transparent border-none outline-none text-xs sm:text-sm w-full text-zinc-800 dark:text-zinc-300 placeholder-zinc-400 dark:placeholder-zinc-500" />
      </div>
    </div>

    <!-- Theme Toggle -->
    <button 
      @click="toggleTheme" 
      class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-200 transition-all cursor-pointer shadow-sm flex items-center justify-center"
      title="Toggle Light/Dark Theme"
    >
      <Sun v-if="isDark" class="w-5 h-5" />
      <Moon v-else class="w-5 h-5" />
    </button>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search, Sun, Moon, Menu } from 'lucide-vue-next'

const isDark = ref(true)

defineEmits(['toggle-sidebar'])

const toggleTheme = () => {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

onMounted(() => {
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'light') {
    isDark.value = false
    document.documentElement.classList.remove('dark')
  } else {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
})
</script>
