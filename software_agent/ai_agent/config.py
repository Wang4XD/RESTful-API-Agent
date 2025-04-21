import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础配置
BASE_CONFIG = {
    "app_name": "Software AI Agent",
    "version": "1.0.0",
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
}

# 语言模型配置
LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "openai"),  # openai/anthropic/huggingface
    "model": os.getenv("LLM_MODEL", "gpt-4"),
    "api_key": os.getenv("LLM_API_KEY", ""),
    "api_base": os.getenv("LLM_API_BASE", ""),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
}

# API配置
API_CONFIG = {
    "base_url": os.getenv("API_BASE_URL", "https://api.yoursoftware.com"),
    "api_key": os.getenv("API_KEY", ""),
    "timeout": int(os.getenv("API_TIMEOUT", "30")),
    "retry_attempts": int(os.getenv("API_RETRY_ATTEMPTS", "3")),
    "retry_delay": int(os.getenv("API_RETRY_DELAY", "2")),
}

# Web服务配置
WEB_CONFIG = {
    "host": os.getenv("WEB_HOST", "0.0.0.0"),
    "port": int(os.getenv("WEB_PORT", "8000")),
    "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
    "auth_required": os.getenv("AUTH_REQUIRED", "True").lower() == "true",
    "jwt_secret": os.getenv("JWT_SECRET", "your-super-secret-key"),
    "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "jwt_expiration": int(os.getenv("JWT_EXPIRATION", "3600")),  # 1 hour
}