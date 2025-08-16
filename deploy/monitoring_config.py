"""
智能测试报告系统监控配置
"""

import os
from typing import Dict, List, Any

# 监控配置
MONITORING_CONFIG = {
    # 系统指标监控
    "system_metrics": {
        "enabled": True,
        "collection_interval": 30,  # 秒
        "metrics": [
            "cpu_usage",
            "memory_usage", 
            "disk_usage",
            "network_io",
            "process_count"
        ]
    },
    
    # 应用指标监控
    "application_metrics": {
        "enabled": True,
        "collection_interval": 10,  # 秒
        "metrics": [
            "request_count",
            "response_time",
            "error_rate",
            "active_connections",
            "queue_size"
        ]
    },
    
    # 业务指标监控
    "business_metrics": {
        "enabled": True,
        "collection_interval": 60,  # 秒
        "metrics": [
            "test_execution_count",
            "report_generation_count",
            "user_activity",
            "data_processing_time"
        ]
    }
}

# 告警规则配置
ALERT_RULES = [
    {
        "name": "high_cpu_usage",
        "metric": "cpu_usage",
        "condition": "greater_than",
        "threshold": 80.0,
        "duration": "5m",
        "severity": "warning",
        "description": "CPU使用率过高"
    },
    {
        "name": "high_memory_usage", 
        "metric": "memory_usage",
        "condition": "greater_than",
        "threshold": 85.0,
        "duration": "5m",
        "severity": "warning",
        "description": "内存使用率过高"
    },
    {
        "name": "high_error_rate",
        "metric": "error_rate",
        "condition": "greater_than",
        "threshold": 5.0,
        "duration": "2m",
        "severity": "critical",
        "description": "错误率过高"
    },
    {
        "name": "slow_response_time",
        "metric": "response_time_p95",
        "condition": "greater_than", 
        "threshold": 2000.0,  # ms
        "duration": "3m",
        "severity": "warning",
        "description": "响应时间过长"
    },
    {
        "name": "low_disk_space",
        "metric": "disk_usage",
        "condition": "greater_than",
        "threshold": 90.0,
        "duration": "1m",
        "severity": "critical",
        "description": "磁盘空间不足"
    }
]

# 通知配置
NOTIFICATION_CONFIG = {
    "channels": {
        "email": {
            "enabled": True,
            "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_address": os.getenv("SMTP_FROM", "noreply@example.com")
        },
        "webhook": {
            "enabled": True,
            "url": os.getenv("WEBHOOK_URL", ""),
            "timeout": 10
        },
        "log": {
            "enabled": True,
            "log_level": "INFO"
        }
    },
    
    "recipients": {
        "critical": ["admin@example.com", "ops@example.com"],
        "warning": ["admin@example.com"],
        "info": ["admin@example.com"]
    },
    
    "rate_limiting": {
        "enabled": True,
        "max_alerts_per_hour": 10,
        "cooldown_period": 300  # 秒
    }
}

# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "level": "INFO",
            "formatter": "detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/monitoring.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "monitoring": {
            "level": "INFO",
            "handlers": ["default", "file"],
            "propagate": False
        }
    }
}

# 健康检查配置
HEALTH_CHECK_CONFIG = {
    "endpoints": [
        {
            "name": "backend_api",
            "url": "http://localhost:8000/health",
            "timeout": 5,
            "interval": 30
        },
        {
            "name": "frontend",
            "url": "http://localhost:3000",
            "timeout": 5,
            "interval": 60
        },
        {
            "name": "database",
            "type": "database",
            "connection_string": os.getenv("DATABASE_URL", "sqlite:///./test.db"),
            "timeout": 10,
            "interval": 60
        },
        {
            "name": "redis",
            "type": "redis",
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "timeout": 5,
            "interval": 30
        }
    ]
}

# 性能监控配置
PERFORMANCE_CONFIG = {
    "profiling": {
        "enabled": os.getenv("PROFILING_ENABLED", "false").lower() == "true",
        "sample_rate": 0.1,  # 10%采样率
        "output_dir": "logs/profiling"
    },
    
    "tracing": {
        "enabled": os.getenv("TRACING_ENABLED", "false").lower() == "true",
        "service_name": "intelligent-test-reporting",
        "jaeger_endpoint": os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
    },
    
    "metrics_export": {
        "prometheus": {
            "enabled": True,
            "port": 9090,
            "path": "/metrics"
        },
        "statsd": {
            "enabled": False,
            "host": "localhost",
            "port": 8125
        }
    }
}

def get_config() -> Dict[str, Any]:
    """获取完整的监控配置"""
    return {
        "monitoring": MONITORING_CONFIG,
        "alerts": ALERT_RULES,
        "notifications": NOTIFICATION_CONFIG,
        "logging": LOGGING_CONFIG,
        "health_checks": HEALTH_CHECK_CONFIG,
        "performance": PERFORMANCE_CONFIG
    }