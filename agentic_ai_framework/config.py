"""
config.py - Enhanced Configuration with Multi-Provider Support
"""

import os
from typing import Dict, Any

class Config:
    """Enhanced configuration with multi-provider LLM support"""
    
    def __init__(self):
        # Core API Configuration
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.database_path = os.getenv("DATABASE_PATH", "data/agentic_ai.db")
        
        # Agent Configuration
        self.max_agent_iterations = int(os.getenv("MAX_AGENT_ITERATIONS", "10"))
        self.scheduler_interval = int(os.getenv("SCHEDULER_INTERVAL", "60"))
        self.tools_directory = os.getenv("TOOLS_DIRECTORY", "tools")
        
        # Memory Management Configuration
        self.max_agent_memory_entries = int(os.getenv("MAX_AGENT_MEMORY_ENTRIES", "20"))
        self.clear_memory_on_startup = os.getenv("CLEAR_MEMORY_ON_STARTUP", "false").lower() == "true"
        self.memory_cleanup_interval = int(os.getenv("MEMORY_CLEANUP_INTERVAL", "3600"))  # 1 hour
        self.memory_retention_days = int(os.getenv("MEMORY_RETENTION_DAYS", "7"))
        
        # Model Warmup Configuration
        self.model_warmup_timeout = int(os.getenv("MODEL_WARMUP_TIMEOUT", "60"))
        self.max_concurrent_warmups = int(os.getenv("MAX_CONCURRENT_WARMUPS", "2"))
        self.auto_warmup_on_startup = os.getenv("AUTO_WARMUP_ON_STARTUP", "true").lower() == "true"
        self.warmup_interval_hours = int(os.getenv("WARMUP_INTERVAL_HOURS", "6"))
        self.max_idle_hours = int(os.getenv("MAX_IDLE_HOURS", "24"))
        self.warmup_enabled = os.getenv("WARMUP_ENABLED", "true").lower() == "true"
        self.background_maintenance = os.getenv("BACKGROUND_MAINTENANCE", "true").lower() == "true"
        self.log_warmup_details = os.getenv("LOG_WARMUP_DETAILS", "true").lower() == "true"
        
        # LLM Provider Configuration
        self.llm_config = self._build_llm_config()
        
        # Logging Configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        
        # Backward compatibility properties
        # Handle missing Ollama provider gracefully
        if "ollama" in self.llm_config.get("providers", {}):
            self.ollama_url = self.llm_config["providers"]["ollama"]["url"]
        else:
            self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        self.default_model = self.llm_config.get("default_model", "gpt-3.5-turbo")
    
    def _build_llm_config(self) -> Dict[str, Any]:
        """Build LLM provider configuration from environment variables"""
        
        # Default provider configuration
        default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
        default_model = os.getenv("DEFAULT_MODEL", "granite3.2:2b")
        fallback_enabled = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"
        
        # Provider configurations
        providers = {}
        
        # Ollama Provider Configuration
        # Default to false for cloud deployments (Ollama requires local installation)
        # Can be explicitly enabled with OLLAMA_ENABLED=true for local deployments
        ollama_enabled_env = os.getenv("OLLAMA_ENABLED", "false")
        ollama_enabled = ollama_enabled_env.lower() == "true"
        if ollama_enabled:
            providers["ollama"] = {
                "enabled": True,
                "url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
                "timeout": int(os.getenv("OLLAMA_TIMEOUT", "300")),
                "default_model": os.getenv("OLLAMA_DEFAULT_MODEL", "granite3.2:2b")
            }
        
        # OpenAI Provider Configuration
        openai_enabled = os.getenv("OPENAI_ENABLED", "false").lower() == "true"
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if openai_enabled and openai_api_key:
            providers["openai"] = {
                "enabled": True,
                "api_key": openai_api_key,
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "organization": os.getenv("OPENAI_ORGANIZATION"),
                "timeout": int(os.getenv("OPENAI_TIMEOUT", "300")),
                "default_model": os.getenv("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
            }
        
        # OpenRouter Provider Configuration (for future implementation)
        openrouter_enabled = os.getenv("OPENROUTER_ENABLED", "false").lower() == "true"
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        if openrouter_enabled and openrouter_api_key:
            providers["openrouter"] = {
                "enabled": True,
                "api_key": openrouter_api_key,
                "base_url": os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                "timeout": int(os.getenv("OPENROUTER_TIMEOUT", "300")),
                "default_model": os.getenv("OPENROUTER_DEFAULT_MODEL", "openai/gpt-3.5-turbo")
            }
        
        # Bedrock Provider Configuration
        bedrock_enabled = os.getenv("BEDROCK_ENABLED", "false").lower() == "true"
        bedrock_access_key = os.getenv("BEDROCK_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
        bedrock_secret_key = os.getenv("BEDROCK_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if bedrock_enabled:
            providers["bedrock"] = {
                "enabled": True,
                "region_name": os.getenv("BEDROCK_REGION", "us-east-1"),
                "aws_access_key_id": bedrock_access_key,
                "aws_secret_access_key": bedrock_secret_key,
                "timeout": int(os.getenv("BEDROCK_TIMEOUT", "300")),
                "default_model": os.getenv("BEDROCK_DEFAULT_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0")
            }
        
        # Fallback order - ensure Ollama is first by default
        fallback_order = os.getenv("LLM_FALLBACK_ORDER", "ollama,bedrock,openai,openrouter").split(",")
        fallback_order = [p.strip() for p in fallback_order if p.strip()]
        
        # Ensure Ollama is in fallback order if enabled
        if ollama_enabled and "ollama" not in fallback_order:
            fallback_order.insert(0, "ollama")
        
        return {
            "default_provider": default_provider,
            "default_model": default_model,
            "fallback_enabled": fallback_enabled,
            "fallback_order": fallback_order,
            "providers": providers
        }
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        return self.llm_config.get("providers", {}).get(provider_name, {})
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled"""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.get("enabled", False)
    
    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled provider names"""
        enabled = []
        for provider_name, config in self.llm_config.get("providers", {}).items():
            if config.get("enabled", False):
                enabled.append(provider_name)
        return enabled
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            # Core API settings
            "api_host": self.api_host,
            "api_port": self.api_port,
            "database_path": self.database_path,
            
            # Agent settings
            "max_agent_iterations": self.max_agent_iterations,
            "scheduler_interval": self.scheduler_interval,
            "tools_directory": self.tools_directory,
            
            # Memory management settings
            "max_agent_memory_entries": self.max_agent_memory_entries,
            "clear_memory_on_startup": self.clear_memory_on_startup,
            "memory_cleanup_interval": self.memory_cleanup_interval,
            "memory_retention_days": self.memory_retention_days,
            
            # Model warmup settings
            "model_warmup_timeout": self.model_warmup_timeout,
            "max_concurrent_warmups": self.max_concurrent_warmups,
            "auto_warmup_on_startup": self.auto_warmup_on_startup,
            "warmup_interval_hours": self.warmup_interval_hours,
            "max_idle_hours": self.max_idle_hours,
            "warmup_enabled": self.warmup_enabled,
            "background_maintenance": self.background_maintenance,
            "log_warmup_details": self.log_warmup_details,
            
            # LLM provider settings
            "llm_config": self.llm_config,
            
            # Backward compatibility
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            
            # Logging settings
            "log_level": self.log_level,
            "log_format": self.log_format
        }
    
    def update(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        for key, value in updates.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif key == "llm_config":
                # Special handling for LLM config updates
                if isinstance(value, dict):
                    self.llm_config.update(value)
                    # Update backward compatibility properties
                    self.ollama_url = self.llm_config.get("providers", {}).get("ollama", {}).get("url", self.ollama_url)
                    self.default_model = self.llm_config.get("default_model", self.default_model)
            else:
                raise ValueError(f"Unknown configuration key: {key}")
    
    def validate(self):
        """Validate configuration values"""
        errors = []
        
        # Validate ports
        if not (1 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}")
        
        # Validate timeouts and intervals
        if self.max_agent_iterations < 1:
            errors.append(f"max_agent_iterations must be >= 1, got {self.max_agent_iterations}")
        
        if self.scheduler_interval < 30:
            errors.append(f"scheduler_interval must be >= 30, got {self.scheduler_interval}")
        
        if self.memory_cleanup_interval < 300:
            errors.append(f"memory_cleanup_interval must be >= 300, got {self.memory_cleanup_interval}")
        
        if self.model_warmup_timeout < 10:
            errors.append(f"model_warmup_timeout must be >= 10, got {self.model_warmup_timeout}")
        
        if self.max_concurrent_warmups < 1:
            errors.append(f"max_concurrent_warmups must be >= 1, got {self.max_concurrent_warmups}")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]