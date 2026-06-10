import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import { useThemeStore } from './stores/themeStore.js'
import './index.css'

// Initialize theme before React renders
useThemeStore.getState().initTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#16181D',
            color: '#FFFFFF',
            border: '1px solid #262A33',
            borderRadius: '10px',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
          },
          success: { iconTheme: { primary: '#22C55E', secondary: '#0A0A0B' } },
          error: { iconTheme: { primary: '#EF4444', secondary: '#0A0A0B' } },
        }}
      />
    </BrowserRouter>
  </StrictMode>
)
