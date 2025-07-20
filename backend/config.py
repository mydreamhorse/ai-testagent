from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./test.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_prefix: str = "/api/v1"
    
    # File upload
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    # OpenAI (for development)
    openai_api_key: str = ""
    use_proxy: bool = True
    
    # Model settings
    ai_model_cache_dir: str = "models"
    batch_size: int = 32
    max_length: int = 512
    
    # Proxy settings (optional, read from environment)
    http_proxy: str = ""
    https_proxy: str = ""
    no_proxy: str = ""
    
    model_config = {
        "env_file": ".env",
        "extra": "allow",  # Allow extra fields from environment
        "protected_namespaces": ("settings_",)  # Fix the protected namespace warning
    }


settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.ai_model_cache_dir, exist_ok=True)