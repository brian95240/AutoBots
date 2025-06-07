import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Bot, 
  Play, 
  Pause, 
  RotateCcw, 
  Settings,
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Eye,
  Shield,
  UserCheck,
  Cog,
  Zap
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Switch } from '@/components/ui/switch'

const BotsOverview = () => {
  const [bots, setBots] = useState([
    {
      id: 'scout',
      name: 'ScoutBot',
      description: 'OCR processing and web scraping with spider.cloud integration',
      icon: Eye,
      status: 'active',
      uptime: '99.8%',
      operations: 1247,
      lastOperation: '2 minutes ago',
      performance: 96.5,
      features: ['OCR Processing', 'Web Scraping', 'Data Extraction', 'Spider.cloud API'],
      metrics: {
        accuracy: 99.5,
        avgProcessingTime: 1.2,
        successRate: 98.7
      }
    },
    {
      id: 'sentinel',
      name: 'SentinelBot',
      description: 'Real-time threat detection and security monitoring',
      icon: Shield,
      status: 'active',
      uptime: '99.9%',
      operations: 3456,
      lastOperation: '30 seconds ago',
      performance: 98.2,
      features: ['Threat Detection', 'Pattern Analysis', 'Real-time Monitoring', 'Security Alerts'],
      metrics: {
        detectionTime: 32.5,
        threatsBlocked: 127,
        falsePositives: 0.3
      }
    },
    {
      id: 'affiliate',
      name: 'AffiliateBot',
      description: 'GDPR compliance automation with zero manual intervention',
      icon: UserCheck,
      status: 'active',
      uptime: '100%',
      operations: 892,
      lastOperation: '5 minutes ago',
      performance: 100,
      features: ['GDPR Compliance', 'Consent Management', 'Data Purging', 'Email Notifications'],
      metrics: {
        complianceRate: 100,
        autoActions: 45,
        responseTime: 0.8
      }
    },
    {
      id: 'operator',
      name: 'OperatorBot',
      description: 'Vendor operations and workflow automation',
      icon: Cog,
      status: 'active',
      uptime: '99.7%',
      operations: 2134,
      lastOperation: '1 minute ago',
      performance: 94.8,
      features: ['Vendor Integration', 'Product Sync', 'Price Updates', 'Inventory Management'],
      metrics: {
        syncSuccess: 97.2,
        vendorsManaged: 12,
        avgSyncTime: 45.3
      }
    },
    {
      id: 'architect',
      name: 'ArchitectBot',
      description: 'System architecture and performance optimization',
      icon: Zap,
      status: 'active',
      uptime: '99.9%',
      operations: 567,
      lastOperation: '3 minutes ago',
      performance: 97.1,
      features: ['Performance Monitoring', 'Auto-optimization', 'Resource Management', 'Scaling'],
      metrics: {
        optimizations: 23,
        performanceGain: 15.2,
        resourceSaved: 8.7
      }
    }
  ])

  const [selectedBot, setSelectedBot] = useState(null)

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'error': return 'text-red-500'
      case 'inactive': return 'text-gray-500'
      default: return 'text-gray-500'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return CheckCircle
      case 'warning': return AlertTriangle
      case 'error': return XCircle
      case 'inactive': return Pause
      default: return Pause
    }
  }

  const handleBotAction = async (botId, action) => {
    // Simulate API call
    console.log(`${action} bot ${botId}`)
    
    setBots(prevBots => 
      prevBots.map(bot => 
        bot.id === botId 
          ? { ...bot, status: action === 'start' ? 'active' : action === 'stop' ? 'inactive' : bot.status }
          : bot
      )
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold text-foreground mb-2">Bots Overview</h1>
        <p className="text-muted-foreground">
          Monitor and control your AutoBots multi-agent system
        </p>
      </motion.div>

      {/* Bots Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {bots.map((bot, index) => {
          const Icon = bot.icon
          const StatusIcon = getStatusIcon(bot.status)
          
          return (
            <motion.div
              key={bot.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="border-border hover:shadow-lg transition-all duration-300 cursor-pointer"
                    onClick={() => setSelectedBot(selectedBot === bot.id ? null : bot.id)}>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                        <Icon className="w-6 h-6 text-primary-foreground" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{bot.name}</CardTitle>
                        <div className="flex items-center space-x-2">
                          <StatusIcon className={`w-4 h-4 ${getStatusColor(bot.status)}`} />
                          <Badge variant={bot.status === 'active' ? 'default' : 'secondary'}>
                            {bot.status}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">{bot.performance}%</div>
                      <div className="text-xs text-muted-foreground">Performance</div>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-4">
                  <CardDescription className="text-sm">
                    {bot.description}
                  </CardDescription>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium">Uptime</div>
                      <div className="text-muted-foreground">{bot.uptime}</div>
                    </div>
                    <div>
                      <div className="font-medium">Operations</div>
                      <div className="text-muted-foreground">{bot.operations.toLocaleString()}</div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Performance</span>
                      <span>{bot.performance}%</span>
                    </div>
                    <Progress value={bot.performance} className="h-2" />
                  </div>
                  
                  <div className="text-xs text-muted-foreground">
                    Last operation: {bot.lastOperation}
                  </div>
                  
                  {/* Expanded Details */}
                  {selectedBot === bot.id && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.3 }}
                      className="border-t border-border pt-4 space-y-4"
                    >
                      {/* Features */}
                      <div>
                        <h4 className="font-medium mb-2">Features</h4>
                        <div className="flex flex-wrap gap-2">
                          {bot.features.map((feature, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      {/* Metrics */}
                      <div>
                        <h4 className="font-medium mb-2">Key Metrics</h4>
                        <div className="space-y-2 text-sm">
                          {Object.entries(bot.metrics).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                              <span className="font-medium">
                                {typeof value === 'number' ? 
                                  (value < 10 ? `${value}s` : value < 100 ? `${value}%` : value.toLocaleString()) 
                                  : value}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Controls */}
                      <div className="flex space-x-2 pt-2">
                        <Button 
                          size="sm" 
                          variant={bot.status === 'active' ? 'secondary' : 'default'}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleBotAction(bot.id, bot.status === 'active' ? 'stop' : 'start')
                          }}
                        >
                          {bot.status === 'active' ? (
                            <>
                              <Pause className="w-4 h-4 mr-1" />
                              Pause
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4 mr-1" />
                              Start
                            </>
                          )}
                        </Button>
                        
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleBotAction(bot.id, 'restart')
                          }}
                        >
                          <RotateCcw className="w-4 h-4 mr-1" />
                          Restart
                        </Button>
                        
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            // Navigate to bot settings
                          }}
                        >
                          <Settings className="w-4 h-4 mr-1" />
                          Config
                        </Button>
                      </div>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* System Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
      >
        <Card className="border-border">
          <CardHeader>
            <CardTitle>System Controls</CardTitle>
            <CardDescription>
              Global controls for the AutoBots system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button 
                onClick={() => bots.forEach(bot => handleBotAction(bot.id, 'start'))}
                className="bg-green-600 hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                Start All Bots
              </Button>
              
              <Button 
                variant="secondary"
                onClick={() => bots.forEach(bot => handleBotAction(bot.id, 'stop'))}
              >
                <Pause className="w-4 h-4 mr-2" />
                Pause All Bots
              </Button>
              
              <Button 
                variant="outline"
                onClick={() => bots.forEach(bot => handleBotAction(bot.id, 'restart'))}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Restart System
              </Button>
              
              <Button variant="outline">
                <Activity className="w-4 h-4 mr-2" />
                System Health Check
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default BotsOverview

