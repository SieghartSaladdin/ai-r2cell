import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  server: {
    // Fixed port (not Vite's default 5173, which other projects often occupy). strictPort makes
    // Vite fail loudly instead of silently moving to another port, so the TUI label stays correct.
    port: 5180,
    strictPort: true,
  },
})
