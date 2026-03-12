"""
Production Logging Configuration
================================
Structured logging with JSON formatting for production monitoring.
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict
import json
from pathlib import Path

from src.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Compatible with log aggregation systems (ELK, Datadog, etc.)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "goal_id"):
            log_data["goal_id"] = record.goal_id
        if hasattr(record, "agent_name"):
            log_data["agent_name"] = record.agent_name
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        
        return json.dumps(log_data)


def setup_logging():
    """
    Configure application logging.
    
    - Development: Human-readable console output
    - Production: JSON-formatted logs to file + stdout
    """
    settings = get_settings()
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if settings.DEBUG:
        # Development: Human-readable format
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)
    else:
        # Production: JSON format
        console_handler.setFormatter(JSONFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format)
    file_handler = logging.FileHandler(
        log_dir / f"agentic_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.FileHandler(log_dir / "errors.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(error_handler)
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logging.info("Logging configured", extra={
        "log_level": settings.LOG_LEVEL,
        "debug_mode": settings.DEBUG
    })


class RequestLogger:
    """
    Middleware for logging HTTP requests.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("api.requests")
    
    async def log_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None
    ):
        """Log HTTP request."""
        self.logger.info(
            f"{method} {path} - {status_code}",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "user_id": user_id
            }
        )


class AgentLogger:
    """
    Logger for agent execution tracking.
    """
    
    def __init__(self, agent_name: str, goal_id: str):
        self.logger = logging.getLogger(f"agents.{agent_name}")
        self.agent_name = agent_name
        self.goal_id = goal_id
    
    def log_start(self):
        """Log agent execution start."""
        self.logger.info(
            f"Agent {self.agent_name} started",
            extra={
                "agent_name": self.agent_name,
                "goal_id": self.goal_id,
                "event": "agent_start"
            }
        )
    
    def log_progress(self, step: str, progress: int):
        """Log agent progress."""
        self.logger.info(
            f"Agent {self.agent_name}: {step} ({progress}%)",
            extra={
                "agent_name": self.agent_name,
                "goal_id": self.goal_id,
                "step": step,
                "progress": progress,
                "event": "agent_progress"
            }
        )
    
    def log_completion(self, duration_seconds: float, success: bool):
        """Log agent completion."""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"Agent {self.agent_name} {'completed' if success else 'failed'}",
            extra={
                "agent_name": self.agent_name,
                "goal_id": self.goal_id,
                "duration_seconds": duration_seconds,
                "success": success,
                "event": "agent_complete"
            }
        )
    
    def log_error(self, error: Exception):
        """Log agent error."""
        self.logger.error(
            f"Agent {self.agent_name} error: {str(error)}",
            extra={
                "agent_name": self.agent_name,
                "goal_id": self.goal_id,
                "error": str(error),
                "event": "agent_error"
            },
            exc_info=True
        )
