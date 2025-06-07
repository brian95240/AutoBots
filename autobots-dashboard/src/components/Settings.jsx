import React, { useState, useEffect } from 'react'
import SettingsAPI from '../services/settingsAPI'
import { toast } from 'sonner'
import { 
  Settings as SettingsIcon,
  Bot,
  Bell,
  Shield,
  Database,
  Mail,
  Cpu,
  Activity,
  Clock,
  AlertTriangle,
  Save,
  RotateCcw,
  Eye,
  UserCheck,
  Cog,
  Zap,
  Server,
  Lock,
  Globe,
  Sliders,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Slider } from '@/components/ui/slider'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'

const Settings = () => {
  // Initialize API client
  const settingsAPI = new SettingsAPI()
  
  // State management
  const [activeTab, setActiveTab] = useState('bots')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState(true)
  const [hasChanges, setHasChanges] = useState(false)
  
  // Configuration states
  const [botConfigs, setBotConfigs] = useState({})
  const [alertConfig, setAlertConfig] = useState({})
  const [systemConfig, setSystemConfig] = useState({})
  const [notificationConfig, setNotificationConfig] = useState({})
  const [securityConfig, setSecurityConfig] = useState({})
  
  // Original states for reset functionality
  const [originalConfigs, setOriginalConfigs] = useState({})

  // Load all configurations on component mount
  useEffect(() => {
    loadAllConfigurations()
  }, [])

  const loadAllConfigurations = async () => {
    try {
      setLoading(true)
      
      const [bots, alerts, system, notifications, security] = await Promise.all([
        settingsAPI.getBotConfigs(),
        settingsAPI.getAlertConfig(),
        settingsAPI.getSystemConfig(),
        settingsAPI.getNotificationConfig(),
        settingsAPI.getSecurityConfig()
      ])
      
      setBotConfigs(bots)
      setAlertConfig(alerts)
      setSystemConfig(system)
      setNotificationConfig(notifications)
      setSecurityConfig(security)
      
      // Store original configurations for reset
      setOriginalConfigs({
        bots,
        alerts,
        system,
        notifications,
        security
      })
      
      setHasChanges(false)
      toast.success('Settings loaded successfully')
    } catch (error) {
      console.error('Failed to load configurations:', error)
      toast.error('Failed to load settings: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  const botIcons = {
    scout: Eye,
    sentinel: Shield,
    affiliate: UserCheck,
    operator: Cog,
    architect: Zap
  }

  const botNames = {
    scout: 'ScoutBot',
    sentinel: 'SentinelBot',
    affiliate: 'AffiliateBot',
    operator: 'OperatorBot',
    architect: 'ArchitectBot'
  }

  // Configuration change handlers with API integration
  const handleBotConfigChange = (botId, field, value) => {
    setBotConfigs(prev => ({
      ...prev,
      [botId]: {
        ...prev[botId],
        [field]: value
      }
    }))
    setHasChanges(true)
  }

  const handleAlertConfigChange = (field, value) => {
    setAlertConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  const handleSystemConfigChange = (field, value) => {
    setSystemConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  const handleNotificationConfigChange = (field, value) => {
    setNotificationConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  const handleSecurityConfigChange = (field, value) => {
    setSecurityConfig(prev => ({
      ...prev,
      [field]: value
    }))
    setHasChanges(true)
  }

  // Save all changes to backend
  const handleSave = async () => {
    try {
      setSaving(true)
      
      // Save all configurations in parallel
      const savePromises = []
      
      // Save bot configurations
      Object.keys(botConfigs).forEach(botId => {
        if (JSON.stringify(botConfigs[botId]) !== JSON.stringify(originalConfigs.bots?.[botId])) {
          savePromises.push(settingsAPI.updateBotConfig(botId, botConfigs[botId]))
        }
      })
      
      // Save other configurations
      if (JSON.stringify(alertConfig) !== JSON.stringify(originalConfigs.alerts)) {
        savePromises.push(settingsAPI.updateAlertConfig(alertConfig))
      }
      
      if (JSON.stringify(systemConfig) !== JSON.stringify(originalConfigs.system)) {
        savePromises.push(settingsAPI.updateSystemConfig(systemConfig))
      }
      
      if (JSON.stringify(notificationConfig) !== JSON.stringify(originalConfigs.notifications)) {
        savePromises.push(settingsAPI.updateNotificationConfig(notificationConfig))
      }
      
      if (JSON.stringify(securityConfig) !== JSON.stringify(originalConfigs.security)) {
        savePromises.push(settingsAPI.updateSecurityConfig(securityConfig))
      }
      
      await Promise.all(savePromises)
      
      // Update original configs
      setOriginalConfigs({
        bots: botConfigs,
        alerts: alertConfig,
        system: systemConfig,
        notifications: notificationConfig,
        security: securityConfig
      })
      
      setHasChanges(false)
      toast.success('Settings saved successfully!')
      
    } catch (error) {
      console.error('Failed to save settings:', error)
      toast.error('Failed to save settings: ' + error.message)
    } finally {
      setSaving(false)
    }
  }

  // Reset all changes
  const handleReset = () => {
    setBotConfigs(originalConfigs.bots || {})
    setAlertConfig(originalConfigs.alerts || {})
    setSystemConfig(originalConfigs.system || {})
    setNotificationConfig(originalConfigs.notifications || {})
    setSecurityConfig(originalConfigs.security || {})
    setHasChanges(false)
    toast.info('Settings reset to last saved state')
  }

  // Test connection functionality
  const testConnection = async (type) => {
    try {
      const result = await settingsAPI.testConnection(type)
      if (result.success) {
        toast.success(result.message)
      } else {
        toast.error(result.message)
      }
    } catch (error) {
      toast.error(`Connection test failed: ${error.message}`)
    }
  }

  // Export/Import functionality
  const exportSettings = async () => {
    try {
      const settings = await settingsAPI.exportSettings()
      const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `autobots-settings-${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('Settings exported successfully')
    } catch (error) {
      toast.error(`Export failed: ${error.message}`)
    }
  }

  const importSettings = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    try {
      const text = await file.text()
      const settings = JSON.parse(text)
      await settingsAPI.importSettings(settings)
      await loadAllConfigurations() // Reload all configurations
      toast.success('Settings imported successfully')
    } catch (error) {
      toast.error(`Import failed: ${error.message}`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center space-x-2">
          <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <span>Loading settings...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Configure your AutoBots system parameters and monitoring preferences
          </p>
        </div>
        
        {/* Save Controls */}
        <div className="flex items-center space-x-3">
          {hasChanges && (
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                Unsaved Changes
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                disabled={saving}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset
              </Button>
            </div>
          )}
          
          <Button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="bg-green-600 hover:bg-green-700"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Settings Tabs */}
      <div>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="bots" className="flex items-center space-x-2">
              <Bot className="w-4 h-4" />
              <span>Bots</span>
            </TabsTrigger>
            <TabsTrigger value="alerts" className="flex items-center space-x-2">
              <Bell className="w-4 h-4" />
              <span>Alerts</span>
            </TabsTrigger>
            <TabsTrigger value="system" className="flex items-center space-x-2">
              <Server className="w-4 h-4" />
              <span>System</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center space-x-2">
              <Mail className="w-4 h-4" />
              <span>Notifications</span>
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center space-x-2">
              <Lock className="w-4 h-4" />
              <span>Security</span>
            </TabsTrigger>
          </TabsList>

          {/* Bot Configuration Tab */}
          <TabsContent value="bots" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {Object.entries(botConfigs).map(([botId, config]) => {
                const Icon = botIcons[botId]
                const botName = botNames[botId]
                
                return (
                  <div key={botId}>
                    <Card className="border-border">
                      <CardHeader>
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center">
                            <Icon className="w-5 h-5 text-primary-foreground" />
                          </div>
                          <div>
                            <CardTitle className="text-lg">{botName}</CardTitle>
                            <CardDescription>Configure {botName} parameters</CardDescription>
                          </div>
                          <div className="ml-auto">
                            <Switch
                              checked={config.enabled}
                              onCheckedChange={(checked) => handleBotConfigChange(botId, 'enabled', checked)}
                            />
                          </div>
                        </div>
                      </CardHeader>
                      
                      <CardContent className="space-y-4">
                        {botId === 'scout' && (
                          <>
                            <div className="space-y-2">
                              <Label>OCR Accuracy Threshold (%)</Label>
                              <div className="px-3">
                                <Slider
                                  value={[config.ocrAccuracyThreshold]}
                                  onValueChange={([value]) => handleBotConfigChange(botId, 'ocrAccuracyThreshold', value)}
                                  max={100}
                                  min={50}
                                  step={1}
                                  className="w-full"
                                />
                                <div className="flex justify-between text-sm text-muted-foreground mt-1">
                                  <span>50%</span>
                                  <span>{config.ocrAccuracyThreshold}%</span>
                                  <span>100%</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Spider API Limit</Label>
                                <Input
                                  type="number"
                                  value={config.spiderApiLimit}
                                  onChange={(e) => handleBotConfigChange(botId, 'spiderApiLimit', parseInt(e.target.value))}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Processing Timeout (s)</Label>
                                <Input
                                  type="number"
                                  value={config.processingTimeout}
                                  onChange={(e) => handleBotConfigChange(botId, 'processingTimeout', parseInt(e.target.value))}
                                />
                              </div>
                            </div>
                          </>
                        )}
                        
                        {botId === 'sentinel' && (
                          <>
                            <div className="space-y-2">
                              <Label>Threat Detection Sensitivity (%)</Label>
                              <div className="px-3">
                                <Slider
                                  value={[config.threatSensitivity]}
                                  onValueChange={([value]) => handleBotConfigChange(botId, 'threatSensitivity', value)}
                                  max={100}
                                  min={10}
                                  step={5}
                                  className="w-full"
                                />
                                <div className="flex justify-between text-sm text-muted-foreground mt-1">
                                  <span>Low</span>
                                  <span>{config.threatSensitivity}%</span>
                                  <span>High</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Response Time Threshold (ms)</Label>
                                <Input
                                  type="number"
                                  value={config.responseTimeThreshold}
                                  onChange={(e) => handleBotConfigChange(botId, 'responseTimeThreshold', parseInt(e.target.value))}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Alert Level</Label>
                                <Select
                                  value={config.alertLevel}
                                  onValueChange={(value) => handleBotConfigChange(botId, 'alertLevel', value)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="info">Info</SelectItem>
                                    <SelectItem value="warning">Warning</SelectItem>
                                    <SelectItem value="error">Error</SelectItem>
                                    <SelectItem value="critical">Critical</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </>
                        )}
                        
                        {botId === 'affiliate' && (
                          <>
                            <div className="flex items-center justify-between">
                              <Label>GDPR Strict Mode</Label>
                              <Switch
                                checked={config.gdprStrictMode}
                                onCheckedChange={(checked) => handleBotConfigChange(botId, 'gdprStrictMode', checked)}
                              />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Email Template</Label>
                                <Select
                                  value={config.emailTemplate}
                                  onValueChange={(value) => handleBotConfigChange(botId, 'emailTemplate', value)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="default">Default</SelectItem>
                                    <SelectItem value="formal">Formal</SelectItem>
                                    <SelectItem value="friendly">Friendly</SelectItem>
                                    <SelectItem value="minimal">Minimal</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="space-y-2">
                                <Label>Purge Schedule</Label>
                                <Select
                                  value={config.purgeSchedule}
                                  onValueChange={(value) => handleBotConfigChange(botId, 'purgeSchedule', value)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="daily">Daily</SelectItem>
                                    <SelectItem value="weekly">Weekly</SelectItem>
                                    <SelectItem value="monthly">Monthly</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </div>
                          </>
                        )}
                        
                        {botId === 'operator' && (
                          <>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Sync Interval (min)</Label>
                                <Input
                                  type="number"
                                  value={config.syncInterval}
                                  onChange={(e) => handleBotConfigChange(botId, 'syncInterval', parseInt(e.target.value))}
                                />
                              </div>
                              <div className="space-y-2">
                                <Label>Retry Attempts</Label>
                                <Input
                                  type="number"
                                  value={config.retryAttempts}
                                  onChange={(e) => handleBotConfigChange(botId, 'retryAttempts', parseInt(e.target.value))}
                                />
                              </div>
                            </div>
                            
                            <div className="flex items-center justify-between">
                              <Label>Batch Processing</Label>
                              <Switch
                                checked={config.batchProcessing}
                                onCheckedChange={(checked) => handleBotConfigChange(botId, 'batchProcessing', checked)}
                              />
                            </div>
                          </>
                        )}
                        
                        {botId === 'architect' && (
                          <>
                            <div className="space-y-2">
                              <Label>Performance Threshold (%)</Label>
                              <div className="px-3">
                                <Slider
                                  value={[config.performanceThreshold]}
                                  onValueChange={([value]) => handleBotConfigChange(botId, 'performanceThreshold', value)}
                                  max={100}
                                  min={50}
                                  step={5}
                                  className="w-full"
                                />
                                <div className="flex justify-between text-sm text-muted-foreground mt-1">
                                  <span>50%</span>
                                  <span>{config.performanceThreshold}%</span>
                                  <span>100%</span>
                                </div>
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4">
                              <div className="space-y-2">
                                <Label>Scaling Rules</Label>
                                <Select
                                  value={config.scalingRules}
                                  onValueChange={(value) => handleBotConfigChange(botId, 'scalingRules', value)}
                                >
                                  <SelectTrigger>
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="auto">Auto</SelectItem>
                                    <SelectItem value="manual">Manual</SelectItem>
                                    <SelectItem value="scheduled">Scheduled</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              <div className="space-y-2">
                                <Label>Monitoring Interval (min)</Label>
                                <Input
                                  type="number"
                                  value={config.monitoringInterval}
                                  onChange={(e) => handleBotConfigChange(botId, 'monitoringInterval', parseInt(e.target.value))}
                                />
                              </div>
                            </div>
                          </>
                        )}
                        
                        <Separator />
                        
                        <div className="flex items-center justify-between">
                          <Label>Auto Restart on Failure</Label>
                          <Switch
                            checked={config.autoRestart || config.autoBlock || config.autoNotification || config.batchProcessing || config.autoOptimize}
                            onCheckedChange={(checked) => {
                              const field = botId === 'scout' ? 'autoRestart' :
                                          botId === 'sentinel' ? 'autoBlock' :
                                          botId === 'affiliate' ? 'autoNotification' :
                                          botId === 'operator' ? 'batchProcessing' :
                                          'autoOptimize'
                              handleBotConfigChange(botId, field, checked)
                            }}
                          />
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                )
              })}
            </div>
          </TabsContent>

          {/* Alert Configuration Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* System Thresholds */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Activity className="w-5 h-5" />
                    <span>System Thresholds</span>
                  </CardTitle>
                  <CardDescription>Configure alert thresholds for system metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* CPU Thresholds */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">CPU Usage</Label>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Warning Threshold</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.cpuWarning}%</span>
                        </div>
                        <Slider
                          value={[alertConfig.cpuWarning]}
                          onValueChange={([value]) => handleAlertConfigChange('cpuWarning', value)}
                          max={100}
                          min={10}
                          step={5}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Critical Threshold</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.cpuCritical}%</span>
                        </div>
                        <Slider
                          value={[alertConfig.cpuCritical]}
                          onValueChange={([value]) => handleAlertConfigChange('cpuCritical', value)}
                          max={100}
                          min={alertConfig.cpuWarning}
                          step={5}
                          className="w-full"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Memory Thresholds */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Memory Usage</Label>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Warning Threshold</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.memoryWarning}%</span>
                        </div>
                        <Slider
                          value={[alertConfig.memoryWarning]}
                          onValueChange={([value]) => handleAlertConfigChange('memoryWarning', value)}
                          max={100}
                          min={10}
                          step={5}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Critical Threshold</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.memoryCritical}%</span>
                        </div>
                        <Slider
                          value={[alertConfig.memoryCritical]}
                          onValueChange={([value]) => handleAlertConfigChange('memoryCritical', value)}
                          max={100}
                          min={alertConfig.memoryWarning}
                          step={5}
                          className="w-full"
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Response Time Thresholds */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Response Time</Label>
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Warning Threshold (ms)</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.responseTimeWarning}ms</span>
                        </div>
                        <Slider
                          value={[alertConfig.responseTimeWarning]}
                          onValueChange={([value]) => handleAlertConfigChange('responseTimeWarning', value)}
                          max={1000}
                          min={50}
                          step={25}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <Label className="text-sm">Critical Threshold (ms)</Label>
                          <span className="text-sm text-muted-foreground">{alertConfig.responseTimeCritical}ms</span>
                        </div>
                        <Slider
                          value={[alertConfig.responseTimeCritical]}
                          onValueChange={([value]) => handleAlertConfigChange('responseTimeCritical', value)}
                          max={2000}
                          min={alertConfig.responseTimeWarning}
                          step={25}
                          className="w-full"
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Alert Behavior */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Bell className="w-5 h-5" />
                    <span>Alert Behavior</span>
                  </CardTitle>
                  <CardDescription>Configure how alerts are handled and delivered</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Alert Channels */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Alert Channels</Label>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Mail className="w-4 h-4" />
                          <Label>Email Alerts</Label>
                        </div>
                        <Switch
                          checked={alertConfig.emailEnabled}
                          onCheckedChange={(checked) => handleAlertConfigChange('emailEnabled', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Globe className="w-4 h-4" />
                          <Label>Slack Notifications</Label>
                        </div>
                        <Switch
                          checked={alertConfig.slackEnabled}
                          onCheckedChange={(checked) => handleAlertConfigChange('slackEnabled', checked)}
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Alert Frequency */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Alert Frequency</Label>
                    <Select
                      value={alertConfig.alertFrequency}
                      onValueChange={(value) => handleAlertConfigChange('alertFrequency', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="immediate">Immediate</SelectItem>
                        <SelectItem value="batched_5min">Batched (5 min)</SelectItem>
                        <SelectItem value="batched_15min">Batched (15 min)</SelectItem>
                        <SelectItem value="batched_hourly">Batched (Hourly)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator />

                  {/* Escalation */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Escalation</Label>
                    <div className="space-y-2">
                      <Label className="text-sm">Escalation Delay (minutes)</Label>
                      <Input
                        type="number"
                        value={alertConfig.escalationDelay}
                        onChange={(e) => handleAlertConfigChange('escalationDelay', parseInt(e.target.value))}
                        min={1}
                        max={60}
                      />
                    </div>
                  </div>

                  <Separator />

                  {/* Quiet Hours */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-base font-medium">Quiet Hours</Label>
                      <Switch
                        checked={alertConfig.quietHours}
                        onCheckedChange={(checked) => handleAlertConfigChange('quietHours', checked)}
                      />
                    </div>
                    {alertConfig.quietHours && (
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label className="text-sm">Start Time</Label>
                          <Input
                            type="time"
                            value={alertConfig.quietStart}
                            onChange={(e) => handleAlertConfigChange('quietStart', e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label className="text-sm">End Time</Label>
                          <Input
                            type="time"
                            value={alertConfig.quietEnd}
                            onChange={(e) => handleAlertConfigChange('quietEnd', e.target.value)}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* System Configuration Tab */}
          <TabsContent value="system" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Performance Settings */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Cpu className="w-5 h-5" />
                    <span>Performance Settings</span>
                  </CardTitle>
                  <CardDescription>Configure system performance parameters</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>API Rate Limit (req/min)</Label>
                      <Input
                        type="number"
                        value={systemConfig.apiRateLimit}
                        onChange={(e) => handleSystemConfigChange('apiRateLimit', parseInt(e.target.value))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>DB Connection Pool</Label>
                      <Input
                        type="number"
                        value={systemConfig.dbConnectionPool}
                        onChange={(e) => handleSystemConfigChange('dbConnectionPool', parseInt(e.target.value))}
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Cache Enabled</Label>
                    <Switch
                      checked={systemConfig.cacheEnabled}
                      onCheckedChange={(checked) => handleSystemConfigChange('cacheEnabled', checked)}
                    />
                  </div>

                  {systemConfig.cacheEnabled && (
                    <div className="space-y-2">
                      <Label>Cache TTL (seconds)</Label>
                      <Input
                        type="number"
                        value={systemConfig.cacheTtl}
                        onChange={(e) => handleSystemConfigChange('cacheTtl', parseInt(e.target.value))}
                      />
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Session Timeout (seconds)</Label>
                      <Input
                        type="number"
                        value={systemConfig.sessionTimeout}
                        onChange={(e) => handleSystemConfigChange('sessionTimeout', parseInt(e.target.value))}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>JWT Expiration (seconds)</Label>
                      <Input
                        type="number"
                        value={systemConfig.jwtExpiration}
                        onChange={(e) => handleSystemConfigChange('jwtExpiration', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* System Modes */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Sliders className="w-5 h-5" />
                    <span>System Modes</span>
                  </CardTitle>
                  <CardDescription>Control system operational modes</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label>Log Level</Label>
                    <Select
                      value={systemConfig.logLevel}
                      onValueChange={(value) => handleSystemConfigChange('logLevel', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="debug">Debug</SelectItem>
                        <SelectItem value="info">Info</SelectItem>
                        <SelectItem value="warning">Warning</SelectItem>
                        <SelectItem value="error">Error</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <Label>Debug Mode</Label>
                    <Switch
                      checked={systemConfig.debugMode}
                      onCheckedChange={(checked) => handleSystemConfigChange('debugMode', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <Label>Maintenance Mode</Label>
                      <p className="text-sm text-muted-foreground">Temporarily disable system access</p>
                    </div>
                    <Switch
                      checked={systemConfig.maintenanceMode}
                      onCheckedChange={(checked) => handleSystemConfigChange('maintenanceMode', checked)}
                    />
                  </div>

                  <Separator />

                  <div className="flex items-center justify-between">
                    <Label>Backup Enabled</Label>
                    <Switch
                      checked={systemConfig.backupEnabled}
                      onCheckedChange={(checked) => handleSystemConfigChange('backupEnabled', checked)}
                    />
                  </div>

                  {systemConfig.backupEnabled && (
                    <div className="space-y-2">
                      <Label>Backup Interval</Label>
                      <Select
                        value={systemConfig.backupInterval}
                        onValueChange={(value) => handleSystemConfigChange('backupInterval', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hourly">Hourly</SelectItem>
                          <SelectItem value="daily">Daily</SelectItem>
                          <SelectItem value="weekly">Weekly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <Label>Compression Enabled</Label>
                    <Switch
                      checked={systemConfig.compressionEnabled}
                      onCheckedChange={(checked) => handleSystemConfigChange('compressionEnabled', checked)}
                    />
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Email Configuration */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Mail className="w-5 h-5" />
                    <span>Email Configuration</span>
                  </CardTitle>
                  <CardDescription>Configure email notification settings</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label>Email Recipients</Label>
                    <Textarea
                      placeholder="Enter email addresses, one per line"
                      value={notificationConfig.emailRecipients.join('\n')}
                      onChange={(e) => handleNotificationConfigChange('emailRecipients', e.target.value.split('\n').filter(email => email.trim()))}
                      rows={3}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>SMTP Server</Label>
                      <Input
                        value={notificationConfig.smtpServer}
                        onChange={(e) => handleNotificationConfigChange('smtpServer', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>SMTP Port</Label>
                      <Input
                        type="number"
                        value={notificationConfig.smtpPort}
                        onChange={(e) => handleNotificationConfigChange('smtpPort', parseInt(e.target.value))}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label>Email User</Label>
                    <Input
                      type="email"
                      value={notificationConfig.emailUser}
                      onChange={(e) => handleNotificationConfigChange('emailUser', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Email Password</Label>
                    <Input
                      type="password"
                      value={notificationConfig.emailPassword}
                      onChange={(e) => handleNotificationConfigChange('emailPassword', e.target.value)}
                      placeholder="App password for email account"
                    />
                  </div>

                  <Button
                    variant="outline"
                    onClick={() => testConnection('Email')}
                    className="w-full"
                  >
                    Test Email Connection
                  </Button>
                </CardContent>
              </Card>

              {/* Notification Types */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Bell className="w-5 h-5" />
                    <span>Notification Types</span>
                  </CardTitle>
                  <CardDescription>Choose which events trigger notifications</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {Object.entries(notificationConfig.notificationTypes).map(([type, enabled]) => (
                    <div key={type} className="flex items-center justify-between">
                      <div className="space-y-1">
                        <Label className="capitalize">
                          {type.replace(/([A-Z])/g, ' $1').trim()}
                        </Label>
                        <p className="text-sm text-muted-foreground">
                          {type === 'systemAlerts' && 'Critical system alerts and errors'}
                          {type === 'botStatus' && 'Bot start, stop, and status changes'}
                          {type === 'performanceIssues' && 'Performance degradation alerts'}
                          {type === 'securityEvents' && 'Security threats and breaches'}
                          {type === 'maintenanceUpdates' && 'Scheduled maintenance notifications'}
                        </p>
                      </div>
                      <Switch
                        checked={enabled}
                        onCheckedChange={(checked) => 
                          handleNotificationConfigChange('notificationTypes', {
                            ...notificationConfig.notificationTypes,
                            [type]: checked
                          })
                        }
                      />
                    </div>
                  ))}

                  <Separator />

                  {/* Slack Configuration */}
                  <div className="space-y-4">
                    <Label className="text-base font-medium">Slack Integration</Label>
                    <div className="space-y-2">
                      <Label>Slack Webhook URL</Label>
                      <Input
                        type="url"
                        value={notificationConfig.slackWebhook}
                        onChange={(e) => handleNotificationConfigChange('slackWebhook', e.target.value)}
                        placeholder="https://hooks.slack.com/services/..."
                      />
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => testConnection('Slack')}
                      disabled={!notificationConfig.slackWebhook}
                      className="w-full"
                    >
                      Test Slack Connection
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Authentication & Access */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Shield className="w-5 h-5" />
                    <span>Authentication & Access</span>
                  </CardTitle>
                  <CardDescription>Configure security and access controls</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1">
                      <Label>Two-Factor Authentication</Label>
                      <p className="text-sm text-muted-foreground">Require 2FA for all users</p>
                    </div>
                    <Switch
                      checked={securityConfig.twoFactorEnabled}
                      onCheckedChange={(checked) => handleSecurityConfigChange('twoFactorEnabled', checked)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Password Policy</Label>
                    <Select
                      value={securityConfig.passwordPolicy}
                      onValueChange={(value) => handleSecurityConfigChange('passwordPolicy', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="basic">Basic (8+ characters)</SelectItem>
                        <SelectItem value="strong">Strong (12+ chars, mixed case, numbers)</SelectItem>
                        <SelectItem value="enterprise">Enterprise (16+ chars, symbols required)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Session Security</Label>
                    <Select
                      value={securityConfig.sessionSecurity}
                      onValueChange={(value) => handleSecurityConfigChange('sessionSecurity', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low (30 days)</SelectItem>
                        <SelectItem value="medium">Medium (7 days)</SelectItem>
                        <SelectItem value="high">High (24 hours)</SelectItem>
                        <SelectItem value="strict">Strict (1 hour)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>IP Whitelist</Label>
                    <Textarea
                      placeholder="Enter IP addresses or ranges, one per line"
                      value={securityConfig.ipWhitelist}
                      onChange={(e) => handleSecurityConfigChange('ipWhitelist', e.target.value)}
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Security Features */}
              <Card className="border-border">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Lock className="w-5 h-5" />
                    <span>Security Features</span>
                  </CardTitle>
                  <CardDescription>Advanced security and monitoring features</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label>API Key Rotation</Label>
                    <Select
                      value={securityConfig.apiKeyRotation}
                      onValueChange={(value) => handleSecurityConfigChange('apiKeyRotation', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="quarterly">Quarterly</SelectItem>
                        <SelectItem value="manual">Manual Only</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Encryption Level</Label>
                    <Select
                      value={securityConfig.encryptionLevel}
                      onValueChange={(value) => handleSecurityConfigChange('encryptionLevel', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="aes128">AES-128</SelectItem>
                        <SelectItem value="aes256">AES-256</SelectItem>
                        <SelectItem value="chacha20">ChaCha20</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator />

                  <div className="space-y-4">
                    <Label className="text-base font-medium">Security Monitoring</Label>
                    
                    <div className="flex items-center justify-between">
                      <Label>Audit Logging</Label>
                      <Switch
                        checked={securityConfig.auditLogging}
                        onCheckedChange={(checked) => handleSecurityConfigChange('auditLogging', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label>Access Logging</Label>
                      <Switch
                        checked={securityConfig.accessLogging}
                        onCheckedChange={(checked) => handleSecurityConfigChange('accessLogging', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label>Brute Force Protection</Label>
                      <Switch
                        checked={securityConfig.bruteForceProtection}
                        onCheckedChange={(checked) => handleSecurityConfigChange('bruteForceProtection', checked)}
                      />
                    </div>

                    <div className="flex items-center justify-between">
                      <Label>Rate Limiting</Label>
                      <Switch
                        checked={securityConfig.rateLimiting}
                        onCheckedChange={(checked) => handleSecurityConfigChange('rateLimiting', checked)}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default Settings

