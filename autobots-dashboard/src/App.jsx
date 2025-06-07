import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import './App.css'

// Import components
import Sidebar from './components/Sidebar'
import Dashboard from './components/Dashboard'
import BotsOverview from './components/BotsOverview'
import SystemMetrics from './components/SystemMetrics'
import AffiliateManagement from './components/AffiliateManagement'
import OperationsLog from './components/OperationsLog'
import Settings from './components/Settings'

// Import UI components
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [darkMode, setDarkMode] = useState(false)
  const [systemStatus, setSystemStatus] = useState('loading')

  // Initialize dark mode from localStorage
  useEffect(() => {
    const savedDarkMode = localStorage.getItem('darkMode') === 'true'
    setDarkMode(savedDarkMode)
    if (savedDarkMode) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    localStorage.setItem('darkMode', newDarkMode.toString())
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  // Check system status on mount
  useEffect(() => {
    const checkSystemStatus = async () => {
      try {
        const response = await fetch('/api/health')
        if (response.ok) {
          const data = await response.json()
          setSystemStatus(data.bots_initialized ? 'healthy' : 'initializing')
        } else {
          setSystemStatus('error')
        }
      } catch (error) {
        console.error('Failed to check system status:', error)
        setSystemStatus('offline')
      }
    }

    checkSystemStatus()
    
    // Check status every 30 seconds
    const interval = setInterval(checkSystemStatus, 30000)
    return () => clearInterval(interval)
  }, [])

  // Show system status notifications
  useEffect(() => {
    if (systemStatus === 'error') {
      toast.error("System Error", {
        description: "AutoBots system is experiencing issues",
      })
    } else if (systemStatus === 'healthy') {
      toast.success("System Online", {
        description: "All AutoBots are operational",
      })
    }
  }, [systemStatus])

  return (
    <Router>
      <div className={`min-h-screen bg-background text-foreground transition-colors duration-300 ${darkMode ? 'dark' : ''}`}>
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar */}
          <AnimatePresence mode="wait">
            {sidebarOpen && (
              <motion.div
                initial={{ x: -280 }}
                animate={{ x: 0 }}
                exit={{ x: -280 }}
                transition={{ duration: 0.3, ease: "easeInOut" }}
                className="w-70 flex-shrink-0"
              >
                <Sidebar 
                  onToggle={() => setSidebarOpen(!sidebarOpen)}
                  darkMode={darkMode}
                  onToggleDarkMode={toggleDarkMode}
                  systemStatus={systemStatus}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header */}
            <motion.header 
              initial={{ y: -60 }}
              animate={{ y: 0 }}
              transition={{ duration: 0.5 }}
              className="bg-card border-b border-border px-6 py-4 flex items-center justify-between"
            >
              <div className="flex items-center space-x-4">
                {!sidebarOpen && (
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </motion.button>
                )}
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                    AutoBots Control Center
                  </h1>
                  <p className="text-sm text-muted-foreground">
                    Multi-Agent Workflow Engine Dashboard
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* System Status Indicator */}
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    systemStatus === 'healthy' ? 'bg-green-500 animate-pulse' :
                    systemStatus === 'initializing' ? 'bg-yellow-500 animate-pulse' :
                    systemStatus === 'error' ? 'bg-red-500 animate-pulse' :
                    'bg-gray-500'
                  }`} />
                  <span className="text-sm font-medium capitalize">{systemStatus}</span>
                </div>

                {/* Dark Mode Toggle */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={toggleDarkMode}
                  className="p-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
                >
                  {darkMode ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                    </svg>
                  )}
                </motion.button>
              </div>
            </motion.header>

            {/* Main Content Area */}
            <main className="flex-1 overflow-auto bg-background">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="p-6"
              >
                <Routes>
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                  <Route path="/dashboard" element={<Dashboard systemStatus={systemStatus} />} />
                  <Route path="/bots" element={<BotsOverview />} />
                  <Route path="/metrics" element={<SystemMetrics />} />
                  <Route path="/affiliates" element={<AffiliateManagement />} />
                  <Route path="/operations" element={<OperationsLog />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </motion.div>
            </main>
          </div>
        </div>

        {/* Toast Notifications */}
        <Toaster />
      </div>
    </Router>
  )
}

export default App

