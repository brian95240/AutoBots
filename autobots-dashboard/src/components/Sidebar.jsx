import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Bot, 
  Activity, 
  Users, 
  FileText, 
  Settings,
  ChevronLeft,
  Zap,
  Shield,
  Eye,
  UserCheck,
  Cog
} from 'lucide-react'

const Sidebar = ({ onToggle, darkMode, onToggleDarkMode, systemStatus }) => {
  const location = useLocation()

  const navigationItems = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      description: 'System overview'
    },
    {
      name: 'Bots Overview',
      href: '/bots',
      icon: Bot,
      description: 'Bot status & controls'
    },
    {
      name: 'System Metrics',
      href: '/metrics',
      icon: Activity,
      description: 'Performance monitoring'
    },
    {
      name: 'Affiliates',
      href: '/affiliates',
      icon: Users,
      description: 'GDPR compliance'
    },
    {
      name: 'Operations Log',
      href: '/operations',
      icon: FileText,
      description: 'Activity history'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      description: 'System configuration'
    }
  ]

  const botStatus = [
    { name: 'ScoutBot', icon: Eye, status: 'active', description: 'OCR & Web Scraping' },
    { name: 'SentinelBot', icon: Shield, status: 'active', description: 'Threat Detection' },
    { name: 'AffiliateBot', icon: UserCheck, status: 'active', description: 'GDPR Compliance' },
    { name: 'OperatorBot', icon: Cog, status: 'active', description: 'Vendor Operations' },
    { name: 'ArchitectBot', icon: Zap, status: 'active', description: 'Performance Optimization' }
  ]

  return (
    <motion.div
      initial={{ x: -280 }}
      animate={{ x: 0 }}
      transition={{ duration: 0.3 }}
      className="w-70 h-full bg-sidebar border-r border-sidebar-border flex flex-col"
    >
      {/* Header */}
      <div className="p-6 border-b border-sidebar-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary/70 rounded-xl flex items-center justify-center">
              <Bot className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-sidebar-foreground">AutoBots</h2>
              <p className="text-xs text-sidebar-foreground/60">v1.0.0</p>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onToggle}
            className="p-2 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/80 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-sidebar-foreground/60 uppercase tracking-wider mb-3">
            Navigation
          </h3>
          {navigationItems.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon
            
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `group flex items-center px-3 py-2.5 rounded-lg transition-all duration-200 ${
                    isActive
                      ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-sm'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                  }`
                }
              >
                <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium">{item.name}</div>
                  <div className="text-xs opacity-60">{item.description}</div>
                </div>
                {isActive && (
                  <motion.div
                    layoutId="activeIndicator"
                    className="w-2 h-2 bg-sidebar-primary-foreground rounded-full"
                  />
                )}
              </NavLink>
            )
          })}
        </div>

        {/* Bot Status */}
        <div className="mb-6">
          <h3 className="text-xs font-semibold text-sidebar-foreground/60 uppercase tracking-wider mb-3">
            Bot Status
          </h3>
          <div className="space-y-2">
            {botStatus.map((bot) => {
              const Icon = bot.icon
              return (
                <motion.div
                  key={bot.name}
                  whileHover={{ scale: 1.02 }}
                  className="flex items-center px-3 py-2 rounded-lg bg-sidebar-accent/50 hover:bg-sidebar-accent transition-colors"
                >
                  <Icon className="w-4 h-4 mr-3 text-sidebar-foreground/70" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-sidebar-foreground">{bot.name}</div>
                    <div className="text-xs text-sidebar-foreground/60">{bot.description}</div>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${
                    bot.status === 'active' ? 'bg-green-500' : 
                    bot.status === 'warning' ? 'bg-yellow-500' : 
                    'bg-red-500'
                  } animate-pulse`} />
                </motion.div>
              )
            })}
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-sidebar-border">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-medium text-sidebar-foreground/60">System Status</span>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${
            systemStatus === 'healthy' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
            systemStatus === 'initializing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
            systemStatus === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
            'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
          }`}>
            {systemStatus}
          </div>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onToggleDarkMode}
          className="w-full flex items-center justify-center px-3 py-2 rounded-lg bg-sidebar-accent text-sidebar-accent-foreground hover:bg-sidebar-accent/80 transition-colors"
        >
          {darkMode ? (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Light Mode
            </>
          ) : (
            <>
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
              Dark Mode
            </>
          )}
        </motion.button>
      </div>
    </motion.div>
  )
}

export default Sidebar

