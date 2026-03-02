"""
Tool Registry
============

Extensible tool system for agents:
- Base Tool class with error handling
- Automatic retries with exponential backoff
- Cost tracking
- Permission system
- Tool discovery
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from enum import Enum

from backend.src.core.config import get_settings
from backend.src.database.models import ToolExecution
from backend.src.database.session import AsyncSession


settings = get_settings()


class ToolCategory(Enum):
    """Tool categories"""
    DATA_GATHERING = "data_gathering"
    ANALYTICS = "analytics"
    COMMUNICATION = "communication"
    CREATION = "creation"
    VALIDATION = "validation"
    RESEARCH = "research"


class ToolPermission(Enum):
    """Permission levels"""
    AUTO = "auto"  # Execute automatically
    CHECKPOINT = "checkpoint"  # Requires human approval
    ADMIN = "admin"  # Admin only


class BaseTool(ABC):
    """
    Base class for all tools.
    
    Provides:
    - Error handling
    - Automatic retries
    - Cost tracking
    - Execution logging
    """
    
    # Subclasses must override these
    name: str = "base_tool"
    description: str = "Base tool class"
    category: ToolCategory = ToolCategory.DATA_GATHERING
    permission: ToolPermission = ToolPermission.AUTO
    cost_per_execution: float = 0.0
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    @abstractmethod
    async def execute(
        self,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            params: Tool-specific parameters
            
        Returns:
            Dict with tool output
            
        Raises:
            ToolExecutionError on failure
        """
        pass
    
    async def run(
        self,
        params: Dict[str, Any],
        session: Optional[AsyncSession] = None,
        goal_id: Optional[str] = None,
        agent_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run tool with error handling, retries, and logging.
        
        Args:
            params: Tool parameters
            session: Database session for logging
            goal_id: Associated research goal
            agent_name: Agent executing this tool
            
        Returns:
            Tool execution result with metadata
        """
        start_time = datetime.utcnow()
        
        # Create execution record
        execution = None
        if session:
            execution = ToolExecution(
                tool_name=self.name,
                tool_category=self.category.value,
                goal_id=goal_id,
                agent_name=agent_name,
                input_params=params,
                status="pending",
            )
            session.add(execution)
            await session.commit()
        
        # Execute with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Execute tool
                result = await self.execute(params)
                
                # Success
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                
                if execution:
                    execution.status = "success"
                    execution.output_data = result
                    execution.duration_seconds = duration
                    execution.cost_usd = self.cost_per_execution
                    execution.completed_at = end_time
                    await session.commit()
                
                return {
                    "success": True,
                    "output": result,
                    "tool": self.name,
                    "duration_seconds": duration,
                    "cost_usd": self.cost_per_execution,
                    "attempts": attempt + 1,
                }
            
            except Exception as e:
                last_error = e
                
                if execution:
                    execution.retry_count = attempt + 1
                    await session.commit()
                
                # Last attempt failed
                if attempt == self.max_retries - 1:
                    break
                
                # Wait before retry (exponential backoff)
                await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        # All retries failed
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        if execution:
            execution.status = "failed"
            execution.error_message = str(last_error)
            execution.duration_seconds = duration
            execution.completed_at = end_time
            await session.commit()
        
        return {
            "success": False,
            "error": str(last_error),
            "tool": self.name,
            "duration_seconds": duration,
            "attempts": self.max_retries,
        }
    
    def validate_params(self, params: Dict[str, Any]) -> None:
        """
        Validate input parameters.
        
        Subclasses can override for custom validation.
        
        Raises:
            ValueError if params are invalid
        """
        pass


# =====================
# Example Tools
# =====================

class WebScraperTool(BaseTool):
    """Tool for scraping websites"""
    
    name = "web_scraper"
    description = "Scrape content from websites"
    category = ToolCategory.DATA_GATHERING
    permission = ToolPermission.AUTO
    cost_per_execution = 0.0
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scrape a website"""
        url = params.get("url", "")
        
        if not url:
            raise ValueError("URL is required")
        
        # For MVP: simulate scraping
        # In production: use BeautifulSoup/Playwright
        
        return {
            "url": url,
            "content": f"Simulated content from {url}",
            "scraped_at": datetime.utcnow().isoformat(),
            "status": "simulated",
        }


class CSVAnalyzerTool(BaseTool):
    """Tool for analyzing CSV files"""
    
    name = "csv_analyzer"
    description = "Analyze CSV data and extract insights"
    category = ToolCategory.ANALYTICS
    permission = ToolPermission.AUTO
    cost_per_execution = 0.0
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CSV data"""
        file_path = params.get("file_path", "")
        
        if not file_path:
            raise ValueError("file_path is required")
        
        # For MVP: simulate analysis
        # In production: use pandas
        
        return {
            "file_path": file_path,
            "rows": 1000,
            "columns": 10,
            "insights": ["Simulated insight 1", "Simulated insight 2"],
            "analyzed_at": datetime.utcnow().isoformat(),
        }


class EmailTool(BaseTool):
    """Tool for sending emails"""
    
    name = "email_sender"
    description = "Send emails to stakeholders"
    category = ToolCategory.COMMUNICATION
    permission = ToolPermission.CHECKPOINT  # Requires approval
    cost_per_execution = 0.0
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send an email"""
        to = params.get("to", "")
        subject = params.get("subject", "")
        body = params.get("body", "")
        
        if not all([to, subject, body]):
            raise ValueError("to, subject, and body are required")
        
        # For MVP: simulate email
        # In production: use SMTP or email service
        
        return {
            "to": to,
            "subject": subject,
            "sent_at": datetime.utcnow().isoformat(),
            "status": "simulated",
        }


# =====================
# Tool Registry
# =====================

class ToolRegistry:
    """
    Central registry for all available tools.
    
    Provides:
    - Tool discovery
    - Tool execution
    - Permission checking
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools"""
        self.register(WebScraperTool())
        self.register(CSVAnalyzerTool())
        self.register(EmailTool())
    
    def register(self, tool: BaseTool) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool
        print(f"✅ Registered tool: {tool.name} ({tool.category.value})")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
    ) -> List[Dict[str, Any]]:
        """List all available tools"""
        tools = []
        
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "permission": tool.permission.value,
                "cost": tool.cost_per_execution,
            })
        
        return tools
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        session: Optional[AsyncSession] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            params: Tool parameters
            session: Database session
            **kwargs: Additional arguments (goal_id, agent_name, etc.)
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
            }
        
        return await tool.run(params, session, **kwargs)
    
    def check_permission(
        self,
        tool_name: str,
        autonomy_level: str,
    ) -> bool:
        """
        Check if tool can be executed given autonomy level.
        
        Args:
            tool_name: Tool to check
            autonomy_level: Current autonomy level
            
        Returns:
            True if execution allowed, False if checkpoint needed
        """
        tool = self.get_tool(tool_name)
        
        if not tool:
            return False
        
        # AUTO tools always allowed
        if tool.permission == ToolPermission.AUTO:
            return True
        
        # CHECKPOINT tools depend on autonomy level
        if tool.permission == ToolPermission.CHECKPOINT:
            return autonomy_level == "full"
        
        # ADMIN tools never auto-execute
        return False


# =====================
# Global Instance
# =====================

_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


# Export for convenience
tool_registry = get_tool_registry()


# =====================
# Convenience Functions
# =====================

async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """Execute a tool (convenience function)"""
    return await tool_registry.execute_tool(tool_name, params, **kwargs)


def list_available_tools(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all tools (convenience function)"""
    cat = ToolCategory(category) if category else None
    return tool_registry.list_tools(cat)
