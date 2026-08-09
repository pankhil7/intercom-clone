import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  build: {
    lib: {
      entry: resolve(__dirname, 'src/widget.ts'),
      name: 'InboxWidget',
      fileName: 'widget',
      formats: ['iife'],
    },
    rollupOptions: {
      output: {
        // socket.io-client is bundled — no external deps needed
      },
    },
    outDir: 'dist',
    minify: true,
    sourcemap: false,
  },
  define: {
    'process.env.NODE_ENV': '"production"',
  },
})
