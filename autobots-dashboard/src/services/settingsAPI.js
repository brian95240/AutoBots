// AutoBots Settings API Client
// Frontend service for managing settings

class SettingsAPI {
  constructor(baseURL = 'http://localhost:5001/api') {
    this.baseURL = baseURL
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`)
      }
      
      return data
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
  }

  // Bot Configuration Methods
  async getBotConfigs() {
    return this.request('/settings/bots')
  }

  async updateBotConfig(botId, config) {
    return this.request(`/settings/bots/${botId}`, {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  }

  // Alert Configuration Methods
  async getAlertConfig() {
    return this.request('/settings/alerts')
  }

  async updateAlertConfig(config) {
    return this.request('/settings/alerts', {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  }

  // System Configuration Methods
  async getSystemConfig() {
    return this.request('/settings/system')
  }

  async updateSystemConfig(config) {
    return this.request('/settings/system', {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  }

  // Notification Configuration Methods
  async getNotificationConfig() {
    return this.request('/settings/notifications')
  }

  async updateNotificationConfig(config) {
    return this.request('/settings/notifications', {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  }

  // Security Configuration Methods
  async getSecurityConfig() {
    return this.request('/settings/security')
  }

  async updateSecurityConfig(config) {
    return this.request('/settings/security', {
      method: 'PUT',
      body: JSON.stringify(config)
    })
  }

  // Utility Methods
  async testConnection(type, config = {}) {
    return this.request('/settings/test-connection', {
      method: 'POST',
      body: JSON.stringify({ type, ...config })
    })
  }

  async exportSettings() {
    return this.request('/settings/export')
  }

  async importSettings(settingsData) {
    return this.request('/settings/import', {
      method: 'POST',
      body: JSON.stringify(settingsData)
    })
  }

  async healthCheck() {
    return this.request('/health')
  }
}

export default SettingsAPI

