"""
Data Agent
==========

Specialized agent for data collection and analysis.

Capabilities:
- Analyze CSV/Excel uploads
- Generate demo data (in demo mode)
- Extract insights from data
- Statistical analysis
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from backend.src.agents.base import BaseAgent
from backend.src.core.ai_manager import get_ai_manager
from backend.src.core.config import get_settings


settings = get_settings()
ai_manager = get_ai_manager()


class DataAgent(BaseAgent):
    """
    Data collection and analysis agent.
    
    In Demo Mode:
    - Generates realistic synthetic data using LLM
    - Creates believable analytics insights
    
    In Real Mode:
    - Connects to actual analytics APIs
    - Processes uploaded CSV/Excel files
    - Runs statistical analysis
    """
    
    agent_name = "data_agent"
    agent_description = "Collects and analyzes product data"
    required_tools = ["csv_analyzer", "web_scraper"]
    
    async def execute(self) -> Dict[str, Any]:
        """
        Main data agent execution.
        
        Workflow:
        1. Understand what data is needed
        2. Collect data (demo or real)
        3. Analyze data
        4. Extract insights
        """
        await self.update_progress("Planning data collection", 10)
        
        # Step 1: Plan data collection
        plan = await self._plan_data_collection()
        
        await self.update_progress("Collecting data", 30)
        
        # Step 2: Collect data
        if settings.is_demo_mode:
            data = await self._generate_demo_data(plan)
        else:
            data = await self._collect_real_data(plan)
        
        await self.update_progress("Analyzing data", 60)
        
        # Step 3: Analyze data
        insights = await self._analyze_data(data)
        
        await self.update_progress("Extracting insights", 90)
        
        # Step 4: Generate final output
        output = await self._generate_output(data, insights)
        
        await self.update_progress("Complete", 100)
        
        return output
    
    # =====================
    # Planning
    # =====================
    
    async def _plan_data_collection(self) -> Dict[str, Any]:
        """
        Plan what data to collect based on goal.
        
        Returns:
            Dict with data collection plan
        """
        prompt = f"""
Analyze this research goal and plan data collection:

GOAL: "{self.goal.description}"

Plan what data we need:
1. What type of data? (analytics, user feedback, competitive, etc.)
2. What metrics are relevant?
3. What timeframe?
4. What granularity?

Return JSON:
{{
    "data_types": ["analytics", "user_feedback"],
    "metrics": ["activation_rate", "churn_rate"],
    "timeframe": "last_30_days",
    "granularity": "daily",
    "sample_size_needed": 1000
}}
"""
        
        try:
            plan = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a data planning expert.",
            )
            return plan
        except:
            # Fallback plan
            return {
                "data_types": ["analytics"],
                "metrics": ["user_engagement"],
                "timeframe": "last_30_days",
                "granularity": "daily",
            }
    
    # =====================
    # Demo Mode (Synthetic Data)
    # =====================
    
    async def _generate_demo_data(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate realistic synthetic data using LLM.
        
        Args:
            plan: Data collection plan
            
        Returns:
            Dict with generated data
        """
        data_types = plan.get("data_types", ["analytics"])
        metrics = plan.get("metrics", ["engagement"])
        
        prompt = f"""
Generate realistic demo data for product research.

CONTEXT:
Goal: {self.goal.description}
Data types needed: {', '.join(data_types)}
Metrics: {', '.join(metrics)}

Create believable synthetic data in JSON format:
{{
    "data_type": "analytics",
    "metrics": [
        {{
            "name": "activation_rate",
            "current_value": 0.28,
            "previous_value": 0.42,
            "change_percent": -33.3,
            "trend": "declining"
        }}
    ],
    "funnel_data": [
        {{"step": "signup", "users": 10000, "conversion": 1.0}},
        {{"step": "email_verify", "users": 8500, "conversion": 0.85}},
        {{"step": "oauth", "users": 2500, "conversion": 0.29}}
    ],
    "insights": [
        "60% drop at OAuth step",
        "Significantly worse than industry benchmark"
    ]
}}

Make it realistic and relevant to the goal. Include specific numbers.
"""
        
        try:
            data = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a data generation expert. Create realistic, believable data.",
                temperature=0.8,  # Higher creativity for varied data
            )
            
            # Add metadata
            data["generated_at"] = datetime.utcnow().isoformat()
            data["mode"] = "demo"
            
            return data
        except Exception as e:
            # Fallback data
            return {
                "data_type": "analytics",
                "metrics": [{
                    "name": "engagement",
                    "current_value": 0.65,
                    "trend": "stable",
                }],
                "insights": ["Data generation failed, using fallback"],
                "error": str(e),
            }
    
    # =====================
    # Real Mode (Actual Data)
    # =====================
    
    async def _collect_real_data(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect real data from APIs or uploads.
        
        Args:
            plan: Data collection plan
            
        Returns:
            Dict with collected data
        """
        # For Week 1 MVP: simplified
        # In production: connect to PostHog, GA4, etc.
        
        return {
            "data_type": "real_analytics",
            "metrics": [],
            "insights": ["Real data collection not yet implemented"],
            "mode": "real",
            "collected_at": datetime.utcnow().isoformat(),
        }
    
    # =====================
    # Analysis
    # =====================
    
    async def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze collected data and extract insights.
        
        Args:
            data: Collected data
            
        Returns:
            Dict with analysis results
        """
        prompt = f"""
Analyze this product data:

DATA:
{json.dumps(data, indent=2)}

GOAL: {self.goal.description}

Provide analysis in JSON:
{{
    "key_findings": [
        "Finding 1 with specific numbers",
        "Finding 2 with specific numbers"
    ],
    "patterns": [
        "Pattern 1",
        "Pattern 2"
    ],
    "anomalies": ["Anything unexpected"],
    "hypotheses": [
        {{
            "hypothesis": "Root cause statement",
            "confidence": 0.85,
            "evidence": ["Supporting fact 1", "Supporting fact 2"]
        }}
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}}

Focus on actionable insights relevant to the goal.
"""
        
        try:
            analysis = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a product analytics expert.",
            )
            return analysis
        except Exception as e:
            return {
                "key_findings": ["Analysis error occurred"],
                "error": str(e),
            }
    
    # =====================
    # Output Generation
    # =====================
    
    async def _generate_output(
        self,
        data: Dict[str, Any],
        insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate final agent output.
        
        Args:
            data: Collected data
            insights: Analysis insights
            
        Returns:
            Dict with complete agent output
        """
        return {
            "agent": self.agent_name,
            "completed_at": datetime.utcnow().isoformat(),
            "summary": self._create_summary(insights),
            "data_collected": data,
            "analysis": insights,
            "next_steps": self._suggest_next_steps(insights),
        }
    
    def _create_summary(self, insights: Dict[str, Any]) -> str:
        """Create text summary of findings"""
        findings = insights.get("key_findings", [])
        if findings:
            return " | ".join(findings[:3])
        return "Data collection complete"
    
    def _suggest_next_steps(self, insights: Dict[str, Any]) -> List[str]:
        """Suggest next steps based on analysis"""
        recommendations = insights.get("recommendations", [])
        if recommendations:
            return recommendations[:3]
        return ["Review findings", "Validate with stakeholders"]
