"""
Real PostHog Analytics Connector
=================================

Production-grade PostHog integration:
- Query events and insights
- Build funnels
- Get user properties
- Track feature flags
- Session recordings
"""

import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.src.core.config import get_settings


settings = get_settings()


class PostHogConnector:
    """
    Real PostHog API connector.
    
    Requires:
    - POSTHOG_API_KEY (environment variable)
    - POSTHOG_PROJECT_ID (environment variable)
    """
    
    def __init__(self):
        self.api_key = settings.posthog_api_key
        self.project_id = settings.posthog_project_id
        self.base_url = "https://app.posthog.com/api"
        
        if not self.api_key or not self.project_id:
            raise ValueError(
                "PostHog credentials not configured. "
                "Set POSTHOG_API_KEY and POSTHOG_PROJECT_ID in .env"
            )
    
    async def query_events(
        self,
        event_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Query events from PostHog.
        
        Args:
            event_name: Filter by specific event (e.g., "button_clicked")
            date_from: Start date (default: 30 days ago)
            date_to: End date (default: now)
            properties: Filter by event properties
            limit: Maximum events to return
            
        Returns:
            Dict with events and metadata
        """
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        url = f"{self.base_url}/projects/{self.project_id}/events"
        
        params = {
            "limit": limit,
            "after": date_from.isoformat(),
            "before": date_to.isoformat(),
        }
        
        if event_name:
            params["event"] = event_name
        
        if properties:
            params["properties"] = properties
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "events": data.get("results", []),
                        "count": len(data.get("results", [])),
                        "next": data.get("next"),
                        "date_range": {
                            "from": date_from.isoformat(),
                            "to": date_to.isoformat(),
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"PostHog API error: {response.status}",
                        "details": error_text
                    }
    
    async def query_insights(
        self,
        insight_type: str = "TRENDS",
        events: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        interval: str = "day",
        breakdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query insights (trends, funnels, retention, etc.).
        
        Args:
            insight_type: "TRENDS", "FUNNELS", "RETENTION", "PATHS"
            events: List of events to analyze
            date_from: Start date (e.g., "-30d" or "2024-01-01")
            date_to: End date (e.g., "2024-01-31")
            interval: "hour", "day", "week", "month"
            breakdown: Property to break down by
            
        Returns:
            Dict with insight results
        """
        url = f"{self.base_url}/projects/{self.project_id}/insights"
        
        if not date_from:
            date_from = "-30d"
        if not date_to:
            date_to = datetime.utcnow().strftime("%Y-%m-%d")
        
        payload = {
            "insight": insight_type,
            "date_from": date_from,
            "date_to": date_to,
            "interval": interval,
        }
        
        if events:
            payload["events"] = [{"id": event} for event in events]
        
        if breakdown:
            payload["breakdown"] = breakdown
            payload["breakdown_type"] = "event"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    
                    return {
                        "success": True,
                        "insight_type": insight_type,
                        "results": data.get("result", []),
                        "metadata": {
                            "date_from": date_from,
                            "date_to": date_to,
                            "interval": interval,
                        }
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"PostHog API error: {response.status}",
                        "details": error_text
                    }
    
    async def build_funnel(
        self,
        steps: List[str],
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        breakdown: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build conversion funnel.
        
        Args:
            steps: List of event names in order
            date_from: Start date
            date_to: End date
            breakdown: Property to segment by
            
        Returns:
            Dict with funnel analysis
        """
        if not date_from:
            date_from = "-30d"
        
        payload = {
            "insight": "FUNNELS",
            "date_from": date_from,
            "date_to": date_to or datetime.utcnow().strftime("%Y-%m-%d"),
            "events": [{"id": event, "order": i} for i, event in enumerate(steps)],
        }
        
        if breakdown:
            payload["breakdown"] = breakdown
        
        url = f"{self.base_url}/projects/{self.project_id}/insights"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    
                    # Parse funnel results
                    results = data.get("result", [])
                    
                    funnel_steps = []
                    for i, step_name in enumerate(steps):
                        step_data = results[i] if i < len(results) else {}
                        
                        funnel_steps.append({
                            "step": i + 1,
                            "name": step_name,
                            "count": step_data.get("count", 0),
                            "conversion_rate": step_data.get("conversion_rate", 0),
                        })
                    
                    return {
                        "success": True,
                        "funnel_steps": funnel_steps,
                        "overall_conversion": funnel_steps[-1]["conversion_rate"] if funnel_steps else 0,
                        "biggest_drop": self._find_biggest_drop(funnel_steps),
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"PostHog API error: {response.status}",
                        "details": error_text
                    }
    
    async def get_user_properties(
        self,
        distinct_id: str,
    ) -> Dict[str, Any]:
        """Get properties for a specific user."""
        
        url = f"{self.base_url}/projects/{self.project_id}/persons"
        
        params = {"distinct_id": distinct_id}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    
                    if results:
                        person = results[0]
                        return {
                            "success": True,
                            "distinct_id": distinct_id,
                            "properties": person.get("properties", {}),
                            "created_at": person.get("created_at"),
                        }
                    else:
                        return {
                            "success": False,
                            "error": "User not found"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"PostHog API error: {response.status}"
                    }
    
    async def get_feature_flags(self) -> Dict[str, Any]:
        """Get all feature flags for the project."""
        
        url = f"{self.base_url}/projects/{self.project_id}/feature_flags"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    flags = []
                    for flag in data.get("results", []):
                        flags.append({
                            "key": flag.get("key"),
                            "name": flag.get("name"),
                            "active": flag.get("active"),
                            "rollout_percentage": flag.get("rollout_percentage"),
                        })
                    
                    return {
                        "success": True,
                        "flags": flags,
                        "count": len(flags),
                    }
                else:
                    return {
                        "success": False,
                        "error": f"PostHog API error: {response.status}"
                    }
    
    # Helper methods
    
    def _find_biggest_drop(self, funnel_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the step with the biggest drop-off."""
        if len(funnel_steps) < 2:
            return {}
        
        biggest_drop = {
            "from_step": 0,
            "to_step": 0,
            "drop_rate": 0,
        }
        
        for i in range(len(funnel_steps) - 1):
            current_rate = funnel_steps[i]["conversion_rate"]
            next_rate = funnel_steps[i + 1]["conversion_rate"]
            drop_rate = current_rate - next_rate
            
            if drop_rate > biggest_drop["drop_rate"]:
                biggest_drop = {
                    "from_step": i + 1,
                    "to_step": i + 2,
                    "from_name": funnel_steps[i]["name"],
                    "to_name": funnel_steps[i + 1]["name"],
                    "drop_rate": drop_rate,
                }
        
        return biggest_drop


# Singleton instance
_posthog_connector: Optional[PostHogConnector] = None


def get_posthog_connector() -> PostHogConnector:
    """Get or create PostHog connector singleton."""
    global _posthog_connector
    
    if _posthog_connector is None:
        if settings.is_demo_mode or not settings.posthog_api_key:
            raise ValueError(
                "PostHog not available in demo mode. "
                "Set POSTHOG_API_KEY and POSTHOG_PROJECT_ID to use real mode."
            )
        _posthog_connector = PostHogConnector()
    
    return _posthog_connector
