<template>
  <div class="flex-1 flex h-[calc(100vh-64px)] lg:h-[calc(100vh-80px)] overflow-hidden bg-zinc-50 dark:bg-zinc-950 text-zinc-800 dark:text-zinc-100 relative font-sans transition-colors duration-250">
    
    <!-- Mobile Backdrop Overlay when drawers are open -->
    <div 
      v-if="(showSessionsDrawer || showLogsDrawer) && !lgScreen"
      class="fixed inset-0 bg-black/40 dark:bg-black/60 z-30 backdrop-blur-sm transition-opacity duration-200"
      @click="closeAllDrawers"
    ></div>

    <!-- Left Sidebar: Thread Selector (Modular) -->
    <SessionSidebar
      :threads="threads"
      :selected-thread="selectedThread"
      :is-refreshing="isRefreshingThreads"
      :background-executing="backgroundExecuting"
      :lg-screen="lgScreen"
      :is-open="showSessionsDrawer"
      @select-thread="selectThreadAndClose"
      @refresh-threads="fetchThreads"
      @close="closeAllDrawers"
    />

    <!-- Center Pane: Graph Canvas Area -->
    <div class="flex-1 h-full relative border-r border-zinc-200 dark:border-zinc-900 flex flex-col min-w-0">
      
      <!-- Top Left Controls Overlay: Reload & Connection Info -->
      <div class="absolute top-4 left-4 z-10 flex flex-wrap gap-2 pointer-events-auto">
        <button 
          @click="loadGraphStructure" 
          class="flex items-center gap-2 px-3 py-1.5 bg-white/90 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-800 rounded-xl text-xs font-semibold tracking-wide transition-all shadow-md active:scale-95 text-zinc-600 dark:text-zinc-300 hover:text-zinc-800 dark:hover:text-zinc-100 backdrop-blur-sm cursor-pointer"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isReloading }" />
          Reset Layout
        </button>
        <div 
          class="flex items-center gap-2 px-3 py-1.5 bg-white/90 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 rounded-xl text-xs font-semibold shadow-md text-zinc-600 dark:text-zinc-300 backdrop-blur-sm"
        >
          <span class="flex h-2 w-2 relative">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Live: <span class="text-emerald-500 dark:text-emerald-400 font-bold uppercase">{{ wsStatus }}</span>
        </div>
      </div>

      <!-- Top Right Controls Overlay: Canvas interactions (Modular) -->
      <CanvasControls
        :is-interactive="isInteractive"
        @zoom-in="zoomIn"
        @zoom-out="zoomOut"
        @fit-view="fitView({ padding: 0.2 })"
        @toggle-interactive="isInteractive = !isInteractive"
      />

      <!-- Canvas container -->
      <div class="flex-1 h-full relative bg-zinc-50 dark:bg-zinc-950 transition-colors duration-250">
        
        <!-- Empty State (No Session Selected) -->
        <div v-if="!selectedThread" class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-zinc-50/95 dark:bg-zinc-950/95 z-20 transition-colors duration-250 p-6 text-center">
          <GitBranch class="w-12 h-12 text-zinc-300 dark:text-zinc-800 animate-pulse mb-1" />
          <p class="text-sm font-semibold text-zinc-400 dark:text-zinc-500">Select a thread session to inspect graph flow</p>
          <button 
            v-if="!lgScreen"
            @click="showSessionsDrawer = true"
            class="mt-3 px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-xs font-bold shadow-md hover:shadow-lg active:scale-95 transition-all flex items-center gap-2 cursor-pointer"
          >
            <MessageSquare class="w-4 h-4" />
            Open Sessions List
          </button>
        </div>

        <VueFlow
          v-model="elements"
          :fit-view-on-init="true"
          :default-zoom="1.0"
          :min-zoom="0.3"
          :max-zoom="3"
          :nodes-draggable="isInteractive"
          :nodes-connectable="false"
          :elements-selectable="isInteractive"
          :pan-on-drag="isInteractive"
          :zoom-on-scroll="isInteractive"
          :zoom-on-pinch="isInteractive"
          :zoom-on-double-click="isInteractive"
          class="h-full vue-flow-container"
        >
          <!-- Custom Premium Nodes -->
          <template #node-custom="{ data }">
            <div 
              class="px-5 py-4 rounded-2xl border flex flex-col gap-2 min-w-[210px] shadow-lg transition-all duration-300 backdrop-blur-md relative"
              :class="[
                data.active 
                  ? 'bg-emerald-50/90 dark:bg-emerald-950/20 border-emerald-500 ring-2 ring-emerald-500/20 shadow-emerald-500/10 dark:shadow-emerald-500/10 scale-105' 
                  : 'bg-white dark:bg-zinc-900/90 border-zinc-200 dark:border-zinc-800 hover:border-zinc-300 dark:hover:border-zinc-700'
              ]"
            >
              <!-- Connection Handles -->
              <Handle type="target" :position="Position.Top" class="custom-handle" />
              
              <!-- Content Header -->
              <div class="flex items-center gap-3 w-full">
                <!-- Icon badge -->
                <div 
                  class="p-2 rounded-xl shrink-0 transition-colors duration-300"
                  :class="[
                    data.active 
                      ? 'bg-emerald-500/20 dark:bg-emerald-400/20 text-emerald-600 dark:text-emerald-400' 
                      : data.bgIconClass + ' ' + data.colorClass
                  ]"
                >
                  <component :is="data.icon" class="w-4.5 h-4.5" />
                </div>
                
                <!-- Label & Type -->
                <div class="flex flex-col min-w-0 flex-1">
                  <span class="text-[9px] font-bold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
                    {{ data.type }}
                  </span>
                  <span class="text-sm font-extrabold text-zinc-800 dark:text-zinc-100 truncate">
                    {{ data.label }}
                  </span>
                </div>
              </div>

              <!-- Active Status Indicator -->
              <div v-if="data.active" class="flex items-center gap-1.5 mt-1 self-start">
                <span class="flex h-2 w-2 relative">
                  <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span class="text-[9.5px] font-semibold text-emerald-600 dark:text-emerald-400">Processing...</span>
              </div>

              <!-- Tools List if present -->
              <div v-if="data.toolsList && data.toolsList.length" class="mt-2 pt-2 border-t border-zinc-100 dark:border-zinc-800/80 flex flex-col gap-0.5 text-[11px] text-zinc-600 dark:text-zinc-400">
                <div v-for="tool in data.toolsList" :key="tool" class="flex items-center gap-2 py-1 border-b last:border-0 border-zinc-100/50 dark:border-zinc-800/40">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></span>
                  <span class="truncate font-medium">{{ tool }}</span>
                </div>
              </div>
              
              <Handle type="source" :position="Position.Bottom" class="custom-handle" />
            </div>
          </template>
        </VueFlow>
      </div>
    </div>

    <!-- Right Sidebar: Detail Inspector Panel (Modular) -->
    <LogInspector
      :active-logs="activeLogs"
      :selected-thread="selectedThread"
      :lg-screen="lgScreen"
      :is-open="showLogsDrawer"
      @close="closeAllDrawers"
    />

    <!-- Mobile Floating Navigation Dock (visible only on screens < 1024px) -->
    <div 
      v-if="!lgScreen"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-30 flex gap-3 bg-white/95 dark:bg-zinc-900/95 border border-zinc-200 dark:border-zinc-800 rounded-full px-5 py-3 shadow-2xl backdrop-blur-md"
    >
      <button 
        @click="showSessionsDrawer = true" 
        class="flex items-center gap-2 text-xs font-bold text-zinc-600 dark:text-zinc-300 px-2 py-0.5 hover:text-zinc-900 dark:hover:text-white transition-all cursor-pointer"
      >
        <MessageSquare class="w-4.5 h-4.5 text-zinc-500" />
        Sessions
      </button>
      <div class="w-px h-5 bg-zinc-200 dark:bg-zinc-800 self-center"></div>
      <button 
        @click="showLogsDrawer = true" 
        class="flex items-center gap-2 text-xs font-bold text-zinc-600 dark:text-zinc-300 px-2 py-0.5 hover:text-zinc-900 dark:hover:text-white transition-all cursor-pointer"
      >
        <Activity class="w-4.5 h-4.5 text-zinc-500" />
        Inspector
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import axios from 'axios'
import { 
  Activity, 
  RefreshCw, 
  GitBranch,
  MessageSquare,
  Sparkles,
  Database,
  Inbox,
  CheckCircle,
  Cpu
} from 'lucide-vue-next'

import SessionSidebar from '../components/graph/SessionSidebar.vue'
import LogInspector from '../components/graph/LogInspector.vue'
import CanvasControls from '../components/graph/CanvasControls.vue'

const threads = ref([])
const selectedThread = ref(null)
const logsByThread = ref({}) // { [threadId]: Array }
const activeNodesByThread = ref({}) // { [threadId]: Set }
const backgroundExecuting = ref({}) // { [threadId]: Boolean }

// Theme & Responsive States
const isDark = ref(false)
const lgScreen = ref(true)
const showSessionsDrawer = ref(false)
const showLogsDrawer = ref(false)
const isInteractive = ref(true)

const wsStatus = ref('connecting')
const isReloading = ref(false)
const isRefreshingThreads = ref(false)
let wsClient = null
let themeObserver = null

const { fitView, zoomIn, zoomOut } = useVueFlow()

// Raw elements templates
const rawNodesList = ref([])
const rawEdgesList = ref([])

// Map internal nodes to clean readable names
const nodeNameMapping = {
  '__start__': 'Receive Message',
  '__end__': 'Send Message',
  'tools': 'R2Cell Tool Suite',
  'call_model': 'AI Model Call'
}

const closeAllDrawers = () => {
  showSessionsDrawer.value = false
  showLogsDrawer.value = false
}

const selectThreadAndClose = (threadId) => {
  selectThread(threadId)
  closeAllDrawers()
}

// Media Query Listener to track screen changes dynamically
const handleResize = () => {
  lgScreen.value = window.innerWidth >= 1024
  if (lgScreen.value) {
    closeAllDrawers()
  }
}

// Listen to HTML class attribute changes to sync Vue Flow styling with the app's Dark/Light mode toggle
const checkDarkMode = () => {
  isDark.value = document.documentElement.classList.contains('dark')
}

// Fetch active thread list from database
const fetchThreads = async () => {
  isRefreshingThreads.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/chat/threads')
    threads.value = res.data.map(t => t && typeof t === 'object' ? t.thread_id : t)
    if (threads.value.length > 0 && !selectedThread.value) {
      selectThread(threads.value[0])
    }
  } catch (err) {
    console.error('Failed to fetch threads:', err)
  } finally {
    isRefreshingThreads.value = false
  }
}

// Get logs of the currently active session
const activeLogs = computed(() => {
  if (!selectedThread.value) return []
  return logsByThread.value[selectedThread.value] || []
})

// Elements composed for Vue Flow (nodes + edges) based on selected thread
const elements = computed(() => {
  if (!selectedThread.value) return []

  const currentActiveNodes = activeNodesByThread.value[selectedThread.value] || new Set()

  const positionMap = {
    '__start__': { x: 250, y: 50 },
    'call_model': { x: 250, y: 185 },
    'tools': { x: 100, y: 320 },
    '__end__': { x: 400, y: 320 }
  }

  const formattedNodes = rawNodesList.value.map(node => {
    const pos = positionMap[node.id] || { x: 250, y: 200 }
    let typeLabel = 'System Link'
    let icon = Cpu
    let colorClass = 'text-zinc-500 dark:text-zinc-400'
    let bgIconClass = 'bg-zinc-100 dark:bg-zinc-800'
    let toolsList = null
    
    if (node.id === '__start__') {
      typeLabel = 'Input Message'
      icon = Inbox
      colorClass = 'text-blue-500 dark:text-blue-400'
      bgIconClass = 'bg-blue-500/10 dark:bg-blue-500/20'
    } else if (node.id === '__end__') {
      typeLabel = 'Output Response'
      icon = CheckCircle
      colorClass = 'text-purple-500 dark:text-purple-400'
      bgIconClass = 'bg-purple-500/10 dark:bg-purple-500/20'
    } else if (node.id === 'tools') {
      typeLabel = 'Agent Tool Suite'
      icon = Database
      colorClass = 'text-amber-500 dark:text-amber-400'
      bgIconClass = 'bg-amber-500/10 dark:bg-amber-500/20'
      toolsList = ["Knowledge Base RAG", "Product Stock Query", "COD Booking Engine", "Bandung Maps Location"]
    } else if (node.id === 'call_model') {
      typeLabel = 'Generator (LLM)'
      icon = Sparkles
      colorClass = 'text-emerald-500 dark:text-emerald-400'
      bgIconClass = 'bg-emerald-500/10 dark:bg-emerald-500/20'
    }

    const isNodeActive = currentActiveNodes.has(node.id)

    return {
      id: node.id,
      type: 'custom',
      data: {
        label: nodeNameMapping[node.id] || node.name,
        type: typeLabel,
        active: isNodeActive,
        icon: icon,
        colorClass: colorClass,
        bgIconClass: bgIconClass,
        toolsList: toolsList
      },
      position: pos
    }
  })

  // Format edges (highlighting edge as animated/green if target node is running)
  const formattedEdges = rawEdgesList.value.map(edge => {
    const isTargetRunning = currentActiveNodes.has(edge.target)
    
    // Choose connection line stroke based on dark/light mode dynamically
    const strokeColor = isTargetRunning 
      ? '#10b981' 
      : (isDark.value ? '#3f3f46' : '#d4d4d8')

    return {
      id: `e-${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: isTargetRunning,
      style: { 
        stroke: strokeColor, 
        strokeWidth: isTargetRunning ? 4 : 2.5,
        transition: 'stroke 0.3s, stroke-width 0.3s'
      }
    }
  })

  return [...formattedNodes, ...formattedEdges]
})

// Load the graph structure from the backend
const loadGraphStructure = async () => {
  isReloading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/graph/structure')
    rawNodesList.value = res.data.nodes
    rawEdgesList.value = res.data.edges
    
    setTimeout(() => {
      fitView({ padding: 0.2 })
    }, 120)

  } catch (err) {
    console.error('Failed to load graph structure:', err)
  } finally {
    isReloading.value = false
  }
}

// Select a session thread to view
const selectThread = (threadId) => {
  selectedThread.value = threadId
  
  if (!logsByThread.value[threadId]) {
    logsByThread.value[threadId] = []
  }
  if (!activeNodesByThread.value[threadId]) {
    activeNodesByThread.value[threadId] = new Set()
  }

  setTimeout(() => {
    fitView({ padding: 0.2 })
  }, 120)
}

// Connect to WebSocket channel
const connectWS = () => {
  const wsUrl = window.location.protocol === 'https:'
    ? `wss://${window.location.host}/api/graph/ws`
    : `ws://${window.location.hostname}:8000/api/graph/ws`

  wsClient = new WebSocket(wsUrl)

  wsClient.onopen = () => {
    wsStatus.value = 'online'
  }

  wsClient.onclose = () => {
    wsStatus.value = 'offline'
    setTimeout(connectWS, 3000) // Reconnect loop
  }

  wsClient.onerror = () => {
    wsStatus.value = 'error'
  }

  wsClient.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.event === 'node_execution') {
        const { node, status, thread_id } = data

        if (!threads.value.includes(thread_id)) {
          threads.value.push(thread_id)
        }

        if (!logsByThread.value[thread_id]) {
          logsByThread.value[thread_id] = []
        }
        if (!activeNodesByThread.value[thread_id]) {
          activeNodesByThread.value[thread_id] = new Set()
        }

        // Add log entry
        const cleanNodeName = nodeNameMapping[node] || node
        logsByThread.value[thread_id].unshift({
          time: new Date().toLocaleTimeString(),
          nodeName: cleanNodeName,
          status: status
        })

        if (logsByThread.value[thread_id].length > 20) {
          logsByThread.value[thread_id].pop()
        }

        // Update node active sets
        if (status === 'running') {
          activeNodesByThread.value[thread_id].add(node)
          backgroundExecuting.value[thread_id] = true
        } else {
          activeNodesByThread.value[thread_id].delete(node)
          
          if (activeNodesByThread.value[thread_id].size === 0) {
            backgroundExecuting.value[thread_id] = false
          }
        }
      }
    } catch (err) {
      console.error('WebSocket message parsing error:', err)
    }
  }
}

onMounted(() => {
  // Sync states
  checkDarkMode()
  handleResize()
  window.addEventListener('resize', handleResize)

  // Observe theme updates in Navbar / body toggle
  themeObserver = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'class') {
        checkDarkMode()
      }
    })
  })
  themeObserver.observe(document.documentElement, { attributes: true })

  loadGraphStructure()
  fetchThreads()
  connectWS()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (themeObserver) {
    themeObserver.disconnect()
  }
  if (wsClient) {
    wsClient.close()
  }
})
</script>

<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';

/* Custom Dotted Background Grid synchronized with dark/light themes */
.vue-flow-container {
  background-color: var(--bg-color) !important;
  background-image: radial-gradient(var(--dot-color) 1.5px, transparent 1.5px) !important;
  background-size: 24px 24px !important;
  transition: background-color 0.25s ease, background-image 0.25s ease !important;
}

:root {
  --bg-color: #fafafa;
  --dot-color: #e4e4e7;
}

.dark {
  --bg-color: #09090b;
  --dot-color: #222227;
}

.vue-flow__panel.credits {
  display: none !important;
}

.vue-flow__transformationpane {
  transition: transform 0.12s ease-out;
}

/* Custom Connection Handle styling for a clean Figma look */
.custom-handle {
  width: 10px !important;
  height: 10px !important;
  background-color: #ffffff !important;
  border: 2px solid #a1a1aa !important;
  border-radius: 50% !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  transition: all 0.2s ease !important;
}

.dark .custom-handle {
  background-color: #18181b !important;
  border-color: #3f3f46 !important;
}

.custom-handle:hover {
  transform: scale(1.3) !important;
  border-color: #10b981 !important;
}

/* Custom flowing line dash animation for active pathways */
.vue-flow__edge.animated .vue-flow__edge-path {
  stroke-dasharray: 6;
  animation: vue-flow__dash-animation 0.75s linear infinite !important;
}

@keyframes vue-flow__dash-animation {
  from {
    stroke-dashoffset: 24;
  }
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes pulseGlow {
  0%, 100% {
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);
  }
  50% {
    box-shadow: 0 0 25px rgba(16, 185, 129, 0.4);
  }
}

.shadow-emerald-500\/10 {
  animation: pulseGlow 1.6s infinite ease-in-out;
}
</style>
