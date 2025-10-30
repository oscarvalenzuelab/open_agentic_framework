"""
main.py - FastAPI Application Entry Point (Enhanced with Multi-Provider LLM Support)
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import uvicorn
import asyncio
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import Config
from models import *
from managers.llm_provider_manager import LLMProviderManager
from managers.memory_manager import MemoryManager
from managers.tool_manager import ToolManager
from managers.agent_manager import AgentManager
from managers.workflow_manager import WorkflowManager
from managers.model_warmup_manager import ModelWarmupManager, ModelWarmupStatus
from pydantic import BaseModel, Field
from models import ScheduledTaskDefinition, ScheduledTaskUpdate, TaskExecutionInfo, RecurrenceType
import os
import json
import zipfile
from pathlib import Path


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Open Agentic Framework",
    description="A robust framework for managing AI agents and workflows with multi-provider LLM support",
    version="1.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
web_ui_path = os.path.join(os.path.dirname(__file__), "web-ui")
if os.path.exists(web_ui_path):
    app.mount("/ui", StaticFiles(directory=web_ui_path, html=True), name="web-ui")
    logger.info(f"Web UI mounted at /ui from {web_ui_path}")
else:
    logger.warning(f"Web UI directory not found at {web_ui_path}")

# Global configuration
config = Config()

# Initialize managers
llm_manager = LLMProviderManager(config.llm_config)
memory_manager = MemoryManager(config.database_path)
tool_manager = ToolManager(memory_manager, config.tools_directory, config)
agent_manager = AgentManager(llm_manager, memory_manager, tool_manager, config)
workflow_manager = WorkflowManager(agent_manager, tool_manager, memory_manager)
warmup_manager = ModelWarmupManager(llm_manager, memory_manager, config)

# Enhanced Background scheduler with memory cleanup
class BackgroundScheduler:
    """Enhanced background scheduler with recurring task support"""
    
    def __init__(self, memory_manager, agent_manager, workflow_manager, config, interval=60):
        self.memory_manager = memory_manager
        self.agent_manager = agent_manager
        self.workflow_manager = workflow_manager
        self.config = config
        self.interval = interval
        self.running = False
        self._last_memory_cleanup = time.time()
        self._last_stats_log = time.time()
    
    async def start(self):
        """Start the background scheduler with recurring task support"""
        self.running = True
        logger.info("Enhanced background scheduler started with recurring task support")
        
        while self.running:
            try:
                await self._process_pending_tasks()
                await self._check_memory_cleanup()
                await self._log_periodic_stats()
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(self.interval)
    
    def stop(self):
        """Stop the background scheduler"""
        self.running = False
        logger.info("Background scheduler stopped")
    
    async def _process_pending_tasks(self):
        """Process pending scheduled tasks including recurring ones"""
        pending_tasks = self.memory_manager.get_pending_scheduled_tasks()
        
        if not pending_tasks:
            return
        
        logger.info(f"Processing {len(pending_tasks)} pending tasks")
        
        for task in pending_tasks:
            try:
                task_id = task['id']
                task_type = task['task_type']
                is_recurring = task.get('is_recurring', False)
                execution_count = task.get('execution_count', 0)
                
                logger.info(f"Executing task {task_id} ({task_type})" + 
                          (f" - execution #{execution_count + 1}" if is_recurring else ""))
                
                start_time = time.time()
                
                if task_type == "agent":
                    result = await self.agent_manager.execute_agent(
                        task['agent_name'], 
                        task['task_description'],
                        context=task['context'] or {}
                    )
                elif task_type == "workflow":
                    result = await self.workflow_manager.execute_workflow(
                        task['workflow_name'],
                        context=task['context'] or {}
                    )
                else:
                    raise ValueError(f"Unknown task type: {task_type}")
                
                execution_time = time.time() - start_time
                
                # Update task as completed
                self.memory_manager.update_scheduled_task_status(
                    task_id, "completed", str(result)
                )
                
                log_msg = f"Completed task {task_id} in {execution_time:.2f}s"
                if is_recurring:
                    log_msg += f" (execution #{execution_count + 1})"
                logger.info(log_msg)
                
            except Exception as e:
                error_msg = str(e)
                execution_count = task.get('execution_count', 0)
                is_recurring = task.get('is_recurring', False)
                
                # Update task as failed
                self.memory_manager.update_scheduled_task_status(
                    task_id, "failed", error_msg
                )
                
                log_msg = f"Failed task {task_id}: {error_msg}"
                if is_recurring:
                    log_msg += f" (execution #{execution_count + 1})"
                logger.error(log_msg)
    
    async def _check_memory_cleanup(self):
        """Check if periodic memory cleanup is needed"""
        current_time = time.time()
        
        if current_time - self._last_memory_cleanup >= self.config.memory_cleanup_interval:
            await self._cleanup_memory_periodic()
            self._last_memory_cleanup = current_time
    
    async def _cleanup_memory_periodic(self):
        """Periodic memory cleanup for all agents"""
        try:
            logger.info("Starting periodic memory cleanup...")
            agents = self.memory_manager.get_all_agents()
            
            for agent in agents:
                self.memory_manager.cleanup_agent_memory(
                    agent["name"], 
                    keep_last=self.config.max_agent_memory_entries
                )
            
            logger.info(f"Completed periodic memory cleanup for {len(agents)} agents")
        except Exception as e:
            logger.error(f"Error during periodic memory cleanup: {e}")
    
    async def _log_periodic_stats(self):
        """Log periodic statistics about tasks and system"""
        current_time = time.time()
        
        # Log stats every hour
        if current_time - self._last_stats_log >= 3600:
            try:
                # Get task statistics
                all_tasks = self.memory_manager.get_all_scheduled_tasks()
                
                recurring_count = sum(1 for task in all_tasks if task.get('is_recurring', False))
                active_recurring = sum(1 for task in all_tasks 
                                     if task.get('is_recurring', False) and task.get('enabled', True))
                total_executions = sum(task.get('execution_count', 0) for task in all_tasks)
                
                logger.info(f"Task Statistics: {len(all_tasks)} total tasks, "
                          f"{recurring_count} recurring ({active_recurring} active), "
                          f"{total_executions} total executions")
                
                # Get memory statistics
                memory_stats = self.memory_manager.get_memory_stats()
                logger.info(f"Memory Statistics: {memory_stats['total_memory_entries']} entries, "
                          f"{memory_stats['agents_with_memory']} agents with memory")
                
                self._last_stats_log = current_time
                
            except Exception as e:
                logger.error(f"Error logging periodic stats: {e}")

# Initialize enhanced background scheduler
background_scheduler = BackgroundScheduler(
    memory_manager, agent_manager, workflow_manager, config, config.scheduler_interval
)

@app.on_event("startup")
async def startup_event():
    """Initialize the framework on startup with memory cleanup"""
    try:
        # Initialize database tables
        memory_manager.initialize_database()
        
        # Clear all agent memory on startup if configured
        if config.clear_memory_on_startup:
            logger.info("Clearing all agent memory on startup...")
            memory_manager.clear_all_agent_memory()
        
        # Initialize LLM providers (non-blocking - warn if no providers available)
        provider_init_success = await llm_manager.initialize()
        if not provider_init_success:
            logger.warning("No LLM providers were successfully initialized. The app will run but agent execution will fail.")
            # Don't crash - allow the app to start so users can configure providers

        # Load and register tools
        tool_manager.discover_and_register_tools()
        
        # Start background scheduler
        asyncio.create_task(background_scheduler.start())
        
        logger.info("Open Agentic Framework started successfully with enhanced memory management")
        
        # Start model warmup manager
        await warmup_manager.start()
        
        logger.info("Open Agentic Framework started successfully with multi-provider support")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    background_scheduler.stop()
    await warmup_manager.stop()
    logger.info("Open Agentic Framework shutdown complete")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint - redirects to web UI if available, otherwise shows API info"""
    return {
        "message": "Open Agentic Framework",
        "version": "1.2.0",
        "web_ui": "/ui",
        "api_docs": "/docs",
        "health": "/health",
        "providers": "/providers",
        "models": "/models",
        "memory_stats": "/memory/stats"
    }

@app.get("/ui")
async def web_ui():
    """Redirect to web UI index page"""
    return RedirectResponse(url="/ui/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint with provider and warmup info"""
    provider_health = await llm_manager.health_check()
    warmup_stats = warmup_manager.get_warmup_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "providers": provider_health,
        "memory_entries": memory_manager.get_memory_stats()["total_memory_entries"],
        "warmup_stats": {
            "active_models": warmup_stats["active_models"],
            "total_models": warmup_stats["total_models"],
            "success_rate": warmup_stats["success_rate"]
        }
    }

# Provider Management Endpoints
@app.get("/providers")
async def list_providers():
    """List all available LLM providers and their status"""
    provider_status = llm_manager.get_provider_status()
    
    return {
        "providers": {
            name: {
                "name": status.name,
                "is_healthy": status.is_healthy,
                "is_initialized": status.is_initialized,
                "model_count": status.model_count,
                "last_check": status.last_check.isoformat(),
                "error_message": status.error_message
            }
            for name, status in provider_status.items()
        },
        "default_provider": config.llm_config.get("default_provider"),
        "fallback_enabled": config.llm_config.get("fallback_enabled"),
        "fallback_order": config.llm_config.get("fallback_order", [])
    }

@app.get("/providers/{provider_name}")
async def get_provider_info(provider_name: str):
    """Get detailed information about a specific provider"""
    provider = llm_manager.get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    models = await llm_manager.list_models(provider_name)
    health_status = await llm_manager.health_check()
    
    return {
        "name": provider_name,
        "is_healthy": health_status.get(provider_name, False),
        "is_initialized": provider.is_initialized,
        "config": provider.get_config(),
        "models": [
            {
                "name": model.name,
                "description": model.description,
                "context_length": model.context_length,
                "supports_streaming": model.supports_streaming,
                "supports_tools": model.supports_tools,
                "model_type": model.model_type
            }
            for model in models
        ],
        "model_count": len(models)
    }

@app.post("/providers/{provider_name}/health-check")
async def check_provider_health(provider_name: str):
    """Perform a health check on a specific provider"""
    provider = llm_manager.get_provider(provider_name)
    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")
    
    is_healthy = await provider.health_check()
    
    return {
        "provider": provider_name,
        "is_healthy": is_healthy,
        "timestamp": datetime.utcnow()
    }

@app.post("/providers/reload-models")
async def reload_provider_models():
    """Reload models from all providers"""
    try:
        await llm_manager.reload_models()
        return {
            "message": "Models reloaded successfully",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload models: {str(e)}")

class ProviderConfigUpdate(BaseModel):
    """Model for updating provider configuration"""
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    timeout: Optional[int] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

@app.post("/providers/{provider_name}/configure")
async def configure_provider(provider_name: str, config_update: ProviderConfigUpdate):
    """Dynamically configure a provider without restart"""
    try:
        # Validate provider exists
        valid_providers = ["openai", "openrouter", "ollama", "bedrock"]
        if provider_name not in valid_providers:
            raise HTTPException(status_code=400, detail=f"Invalid provider. Must be one of: {valid_providers}")
        
        # Get current config
        current_config = config.llm_config.get("providers", {}).get(provider_name, {})
        
        # Update with new values
        update_dict = config_update.dict(exclude_unset=True)
        current_config.update(update_dict)
        
        # Apply to config
        if "providers" not in config.llm_config:
            config.llm_config["providers"] = {}
        config.llm_config["providers"][provider_name] = current_config
        
        # If enabling a provider, reinitialize it
        if update_dict.get("enabled", False):
            await _reinitialize_provider(provider_name, current_config)
        
        # If disabling, remove from active providers
        elif update_dict.get("enabled") is False:
            if provider_name in llm_manager.providers:
                del llm_manager.providers[provider_name]
                logger.info(f"Disabled provider: {provider_name}")
        
        return {
            "message": f"Provider {provider_name} configured successfully",
            "provider": provider_name,
            "config": current_config,
            "restart_required": False
        }
        
    except Exception as e:
        logger.error(f"Error configuring provider {provider_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _reinitialize_provider(provider_name: str, provider_config: Dict[str, Any]):
    """Reinitialize a provider with new configuration"""
    try:
        # Create new provider instance
        provider = llm_manager._create_provider(provider_name, provider_config)
        if not provider:
            raise ValueError(f"Failed to create provider instance for {provider_name}")
        
        # Initialize the provider
        if await provider.initialize():
            # Add to active providers
            llm_manager.providers[provider_name] = provider
            
            # Load models for this provider
            await llm_manager._load_provider_models(provider_name)
            
            logger.info(f"Successfully reinitialized provider: {provider_name}")
            return True
        else:
            logger.error(f"Failed to initialize provider: {provider_name}")
            return False
            
    except Exception as e:
        logger.error(f"Error reinitializing provider {provider_name}: {e}")
        return False

@app.get("/providers/{provider_name}/config")
async def get_provider_config(provider_name: str):
    """Get current provider configuration (without sensitive data)"""
    try:
        provider_config = config.llm_config.get("providers", {}).get(provider_name, {})
        
        # Remove sensitive information from response
        safe_config = provider_config.copy()
        if "api_key" in safe_config:
            safe_config["api_key"] = "***" + safe_config["api_key"][-4:] if len(safe_config["api_key"]) > 4 else "***"
        if "aws_access_key_id" in safe_config:
            safe_config["aws_access_key_id"] = "***" + safe_config["aws_access_key_id"][-4:] if len(safe_config["aws_access_key_id"]) > 4 else "***"
        if "aws_secret_access_key" in safe_config:
            safe_config["aws_secret_access_key"] = "***" + safe_config["aws_secret_access_key"][-4:] if len(safe_config["aws_secret_access_key"]) > 4 else "***"
        
        return {
            "provider": provider_name,
            "config": safe_config,
            "is_active": provider_name in llm_manager.providers,
            "is_healthy": await _check_provider_health_safe(provider_name)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _check_provider_health_safe(provider_name: str) -> bool:
    """Safely check provider health without throwing errors"""
    try:
        if provider_name in llm_manager.providers:
            return await llm_manager.providers[provider_name].health_check()
        return False
    except:
        return False

@app.post("/providers/reload")
async def reload_all_providers():
    """Reload all providers with current configuration"""
    try:
        # Reinitialize the LLM manager with current config
        await llm_manager.initialize()
        
        return {
            "message": "All providers reloaded successfully",
            "active_providers": list(llm_manager.providers.keys()),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error reloading providers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced Models endpoints with multi-provider support
@app.get("/models", response_model=List[str])
async def list_models(provider: str = None):
    """List all available models from all providers or a specific provider"""
    try:
        models = await llm_manager.list_models(provider)
        return [model.name for model in models]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch models: {str(e)}")

@app.get("/models/detailed")
async def list_models_detailed(provider: str = None):
    """List all available models with detailed information"""
    try:
        models = await llm_manager.list_models(provider)
        return {
            "models": [
                {
                    "name": model.name,
                    "provider": model.provider,
                    "description": model.description,
                    "context_length": model.context_length,
                    "max_tokens": model.max_tokens,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                    "supports_streaming": model.supports_streaming,
                    "supports_tools": model.supports_tools,
                    "model_type": model.model_type
                }
                for model in models
            ],
            "total_count": len(models),
            "provider_filter": provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed models: {str(e)}")

@app.get("/models/status")
async def get_models_status():
    """Get detailed status of available models across all providers"""
    try:
        provider_health = await llm_manager.health_check()
        all_models = await llm_manager.list_models()
        
        models_by_provider = {}
        for model in all_models:
            if model.provider not in models_by_provider:
                models_by_provider[model.provider] = []
            models_by_provider[model.provider].append(model.name)
        
        return {
            "provider_health": provider_health,
            "total_models": len(all_models),
            "models_by_provider": models_by_provider,
            "default_provider": config.llm_config.get("default_provider"),
            "default_model": config.llm_config.get("default_model"),
            "enabled_providers": config.get_enabled_providers()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models status: {str(e)}")

@app.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get detailed information about a specific model"""
    try:
        model_info = llm_manager.get_model_info(model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
        
        return {
            "name": model_info.name,
            "provider": model_info.provider,
            "description": model_info.description,
            "context_length": model_info.context_length,
            "max_tokens": model_info.max_tokens,
            "cost_per_1k_tokens": model_info.cost_per_1k_tokens,
            "supports_streaming": model_info.supports_streaming,
            "supports_tools": model_info.supports_tools,
            "model_type": model_info.model_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")

@app.post("/models/test/{model_name}")
async def test_model(model_name: str):
    """Test if a model is working correctly"""
    try:
        test_prompt = "Hello, please respond with 'Model test successful' to confirm you are working."
        
        response = await llm_manager.generate_response(
            prompt=test_prompt,
            model=model_name
        )
        
        return {
            "model_name": model_name,
            "test_prompt": test_prompt,
            "response": response,
            "status": "working",
            "test_successful": True
        }
        
    except Exception as e:
        logger.error(f"Model test error for {model_name}: {e}")
        return {
            "model_name": model_name,
            "error": str(e),
            "status": "error",
            "test_successful": False
        }

# Ollama-specific endpoints (for backward compatibility)
@app.post("/models/install")
async def install_model(request: ModelInstallRequest, background_tasks: BackgroundTasks):
    """Install a new model (Ollama provider only)"""
    try:
        ollama_provider = llm_manager.get_provider("ollama")
        if not ollama_provider:
            raise HTTPException(status_code=400, detail="Ollama provider not available")
        
        model_name = request.model_name.strip()
        if not model_name:
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        logger.info(f"Starting installation of model: {model_name}")
        
        if request.wait_for_completion:
            success = await ollama_provider.pull_model(model_name)
            
            if success:
                # Reload models to include the new one
                await llm_manager.reload_models()
                
                return {
                    "message": f"Model {model_name} installed successfully",
                    "model_name": model_name,
                    "status": "installed"
                }
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Failed to install model {model_name}"
                )
        else:
            # Start installation in background
            async def background_install():
                try:
                    logger.info(f"Background installation started for {model_name}")
                    success = await ollama_provider.pull_model(model_name)
                    if success:
                        await llm_manager.reload_models()
                        logger.info(f"Background installation completed for {model_name}")
                    else:
                        logger.error(f"Background installation failed for {model_name}")
                except Exception as e:
                    logger.error(f"Background installation error for {model_name}: {e}")
            
            background_tasks.add_task(background_install)
            return {
                "message": f"Model {model_name} installation started in background",
                "model_name": model_name,
                "status": "installing"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected model installation error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model (Ollama provider only)"""
    try:
        ollama_provider = llm_manager.get_provider("ollama")
        if not ollama_provider:
            raise HTTPException(status_code=400, detail="Ollama provider not available")
        
        success = await ollama_provider.delete_model(model_name)
        if success:
            # Reload models to reflect the deletion
            await llm_manager.reload_models()
            
            return {
                "message": f"Model {model_name} deleted successfully",
                "model_name": model_name,
                "status": "deleted"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to delete model {model_name}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """Get current framework configuration"""
    return ConfigResponse(**config.to_dict())

@app.put("/config")
async def update_config(config_update: ConfigUpdate):
    """Update framework configuration"""
    try:
        config.update(config_update.dict(exclude_unset=True))
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Agent endpoints (updated to use new LLM manager)
@app.post("/agents", response_model=AgentResponse)
async def create_agent(agent_def: AgentDefinition):
    """Create a new agent"""
    try:
        agent_id = memory_manager.register_agent(
            name=agent_def.name,
            role=agent_def.role,
            goals=agent_def.goals,
            backstory=agent_def.backstory,
            tools=agent_def.tools,
            ollama_model=agent_def.ollama_model,
            enabled=agent_def.enabled,
            tool_configs=agent_def.tool_configs or {}
        )
        return AgentResponse(id=agent_id, name=agent_def.name, message="Agent created successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all agents"""
    return memory_manager.get_all_agents()

@app.get("/agents/{agent_name}", response_model=AgentInfo)
async def get_agent(agent_name: str):
    """Get agent details"""
    agent = memory_manager.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

@app.put("/agents/{agent_name}")
async def update_agent(agent_name: str, agent_update: AgentUpdate):
    """Update an existing agent"""
    try:
        memory_manager.update_agent(agent_name, agent_update.dict(exclude_unset=True))
        return {"message": "Agent updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/agents/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent"""
    try:
        memory_manager.delete_agent(agent_name)
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_name}/execute", response_model=AgentExecutionResponse)
async def execute_agent(agent_name: str, request: AgentExecutionRequest):
    """Execute an agent task with model usage tracking"""
    try:
        # Get agent info to track model usage
        agent = memory_manager.get_agent(agent_name)
        if agent:
            model_name = agent.get('ollama_model', config.default_model)
            await warmup_manager.mark_model_used(model_name)
        
        result = await agent_manager.execute_agent(
            agent_name, request.task, request.context or {}
        )
        return AgentExecutionResponse(
            agent_name=agent_name,
            task=request.task,
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/agents/{agent_name}/memory", response_model=List[MemoryEntryResponse])
async def get_agent_memory(agent_name: str, limit: int = 5):
    """Get agent's memory/conversation history (limited)"""
    return memory_manager.get_agent_memory(agent_name, limit)

# Memory management endpoints (unchanged)
@app.delete("/agents/{agent_name}/memory")
async def clear_agent_memory(agent_name: str):
    """Clear all memory for a specific agent"""
    try:
        agent = memory_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        memory_manager.clear_agent_memory(agent_name)
        return {"message": f"Memory cleared for agent {agent_name}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/agents/{agent_name}/memory/cleanup")
async def cleanup_agent_memory_endpoint(agent_name: str, keep_last: int = 5):
    """Cleanup old memory entries for a specific agent"""
    try:
        agent = memory_manager.get_agent(agent_name)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        memory_manager.cleanup_agent_memory(agent_name, keep_last)
        return {
            "message": f"Memory cleanup completed for agent {agent_name}",
            "kept_entries": keep_last
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory usage statistics"""
    try:
        stats = memory_manager.get_memory_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/clear-all")
async def clear_all_memory():
    """Clear memory for all agents"""
    try:
        memory_manager.clear_all_agent_memory()
        return {"message": "All agent memory cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/memory/cleanup")
async def cleanup_all_agent_memory():
    """Cleanup old memory entries for all agents, keeping only last entries"""
    try:
        agents = memory_manager.get_all_agents()
        cleaned_agents = 0
        
        for agent in agents:
            memory_manager.cleanup_agent_memory(agent["name"], keep_last=config.max_agent_memory_entries)
            cleaned_agents += 1
        
        return {
            "message": f"Memory cleanup completed for {cleaned_agents} agents",
            "agents_processed": cleaned_agents,
            "kept_entries_per_agent": config.max_agent_memory_entries
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Tool endpoints (unchanged)
@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """List all tools"""
    return memory_manager.get_all_tools()

@app.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool(tool_name: str):
    """Get tool details"""
    tool = memory_manager.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool

@app.post("/tools/{tool_name}/execute", response_model=ToolExecutionResponse)
async def execute_tool(tool_name: str, request: ToolExecutionRequest):
    """Execute a specific tool with parameters"""
    try:
        result = await tool_manager.execute_tool(tool_name, request.parameters, request.agent_name)
        return ToolExecutionResponse(
            tool_name=tool_name,
            parameters=request.parameters,
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Tool execution failed for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/{tool_name}/config")
async def get_tool_config(tool_name: str):
    """Get configuration for a specific tool"""
    try:
        tool = tool_manager.get_tool_instance(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Return the tool's configuration from database
        config = memory_manager.get_tool_configuration(tool_name) or {}
        return config
    except Exception as e:
        logger.error(f"Failed to get config for tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/{tool_name}/configure")
async def configure_tool(tool_name: str, config: Dict[str, Any]):
    """Configure a specific tool with new settings"""
    try:
        tool = tool_manager.get_tool_instance(tool_name)
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Store configuration in database (tool-level configuration)
        memory_manager.set_tool_configuration(tool_name, config)
        
        # Also set configuration on tool instance for immediate use
        if hasattr(tool, 'set_config'):
            tool.set_config(config)
            logger.info(f"Updated configuration for tool {tool_name}")
            return {"message": f"Configuration updated for tool {tool_name}"}
        else:
            raise HTTPException(status_code=400, detail=f"Tool {tool_name} does not support configuration")
    except Exception as e:
        logger.error(f"Failed to configure tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow endpoints (unchanged)
@app.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow_def: WorkflowDefinition):
    """Create a new workflow"""
    try:
        steps_dict = []
        for step in workflow_def.steps:
            step_dict = {
                "type": step.type,
                "name": step.name,
                "task": step.task,
                "tool": getattr(step, 'tool', None),
                "parameters": step.parameters or {},
                "context_key": step.context_key,
                "use_previous_output": getattr(step, 'use_previous_output', False),
                "preserve_objects": getattr(step, 'preserve_objects', False)
            }
            steps_dict.append(step_dict)
        
        workflow_id = memory_manager.register_workflow(
            name=workflow_def.name,
            description=workflow_def.description,
            steps=steps_dict,
            enabled=workflow_def.enabled,
            input_schema=workflow_def.input_schema,
            output_spec=workflow_def.output_spec
        )
        return WorkflowResponse(id=workflow_id, name=workflow_def.name, message="Workflow created successfully")
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/workflows", response_model=List[WorkflowInfo])
async def list_workflows():
    """List all workflows"""
    return memory_manager.get_all_workflows()

@app.get("/workflows/{workflow_name}", response_model=WorkflowInfo)
async def get_workflow(workflow_name: str):
    """Get workflow details"""
    workflow = memory_manager.get_workflow(workflow_name)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@app.put("/workflows/{workflow_name}")
async def update_workflow(workflow_name: str, workflow_update: WorkflowUpdate):
    """Update an existing workflow"""
    try:
        memory_manager.update_workflow(workflow_name, workflow_update.dict(exclude_unset=True))
        return {"message": "Workflow updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/workflows/{workflow_name}")
async def delete_workflow(workflow_name: str):
    """Delete a workflow"""
    try:
        memory_manager.delete_workflow(workflow_name)
        return {"message": "Workflow deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/workflows/{workflow_name}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(workflow_name: str, request: WorkflowExecutionRequest):
    """Execute a workflow with input validation"""
    try:
        # Get workflow to check input schema
        workflow = memory_manager.get_workflow(workflow_name)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_name} not found")
        
        if not workflow.get("enabled", True):
            raise HTTPException(status_code=400, detail=f"Workflow {workflow_name} is disabled")
        
        # Validate input against schema if present
        input_context = request.context or {}
        if workflow.get("input_schema"):
            validation_error = validate_workflow_input(workflow["input_schema"], input_context)
            if validation_error:
                raise HTTPException(status_code=400, detail=f"Input validation failed: {validation_error}")
        
        # Get agent name from agent_id if provided
        agent_name = None
        if request.agent_id:
            agent = memory_manager.get_agent_by_id(request.agent_id)
            if agent:
                agent_name = agent.get("name")
                logger.info(f"Workflow execution with agent: {agent_name}")
        
        result = await workflow_manager.execute_workflow(
            workflow_name, input_context, agent_name
        )
        return WorkflowExecutionResponse(
            workflow_name=workflow_name,
            context=input_context,
            result=result,
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

def validate_workflow_input(input_schema: Dict[str, Any], input_data: Dict[str, Any]) -> Optional[str]:
    """
    Validate workflow input against schema
    
    Args:
        input_schema: JSON schema for input validation
        input_data: Actual input data
        
    Returns:
        Error message if validation fails, None if valid
    """
    try:
        # Check required fields
        required_fields = input_schema.get("required", [])
        for field in required_fields:
            if field not in input_data:
                return f"Required field '{field}' is missing"
            
            # Check for None or empty values
            value = input_data[field]
            if value is None or (isinstance(value, str) and value.strip() == ""):
                return f"Required field '{field}' cannot be empty"
        
        # Basic type validation
        properties = input_schema.get("properties", {})
        for field_name, field_schema in properties.items():
            if field_name in input_data:
                expected_type = field_schema.get("type")
                value = input_data[field_name]
                
                if expected_type and not _validate_field_type(value, expected_type):
                    return f"Field '{field_name}' should be of type {expected_type}"
        
        return None  # Validation passed
        
    except Exception as e:
        return f"Validation error: {str(e)}"

def _validate_field_type(value: Any, expected_type: str) -> bool:
    """Validate if value matches expected JSON schema type"""
    type_mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }
    
    if expected_type in type_mapping:
        expected_python_type = type_mapping[expected_type]
        return isinstance(value, expected_python_type)
    
    return True

# Scheduling endpoints (unchanged)
@app.post("/schedule", response_model=ScheduleResponse)
async def schedule_task(task: ScheduledTaskDefinition):
    """Schedule a task for execution with full recurring support"""
    try:
        # Debug logging
        logger.info(f"Received task data: {task.dict()}")
        
        # Ensure scheduled_time is properly converted if it's a string
        scheduled_time = task.scheduled_time
        if isinstance(scheduled_time, str):
            try:
                # Handle ISO format with or without Z suffix
                if scheduled_time.endswith('Z'):
                    scheduled_time = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
                else:
                    scheduled_time = datetime.fromisoformat(scheduled_time)
                logger.info(f"Converted scheduled_time to: {scheduled_time}")
            except ValueError as e:
                logger.error(f"Error parsing scheduled_time: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid date format: {scheduled_time}")
        
        # Call memory_manager with ALL recurring parameters
        task_id = memory_manager.schedule_task(
            task_type=task.task_type,
            agent_name=task.agent_name,
            workflow_name=task.workflow_name,
            task_description=task.task_description,
            scheduled_time=scheduled_time,
            context=task.context or {},
            # NEW: Pass all recurring parameters
            is_recurring=task.is_recurring,
            recurrence_pattern=task.recurrence_pattern,
            recurrence_type=task.recurrence_type,
            max_executions=task.max_executions,
            max_failures=task.max_failures
        )
        
        # Calculate next execution for response
        next_execution = None
        if task.is_recurring and task.recurrence_pattern:
            try:
                next_execution = memory_manager._calculate_next_execution(
                    scheduled_time, 
                    task.recurrence_pattern, 
                    task.recurrence_type
                )
            except Exception as e:
                logger.warning(f"Could not calculate next execution: {e}")
        
        logger.info(f"Successfully created task {task_id} - recurring: {task.is_recurring}")
        
        return ScheduleResponse(
            id=task_id, 
            message="Task scheduled successfully",
            is_recurring=task.is_recurring,
            next_execution=next_execution
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling task: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/schedule", response_model=List[ScheduledTaskInfo])
async def list_scheduled_tasks():
    """List all scheduled tasks"""
    return memory_manager.get_all_scheduled_tasks()

@app.delete("/schedule/{task_id}")
async def delete_scheduled_task(task_id: int):
    """Delete a scheduled task"""
    try:
        memory_manager.delete_scheduled_task(task_id)
        return {"message": "Scheduled task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/schedule/statistics")
async def get_schedule_statistics():
    """Get comprehensive scheduling statistics"""
    try:
        all_tasks = memory_manager.get_all_scheduled_tasks()
        
        stats = {
            "total_tasks": len(all_tasks),
            "one_time_tasks": sum(1 for task in all_tasks if not task.get('is_recurring', False)),
            "recurring_tasks": sum(1 for task in all_tasks if task.get('is_recurring', False)),
            "active_recurring": sum(1 for task in all_tasks 
                                  if task.get('is_recurring', False) and task.get('enabled', True)),
            "disabled_tasks": sum(1 for task in all_tasks if not task.get('enabled', True)),
            "completed_tasks": sum(1 for task in all_tasks if task.get('status') == 'completed'),
            "failed_tasks": sum(1 for task in all_tasks if task.get('status') == 'failed'),
            "pending_tasks": sum(1 for task in all_tasks if task.get('status') == 'pending'),
            "total_executions": sum(task.get('execution_count', 0) for task in all_tasks),
            "successful_executions": sum(task.get('execution_count', 0) - task.get('failure_count', 0) 
                                        for task in all_tasks),
            "failed_executions": sum(task.get('failure_count', 0) for task in all_tasks)
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/{task_id}/executions")
async def get_task_executions(task_id: int, limit: int = 10):
    """Get execution history for a specific task"""
    try:
        executions = memory_manager.get_task_executions(task_id, limit)
        return {
            "task_id": task_id,
            "executions": executions,
            "total_shown": len(executions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/{task_id}/enable")
async def enable_scheduled_task(task_id: int):
    """Enable a scheduled task"""
    try:
        memory_manager.enable_scheduled_task(task_id)
        return {"message": f"Task {task_id} enabled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule/{task_id}/disable")
async def disable_scheduled_task(task_id: int):
    """Disable a scheduled task"""
    try:
        memory_manager.disable_scheduled_task(task_id)
        return {"message": f"Task {task_id} disabled successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/schedule/{task_id}")
async def update_scheduled_task(task_id: int, task_update: ScheduledTaskUpdate):
    """Update a scheduled task with full recurring support"""
    try:
        # Debug logging
        logger.info(f"Updating task {task_id} with data: {task_update.dict(exclude_unset=True)}")
        
        # Get current task
        all_tasks = memory_manager.get_all_scheduled_tasks()
        current_task = next((task for task in all_tasks if task['id'] == task_id), None)
        
        if not current_task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Convert the update data, handling datetime conversion
        update_dict = task_update.dict(exclude_unset=True)
        
        # Handle scheduled_time conversion if provided
        if 'scheduled_time' in update_dict and isinstance(update_dict['scheduled_time'], str):
            try:
                scheduled_time_str = update_dict['scheduled_time']
                if scheduled_time_str.endswith('Z'):
                    update_dict['scheduled_time'] = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
                else:
                    update_dict['scheduled_time'] = datetime.fromisoformat(scheduled_time_str)
                logger.info(f"Converted scheduled_time to: {update_dict['scheduled_time']}")
            except ValueError as e:
                logger.error(f"Error parsing scheduled_time: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid date format: {update_dict['scheduled_time']}")
        
        # Validate recurrence pattern if provided
        if update_dict.get('recurrence_pattern') and update_dict.get('recurrence_type'):
            if not memory_manager.validate_recurrence_pattern(
                update_dict['recurrence_pattern'], 
                update_dict['recurrence_type']
            ):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid recurrence pattern"
                )
        
        # Update the task using the enhanced method
        memory_manager.update_scheduled_task_fields(task_id, update_dict)
        
        logger.info(f"Successfully updated task {task_id}")
        
        return {
            "message": f"Task {task_id} updated successfully",
            "task_id": task_id,
            "updated_fields": list(update_dict.keys())
        }
        
    except ValueError as e:
        logger.error(f"Task not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedule/patterns/suggestions")
async def get_recurrence_pattern_suggestions():
    """Get suggested recurrence patterns for the UI"""
    simple_patterns = [
        {"pattern": "5m", "type": "simple", "description": "Every 5 minutes"},
        {"pattern": "15m", "type": "simple", "description": "Every 15 minutes"},
        {"pattern": "30m", "type": "simple", "description": "Every 30 minutes"},
        {"pattern": "1h", "type": "simple", "description": "Every hour"},
        {"pattern": "2h", "type": "simple", "description": "Every 2 hours"},
        {"pattern": "6h", "type": "simple", "description": "Every 6 hours"},
        {"pattern": "12h", "type": "simple", "description": "Every 12 hours"},
        {"pattern": "1d", "type": "simple", "description": "Every day"},
        {"pattern": "7d", "type": "simple", "description": "Every week"}
    ]
    
    cron_patterns = [
        {"pattern": "*/5 * * * *", "type": "cron", "description": "Every 5 minutes"},
        {"pattern": "0 * * * *", "type": "cron", "description": "Every hour"},
        {"pattern": "0 */6 * * *", "type": "cron", "description": "Every 6 hours"},
        {"pattern": "0 9 * * *", "type": "cron", "description": "Daily at 9:00 AM"},
        {"pattern": "0 9 * * 1", "type": "cron", "description": "Weekly on Monday at 9:00 AM"},
        {"pattern": "0 9 1 * *", "type": "cron", "description": "Monthly on 1st at 9:00 AM"},
        {"pattern": "0 0 * * 0", "type": "cron", "description": "Weekly on Sunday at midnight"},
        {"pattern": "0 0 1 1 *", "type": "cron", "description": "Yearly on January 1st at midnight"}
    ]
    
    return {
        "simple_patterns": simple_patterns,
        "cron_patterns": cron_patterns
    }

class PatternValidationRequest(BaseModel):
    """Request model for pattern validation"""
    pattern: str = Field(..., description="Pattern to validate")
    pattern_type: str = Field(..., description="Pattern type: simple or cron")

@app.post("/schedule/patterns/validate")
async def validate_recurrence_pattern(request: PatternValidationRequest):
    """Validate a recurrence pattern"""
    try:
        is_valid = memory_manager.validate_recurrence_pattern(request.pattern, request.pattern_type)
        
        result = {
            "pattern": request.pattern,
            "pattern_type": request.pattern_type,
            "is_valid": is_valid
        }
        
        if is_valid:
            # Calculate next few execution times as preview
            try:
                base_time = datetime.utcnow()
                next_executions = []
                
                for i in range(3):  # Show next 3 executions
                    if request.pattern_type == "cron":
                        from croniter import croniter
                        cron = croniter(request.pattern, base_time)
                        next_time = cron.get_next(datetime)
                    else:  # simple
                        next_time = memory_manager._parse_simple_pattern(base_time, request.pattern)
                    
                    next_executions.append(next_time.isoformat())
                    base_time = next_time
                
                result["next_executions_preview"] = next_executions
                
            except Exception as e:
                result["preview_error"] = str(e)
        
        return result
        
    except Exception as e:
        return {
            "pattern": request.pattern,
            "pattern_type": request.pattern_type,
            "is_valid": False,
            "error": str(e)
        }


# Backup and Restore Endpoints
class BackupExportRequest(BaseModel):
    """Request model for backup export"""
    export_path: Optional[str] = Field(default="backups", description="Directory path to save the backup files")
    include_memory: Optional[bool] = Field(default=False, description="Whether to include agent memory/conversation history")
    include_config: Optional[bool] = Field(default=True, description="Whether to include system configuration")
    include_tools: Optional[bool] = Field(default=True, description="Whether to include tool definitions")
    include_scheduled_tasks: Optional[bool] = Field(default=True, description="Whether to include scheduled tasks")
    create_zip: Optional[bool] = Field(default=True, description="Whether to create a zip file containing all exports")
    backup_name: Optional[str] = Field(default=None, description="Custom name for the backup")

class BackupImportRequest(BaseModel):
    """Request model for backup import"""
    backup_path: str = Field(..., description="Path to backup directory or zip file")
    import_agents: Optional[bool] = Field(default=True, description="Whether to import agents")
    import_workflows: Optional[bool] = Field(default=True, description="Whether to import workflows")
    import_tools: Optional[bool] = Field(default=True, description="Whether to import tool definitions")
    import_scheduled_tasks: Optional[bool] = Field(default=True, description="Whether to import scheduled tasks")
    import_memory: Optional[bool] = Field(default=False, description="Whether to import agent memory/conversation history")
    overwrite_existing: Optional[bool] = Field(default=False, description="Whether to overwrite existing entities with the same name")
    dry_run: Optional[bool] = Field(default=False, description="Whether to perform a dry run without actually importing")

@app.post("/backup/export")
async def export_backup(request: BackupExportRequest):
    """Export agents, workflows, tools, and configuration to backup files"""
    try:
        # Create backup directory
        backup_dir = Path(request.export_path or "backups")
        backup_dir.mkdir(exist_ok=True)
        
        # Generate backup name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = request.backup_name or f"backup_{timestamp}"
        backup_path = backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        backup_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "backup_name": backup_name,
                "options": request.dict()
            },
            "agents": [],
            "workflows": [],
            "tools": [],
            "scheduled_tasks": [],
            "config": {}
        }
        
        # Export agents
        if True:  # Always export agents
            agents = memory_manager.get_all_agents()
            backup_data["agents"] = agents
            logger.info(f"Exported {len(agents)} agents")
        
        # Export workflows
        if True:  # Always export workflows
            workflows = memory_manager.get_all_workflows()
            backup_data["workflows"] = workflows
            logger.info(f"Exported {len(workflows)} workflows")
        
        # Export tools
        if request.include_tools:
            tools = memory_manager.get_all_tools()
            backup_data["tools"] = tools
            logger.info(f"Exported {len(tools)} tools")
        
        # Export scheduled tasks
        if request.include_scheduled_tasks:
            scheduled_tasks = memory_manager.get_all_scheduled_tasks()
            backup_data["scheduled_tasks"] = scheduled_tasks
            logger.info(f"Exported {len(scheduled_tasks)} scheduled tasks")
        
        # Export configuration
        if request.include_config:
            backup_data["config"] = {
                "llm_config": config.llm_config,
                "database_path": config.database_path,
                "tools_directory": config.tools_directory,
                "api_host": config.api_host,
                "api_port": config.api_port,
                "max_agent_memory_entries": config.max_agent_memory_entries,
                "memory_cleanup_interval": config.memory_cleanup_interval
            }
            logger.info("Exported system configuration")
        
        # Export memory if requested
        if request.include_memory:
            memory_data = {}
            for agent in agents:
                agent_name = agent["name"]
                memory_entries = memory_manager.get_agent_memory(agent_name, limit=1000)
                memory_data[agent_name] = memory_entries
            backup_data["memory"] = memory_data
            logger.info(f"Exported memory for {len(agents)} agents")
        
        # Save backup data
        backup_file = backup_path / "backup.json"
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        # Create zip file if requested
        zip_path = None
        if request.create_zip:
            zip_path = backup_dir / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            # Remove the directory if zip was created
            import shutil
            shutil.rmtree(backup_path)
            logger.info(f"Created zip backup: {zip_path}")
        
        return {
            "status": "success",
            "message": f"Backup '{backup_name}' created successfully",
            "backup_name": backup_name,
            "backup_path": str(zip_path if zip_path else backup_path),
            "backup_type": "zip" if zip_path else "directory",
            "exported_items": {
                "agents": len(backup_data["agents"]),
                "workflows": len(backup_data["workflows"]),
                "tools": len(backup_data["tools"]),
                "scheduled_tasks": len(backup_data["scheduled_tasks"]),
                "include_memory": request.include_memory,
                "include_config": request.include_config
            }
        }
        
    except Exception as e:
        logger.error(f"Error during backup export: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backup/import")
async def import_backup(
    file: UploadFile = File(...),
    options: str = Form(...)
):
    """Import agents, workflows, tools, and configuration from backup files"""
    try:
        # Parse import options
        import_options = json.loads(options)
        
        # Create temporary directory for uploaded file
        temp_dir = Path("temp_imports")
        temp_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = temp_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # Extract backup data
            backup_data = None
            
            # Check if it's a zip file
            if file.filename.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    if 'backup.json' in zipf.namelist():
                        with zipf.open('backup.json') as f:
                            backup_data = json.load(f)
                    else:
                        raise HTTPException(status_code=400, detail="Invalid backup file: backup.json not found")
            else:
                # Assume it's a JSON file
                with open(file_path, 'r') as f:
                    backup_data = json.load(f)
            
            if not backup_data:
                raise HTTPException(status_code=400, detail="Invalid backup file: could not read backup data")
            
            # Validate backup structure
            required_keys = ["metadata", "agents", "workflows"]
            missing_keys = [key for key in required_keys if key not in backup_data]
            if missing_keys:
                raise HTTPException(status_code=400, detail=f"Invalid backup file: missing keys: {missing_keys}")
            
            # Perform dry run if requested
            if import_options.get("dry_run", False):
                return {
                    "status": "success",
                    "message": "Dry run completed successfully",
                    "dry_run": True,
                    "import_summary": {
                        "agents": len(backup_data.get("agents", [])),
                        "workflows": len(backup_data.get("workflows", [])),
                        "tools": len(backup_data.get("tools", [])),
                        "scheduled_tasks": len(backup_data.get("scheduled_tasks", [])),
                        "include_memory": bool(backup_data.get("memory")),
                        "include_config": bool(backup_data.get("config"))
                    }
                }
            
            # Import agents
            imported_agents = 0
            if import_options.get("import_agents", True):
                for agent in backup_data.get("agents", []):
                    try:
                        # Check if agent already exists
                        existing_agent = memory_manager.get_agent(agent["name"])
                        if existing_agent and not import_options.get("overwrite_existing", False):
                            logger.warning(f"Agent '{agent['name']}' already exists, skipping")
                            continue
                        
                        # Import agent
                        memory_manager.register_agent(
                            name=agent["name"],
                            role=agent.get("role", ""),
                            goals=agent.get("goals", ""),
                            backstory=agent.get("backstory", ""),
                            tools=agent.get("tools", []),
                            ollama_model=agent.get("ollama_model", "llama3"),
                            enabled=agent.get("enabled", True),
                            tool_configs=agent.get("tool_configs", {})
                        )
                        imported_agents += 1
                        logger.info(f"Imported agent: {agent['name']}")
                    except Exception as e:
                        logger.error(f"Failed to import agent {agent['name']}: {e}")
            
            # Import workflows
            imported_workflows = 0
            if import_options.get("import_workflows", True):
                for workflow in backup_data.get("workflows", []):
                    try:
                        # Check if workflow already exists
                        existing_workflow = memory_manager.get_workflow(workflow["name"])
                        if existing_workflow and not import_options.get("overwrite_existing", False):
                            logger.warning(f"Workflow '{workflow['name']}' already exists, skipping")
                            continue
                        
                        # Import workflow
                        memory_manager.register_workflow(
                            name=workflow["name"],
                            description=workflow.get("description", ""),
                            steps=workflow.get("steps", []),
                            enabled=workflow.get("enabled", True),
                            input_schema=workflow.get("input_schema", {}),
                            output_spec=workflow.get("output_spec", {})
                        )
                        imported_workflows += 1
                        logger.info(f"Imported workflow: {workflow['name']}")
                    except Exception as e:
                        logger.error(f"Failed to import workflow {workflow['name']}: {e}")
            
            # Import tools
            imported_tools = 0
            if import_options.get("import_tools", True):
                for tool in backup_data.get("tools", []):
                    try:
                        # Check if tool already exists
                        existing_tool = memory_manager.get_tool(tool["name"])
                        if existing_tool and not import_options.get("overwrite_existing", False):
                            logger.warning(f"Tool '{tool['name']}' already exists, skipping")
                            continue
                        
                        # Import tool
                        memory_manager.register_tool(
                            name=tool["name"],
                            description=tool.get("description", ""),
                            parameters_schema=tool.get("parameters_schema", {}),
                            class_name=tool.get("class_name", ""),
                            enabled=tool.get("enabled", True)
                        )
                        imported_tools += 1
                        logger.info(f"Imported tool: {tool['name']}")
                    except Exception as e:
                        logger.error(f"Failed to import tool {tool['name']}: {e}")
            
            # Import scheduled tasks
            imported_tasks = 0
            if import_options.get("import_scheduled_tasks", True):
                for task in backup_data.get("scheduled_tasks", []):
                    try:
                        # Import scheduled task
                        memory_manager.schedule_task(
                            task_type=task["task_type"],
                            scheduled_time=task["scheduled_time"],
                            agent_name=task.get("agent_name"),
                            workflow_name=task.get("workflow_name"),
                            task_description=task.get("task_description", ""),
                            context=task.get("context", {}),
                            is_recurring=task.get("is_recurring", False),
                            recurrence_pattern=task.get("recurrence_pattern"),
                            recurrence_type=task.get("recurrence_type", "simple"),
                            max_executions=task.get("max_executions"),
                            max_failures=task.get("max_failures", 3)
                        )
                        imported_tasks += 1
                        logger.info(f"Imported scheduled task: {task.get('agent_name', task.get('workflow_name', 'Unknown'))}")
                    except Exception as e:
                        logger.error(f"Failed to import scheduled task {task.get('agent_name', task.get('workflow_name', 'Unknown'))}: {e}")
            
            # Import memory if requested
            imported_memory = 0
            if import_options.get("import_memory", False) and "memory" in backup_data:
                for agent_name, memory_entries in backup_data["memory"].items():
                    try:
                        for entry in memory_entries:
                            memory_manager.add_memory_entry(
                                agent_name=agent_name,
                                role=entry["role"],
                                content=entry["content"],
                                metadata=entry.get("entry_metadata", {})
                            )
                        imported_memory += len(memory_entries)
                        logger.info(f"Imported {len(memory_entries)} memory entries for agent: {agent_name}")
                    except Exception as e:
                        logger.error(f"Failed to import memory for agent {agent_name}: {e}")
            
            return {
                "status": "success",
                "message": "Backup imported successfully",
                "import_summary": {
                    "agents": imported_agents,
                    "workflows": imported_workflows,
                    "tools": imported_tools,
                    "scheduled_tasks": imported_tasks,
                    "memory_entries": imported_memory
                }
            }
            
        finally:
            # Clean up temporary file
            if file_path.exists():
                file_path.unlink()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during backup import: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/list")
async def list_backups(backup_dir: str = "backups"):
    """List available backups"""
    try:
        backup_path = Path(backup_dir)
        if not backup_path.exists():
            logger.warning(f"Backup directory {backup_dir} does not exist")
            return {"backups": [], "message": f"Backup directory {backup_dir} does not exist"}
        
        backups = []
        logger.info(f"Scanning backup directory: {backup_path}")
        
        # Look for backup directories and zip files
        for item in backup_path.iterdir():
            logger.debug(f"Checking item: {item}")
            if item.is_dir():
                # Check if it's a backup directory (contains backup.json)
                backup_file = item / "backup.json"
                if backup_file.exists():
                    try:
                        with open(backup_file, 'r') as f:
                            backup_data = json.load(f)
                        metadata = backup_data.get("metadata", {})
                        backups.append({
                            "name": item.name,
                            "type": "directory",
                            "path": str(item),
                            "metadata": metadata
                        })
                        logger.info(f"Found backup directory: {item.name}")
                    except Exception as e:
                        logger.warning(f"Invalid backup file in directory {item.name}: {e}")
                        continue
            elif item.suffix == '.zip':
                # Check if it's a backup zip file
                try:
                    with zipfile.ZipFile(item, 'r') as zipf:
                        if 'backup.json' in zipf.namelist():
                            with zipf.open('backup.json') as f:
                                backup_data = json.load(f)
                            metadata = backup_data.get("metadata", {})
                            backups.append({
                                "name": item.stem,
                                "type": "zip",
                                "path": str(item),
                                "metadata": metadata
                            })
                            logger.info(f"Found backup zip: {item.name}")
                        else:
                            logger.debug(f"Zip file {item.name} does not contain backup.json")
                except Exception as e:
                    logger.warning(f"Invalid zip file {item.name}: {e}")
                    continue
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
        
        logger.info(f"Found {len(backups)} backups")
        return {
            "backups": backups,
            "total": len(backups),
            "backup_directory": str(backup_path)
        }
        
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/backup/download/{backup_name}")
async def download_backup(backup_name: str):
    """Download a backup as a zip file"""
    try:
        backup_dir = Path("backups")
        zip_path = backup_dir / f"{backup_name}.zip"
        
        if not zip_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")
        
        return FileResponse(
            path=str(zip_path),
            filename=f"{backup_name}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/backup/delete/{backup_name}")
async def delete_backup(backup_name: str):
    """Delete a backup"""
    try:
        backup_dir = Path("backups")
        backup_path = backup_dir / backup_name
        
        # Check if it's a directory
        if backup_path.is_dir():
            import shutil
            shutil.rmtree(backup_path)
        # Check if it's a zip file
        elif (backup_path.with_suffix('.zip')).exists():
            (backup_path.with_suffix('.zip')).unlink()
        else:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        return {"message": f"Backup '{backup_name}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=True
    )