import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, 
  Bot, 
  Users, 
  FileText, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Shield,
  Eye,
  UserCheck,
  Cog
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

const Dashboard = ({ systemStatus }) => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)

  // Mock data for demonstration
  const mockMetrics = {
    system_status: {
      performance_score: 94.5,
      metrics: {
        cpu_usage: { value: 45.2, component: 'system' },
        memory_usage: { value: 62.8, component: 'system' },
        threat_detection_time: { value: 32.5, component: 'sentinel' },
        api_response_time: { value: 125.3, component: 'api' }
      },
      alerts: []
    },
    recent_operations: [
      { id: 1, operation_type: 'product_sync', bot_name: 'OperatorBot', vendor: 'amazon', status: 'completed', created_at: '2024-01-15T10:30:00Z' },
      { id: 2, operation_type: 'threat_analysis', bot_name: 'SentinelBot', vendor: 'system', status: 'completed', created_at: '2024-01-15T10:25:00Z' },
      { id: 3, operation_type: 'ocr_processing', bot_name: 'ScoutBot', vendor: 'spider', status: 'running', created_at: '2024-01-15T10:20:00Z' },
      { id: 4, operation_type: 'gdpr_compliance', bot_name: 'AffiliateBot', vendor: 'system', status: 'completed', created_at: '2024-01-15T10:15:00Z' },
      { id: 5, operation_type: 'performance_optimization', bot_name: 'ArchitectBot', vendor: 'system', status: 'completed', created_at: '2024-01-15T10:10:00Z' }
    ],
    affiliate_stats: {
      total_affiliates: 156,
      active_affiliates: 142,
      consented_affiliates: 156,
      compliance_rate: 100
    }
  }

  // Performance data for charts
  const performanceData = [
    { time: '00:00', cpu: 35, memory: 45, response: 120 },
    { time: '04:00', cpu: 28, memory: 42, response: 115 },
    { time: '08:00', cpu: 52, memory: 68, response: 145 },
    { time: '12:00', cpu: 45, memory: 62, response: 125 },
    { time: '16:00', cpu: 38, memory: 55, response: 130 },
    { time: '20:00', cpu: 42, memory: 58, response: 135 }
  ]

  const botActivityData = [
    { name: 'ScoutBot', operations: 45, success: 42 },
    { name: 'SentinelBot', operations: 38, success: 38 },
    { name: 'AffiliateBot', operations: 23, success: 23 },
    { name: 'OperatorBot', operations: 67, success: 64 },
    { name: 'ArchitectBot', operations: 12, success: 12 }
  ]

  const threatData = [
    { name: 'Clean', value: 85, color: '#10b981' },
    { name: 'Suspicious', value: 12, color: '#f59e0b' },
    { name: 'Threats', value: 3, color: '#ef4444' }
  ]

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        // In production, this would fetch from the API
        // const response = await fetch('/api/dashboard/metrics')
        // const data = await response.json()
        
        // For now, use mock data
        setTimeout(() => {
          setMetrics(mockMetrics)
          setLoading(false)
        }, 1000)
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
        setMetrics(mockMetrics)
        setLoading(false)
      }
    }

    fetchMetrics()
    
    // Refresh metrics every 30 seconds
    const interval = setInterval(fetchMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full"
        />
      </div>
    )
  }

  const performanceScore = metrics?.system_status?.performance_score || 0
  const cpuUsage = metrics?.system_status?.metrics?.cpu_usage?.value || 0
  const memoryUsage = metrics?.system_status?.metrics?.memory_usage?.value || 0
  const responseTime = metrics?.system_status?.metrics?.api_response_time?.value || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time overview of your AutoBots multi-agent system
        </p>
      </motion.div>

      {/* Key Metrics Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Performance Score</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{performanceScore.toFixed(1)}%</div>
            <Progress value={performanceScore} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              System operating optimally
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Bots</CardTitle>
            <Bot className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5/5</div>
            <div className="flex space-x-1 mt-2">
              {[Eye, Shield, UserCheck, Cog, Zap].map((Icon, index) => (
                <Icon key={index} className="h-4 w-4 text-green-500" />
              ))}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              All systems operational
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">GDPR Compliance</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {metrics?.affiliate_stats?.compliance_rate || 100}%
            </div>
            <p className="text-xs text-green-600 mt-2">
              +{metrics?.affiliate_stats?.consented_affiliates || 0} consented affiliates
            </p>
            <p className="text-xs text-muted-foreground">
              Zero manual intervention
            </p>
          </CardContent>
        </Card>

        <Card className="border-border">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{responseTime.toFixed(0)}ms</div>
            <Progress value={(200 - responseTime) / 2} className="mt-2" />
            <p className="text-xs text-muted-foreground mt-2">
              Target: &lt;200ms
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Trends */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Card className="border-border">
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>
                Real-time system metrics over the last 24 hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="time" className="text-muted-foreground" />
                  <YAxis className="text-muted-foreground" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} name="CPU %" />
                  <Line type="monotone" dataKey="memory" stroke="#10b981" strokeWidth={2} name="Memory %" />
                  <Line type="monotone" dataKey="response" stroke="#f59e0b" strokeWidth={2} name="Response (ms)" />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Bot Activity */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Bot Activity</CardTitle>
              <CardDescription>
                Operations completed by each bot today
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={botActivityData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="name" className="text-muted-foreground" />
                  <YAxis className="text-muted-foreground" />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="operations" fill="#3b82f6" name="Total Operations" />
                  <Bar dataKey="success" fill="#10b981" name="Successful" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Operations */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="lg:col-span-2"
        >
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Recent Operations</CardTitle>
              <CardDescription>
                Latest bot activities and their status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {metrics?.recent_operations?.slice(0, 5).map((operation, index) => (
                  <motion.div
                    key={operation.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        {operation.bot_name === 'ScoutBot' && <Eye className="w-4 h-4 text-primary" />}
                        {operation.bot_name === 'SentinelBot' && <Shield className="w-4 h-4 text-primary" />}
                        {operation.bot_name === 'AffiliateBot' && <UserCheck className="w-4 h-4 text-primary" />}
                        {operation.bot_name === 'OperatorBot' && <Cog className="w-4 h-4 text-primary" />}
                        {operation.bot_name === 'ArchitectBot' && <Zap className="w-4 h-4 text-primary" />}
                      </div>
                      <div>
                        <p className="text-sm font-medium">{operation.operation_type.replace('_', ' ')}</p>
                        <p className="text-xs text-muted-foreground">{operation.bot_name} • {operation.vendor}</p>
                      </div>
                    </div>
                    <Badge variant={
                      operation.status === 'completed' ? 'default' :
                      operation.status === 'running' ? 'secondary' :
                      'destructive'
                    }>
                      {operation.status}
                    </Badge>
                  </motion.div>
                ))}
              </div>
              <Button variant="outline" className="w-full mt-4">
                View All Operations
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {/* Threat Analysis */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <Card className="border-border">
            <CardHeader>
              <CardTitle>Threat Analysis</CardTitle>
              <CardDescription>
                Security scan results from SentinelBot
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={threatData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {threatData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-4">
                {threatData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm">{item.name}</span>
                    </div>
                    <span className="text-sm font-medium">{item.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  )
}

export default Dashboard

