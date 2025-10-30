// js/api.js - Enhanced API Client with Recurring Task Support

class AgenticAPI {
    constructor(baseURL = null) {
        // Automatically detect the correct base URL
        this.baseURL = baseURL || window.location.origin;
    }

    async request(endpoint, options = {}) {
        try {
            console.log(`Making request to: ${this.baseURL}${endpoint}`);
            
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            console.log(`Response status: ${response.status}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(`HTTP error! status: ${response.status}, body: ${errorText}`);
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }
            
            const data = await response.json();
            console.log(`Response data:`, data);
            return data;
        } catch (error) {
            console.error('API Error:', error);
            
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error(`Cannot connect to API server at ${this.baseURL}. Make sure the Open Agentic Framework is running.`);
            }
            
            throw error;
        }
    }

    // Health & System endpoints (unchanged)
    getHealth() { 
        return this.request('/health'); 
    }
    
    async getProviders() { 
        try {
            return await this.request('/providers');
        } catch (error) {
            if (error.message.includes('404')) {
                console.warn('Providers endpoint not available - using older version of Open Agentic Framework');
                return null;
            }
            throw error;
        }
    }
    
    async getModels() { 
        try {
            const response = await this.request('/models/detailed');
            return this.normalizeModelsResponse(response);
        } catch (error) {
            console.warn('Failed to get detailed models, trying basic endpoint:', error.message);
            try {
                const response = await this.request('/models');
                return this.normalizeModelsResponse(response);
            } catch (fallbackError) {
                console.warn('Both models endpoints failed, using fallback models');
                return this.getFallbackModels();
            }
        }
    }

    normalizeModelsResponse(response) {
        // Handle different response formats
        if (Array.isArray(response)) {
            return response.map(this.normalizeModel);
        }
        
        if (response && Array.isArray(response.models)) {
            return response.models.map(this.normalizeModel);
        }
        
        if (response && response.available_models) {
            return Object.entries(response.available_models).map(([name, details]) => 
                this.normalizeModel({ name, ...details })
            );
        }
        
        // If response is an object with model names as keys
        if (response && typeof response === 'object' && !Array.isArray(response)) {
            return Object.entries(response).map(([name, details]) => 
                this.normalizeModel({ name, ...details })
            );
        }
        
        console.warn('Unexpected models response format:', response);
        return this.getFallbackModels();
    }

    normalizeModel(model) {
        // Ensure each model has required properties
        if (typeof model === 'string') {
            return {
                name: model,
                provider: 'ollama',
                display_name: model
            };
        }
        
        return {
            name: model.name || model.model || 'unknown',
            provider: model.provider || model.type || 'ollama',
            display_name: model.display_name || model.name || model.model || 'unknown',
            description: model.description || '',
            size: model.size || null,
            parameters: model.parameters || null
        };
    }

    getFallbackModels() {
        return [
            { name: 'granite3.2:2b', provider: 'ollama', display_name: 'Granite 3.2 2B' },
            { name: 'deepseek-r1:1.5b', provider: 'ollama', display_name: 'DeepSeek R1 1.5B' },
            { name: 'tinyllama:1.1b', provider: 'ollama', display_name: 'TinyLlama 1.1B' },
            { name: 'phi3:mini', provider: 'ollama', display_name: 'Phi-3 Mini' },
            { name: 'llama3.2:1b', provider: 'ollama', display_name: 'Llama 3.2 1B' }
        ];
    }
    
    getMemoryStats() { 
        return this.request('/memory/stats'); 
    }

    // Agent endpoints (unchanged)
    getAgents() { 
        return this.request('/agents'); 
    }
    
    createAgent(agent) { 
        return this.request('/agents', { 
            method: 'POST', 
            body: JSON.stringify(agent) 
        }); 
    }
    
    updateAgent(name, agent) { 
        return this.request(`/agents/${encodeURIComponent(name)}`, { 
            method: 'PUT', 
            body: JSON.stringify(agent) 
        }); 
    }
    
    deleteAgent(name) { 
        return this.request(`/agents/${encodeURIComponent(name)}`, { 
            method: 'DELETE' 
        }); 
    }
    
    executeAgent(name, task, context = {}) {
        return this.request(`/agents/${encodeURIComponent(name)}/execute`, {
            method: 'POST',
            body: JSON.stringify({ task, context })
        });
    }

    // Workflow endpoints (unchanged)
    getWorkflows() { 
        return this.request('/workflows'); 
    }
    
    createWorkflow(workflow) { 
        return this.request('/workflows', { 
            method: 'POST', 
            body: JSON.stringify(workflow) 
        }); 
    }
    
    updateWorkflow(name, workflow) {
        return this.request(`/workflows/${encodeURIComponent(name)}`, {
            method: 'PUT',
            body: JSON.stringify(workflow)
        });
    }
    
    deleteWorkflow(name) {
        return this.request(`/workflows/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
    }
    
    executeWorkflow(name, context = {}) {
        return this.request(`/workflows/${encodeURIComponent(name)}/execute`, {
            method: 'POST',
            body: JSON.stringify({ context })
        });
    }

    // Tool endpoints (unchanged)
    getTools() { 
        return this.request('/tools'); 
    }
    
    executeTool(name, parameters) {
        return this.request(`/tools/${encodeURIComponent(name)}/execute`, {
            method: 'POST',
            body: JSON.stringify({ parameters })
        });
    }

    // NEW: Tool configuration endpoints
    getToolConfig(toolName) {
        return this.request(`/tools/${encodeURIComponent(toolName)}/config`);
    }

    configureTool(toolName, config) {
        return this.request(`/tools/${encodeURIComponent(toolName)}/configure`, {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    // ENHANCED: Scheduling endpoints with recurring support
    getScheduledTasks() { 
        return this.request('/schedule'); 
    }
    
    scheduleTask(task) {
        return this.request('/schedule', {
            method: 'POST',
            body: JSON.stringify(task)
        });
    }
    
    updateScheduledTask(taskId, updates) {
        return this.request(`/schedule/${encodeURIComponent(taskId)}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }
    
    deleteScheduledTask(taskId) {
        return this.request(`/schedule/${encodeURIComponent(taskId)}`, {
            method: 'DELETE'
        });
    }

    // NEW: Recurring task management endpoints
    enableScheduledTask(taskId) {
        return this.request(`/schedule/${encodeURIComponent(taskId)}/enable`, {
            method: 'POST'
        });
    }

    disableScheduledTask(taskId) {
        return this.request(`/schedule/${encodeURIComponent(taskId)}/disable`, {
            method: 'POST'
        });
    }

    getTaskExecutions(taskId, limit = 10) {
        return this.request(`/schedule/${encodeURIComponent(taskId)}/executions?limit=${limit}`);
    }

    getScheduleStatistics() {
        return this.request('/schedule/statistics');
    }

    // NEW: Recurrence pattern endpoints
    getRecurrencePatternSuggestions() {
        return this.request('/schedule/patterns/suggestions');
    }

    validateRecurrencePattern(pattern, patternType) {
        return this.request('/schedule/patterns/validate', {
            method: 'POST',
            body: JSON.stringify({
                pattern: pattern,
                pattern_type: patternType
            })
        });
    }

    // Provider management endpoints (unchanged)
    getProviders() { 
        return this.request('/providers'); 
    }

    configureProvider(providerName, config) {
        return this.request(`/providers/${encodeURIComponent(providerName)}/configure`, {
            method: 'POST',
            body: JSON.stringify(config)
        });
    }

    getProviderConfig(providerName) {
        return this.request(`/providers/${encodeURIComponent(providerName)}/config`);
    }

    checkProviderHealth(providerName) {
        return this.request(`/providers/${encodeURIComponent(providerName)}/health-check`, {
            method: 'POST'
        });
    }

    reloadProviders() {
        return this.request('/providers/reload', {
            method: 'POST'
        });
    }

    reloadModels() {
        return this.request('/providers/reload-models', {
            method: 'POST'
        });
    }

    // Model management endpoints (unchanged)
    installModel(modelName, waitForCompletion = false) {
        return this.request('/models/install', {
            method: 'POST',
            body: JSON.stringify({
                model_name: modelName,
                wait_for_completion: waitForCompletion
            })
        });
    }

    deleteModel(modelName) {
        return this.request(`/models/${encodeURIComponent(modelName)}`, {
            method: 'DELETE'
        });
    }

    testModel(modelName) {
        return this.request(`/models/test/${encodeURIComponent(modelName)}`, {
            method: 'POST'
        });
    }

    getModelStatus() {
        return this.request('/models/status');
    }

    getModelInfo(modelName) {
        return this.request(`/models/${encodeURIComponent(modelName)}/info`);
    }
}

// Create global API instance
window.AgenticAPI = AgenticAPI;
window.api = new AgenticAPI();