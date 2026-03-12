"""
Goal Parser
===========

Converts natural language goals into structured missions:
- Extracts intent, constraints, success criteria
- Generates task breakdown
- Estimates resources (time, cost)
- Determines autonomy level
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.core.config import get_settings
from src.core.ai_manager import get_ai_manager


settings = get_settings()
ai_manager = get_ai_manager()


class ParsedGoal:
    """Structured representation of a parsed goal"""
    
    def __init__(self, data: Dict[str, Any]):
        self.raw_description = data.get("raw_description", "")
        self.intent = data.get("intent", "")
        self.goal_type = data.get("goal_type", "general")
        self.success_criteria = data.get("success_criteria", [])
        self.constraints = data.get("constraints", {})
        self.sub_goals = data.get("sub_goals", [])
        self.estimated_duration_days = data.get("estimated_duration_days", 7)
        self.estimated_cost_usd = data.get("estimated_cost_usd", 1000)
        self.autonomy_level = data.get("autonomy_level", "supervised")
        self.required_agents = data.get("required_agents", ["data_agent"])
        self.checkpoints = data.get("checkpoints", [])
        self.risks = data.get("risks", [])
        self.metadata = data.get("metadata", {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "raw_description": self.raw_description,
            "intent": self.intent,
            "goal_type": self.goal_type,
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "sub_goals": self.sub_goals,
            "estimated_duration_days": self.estimated_duration_days,
            "estimated_cost_usd": self.estimated_cost_usd,
            "autonomy_level": self.autonomy_level,
            "required_agents": self.required_agents,
            "checkpoints": self.checkpoints,
            "risks": self.risks,
            "metadata": self.metadata,
        }


class GoalParser:
    """
    Parses natural language research goals into structured missions.
    
    Uses LLM to understand intent and generate execution plan.
    """
    
    def __init__(self):
        self.ai_manager = ai_manager
    
    async def parse(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ParsedGoal:
        """
        Parse natural language goal into structured mission.
        
        Args:
            description: User's goal description
            context: Additional context (user preferences, past goals, etc.)
            
        Returns:
            ParsedGoal with structured mission data
        """
        # Build parsing prompt
        prompt = self._build_parsing_prompt(description, context)
        
        # Generate structured mission
        try:
            mission_data = await self.ai_manager.generate_json(
                prompt=prompt,
                system="You are an expert product research planner.",
                temperature=0.3,  # Lower temperature for consistency
            )
            
            # Add raw description
            mission_data["raw_description"] = description
            
            # Validate and normalize (pass description for agent detection)
            mission_data = self._validate_mission(mission_data, description)
            
            return ParsedGoal(mission_data)
            
        except Exception as e:
            # Fallback: create basic mission
            return self._create_fallback_mission(description)
    
    def _build_parsing_prompt(
        self,
        description: str,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build prompt for goal parsing"""
        
        context_str = ""
        if context:
            context_str = f"\nAdditional context:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""
Analyze this product research goal and create a structured mission plan:

USER'S GOAL:
"{description}"
{context_str}

Parse this into a comprehensive mission structure with JSON format:

{{
    "intent": "Clear statement of what user wants to achieve",
    "goal_type": "one of: root_cause_analysis, feature_validation, user_research, competitive_analysis, usability_testing, general",
    
    "success_criteria": [
        "Specific measurable outcome 1",
        "Specific measurable outcome 2"
    ],
    
    "constraints": {{
        "budget_usd": 2000 (extract from description or estimate),
        "timeline_days": 7 (extract from description or estimate),
        "urgency": "low|medium|high",
        "quality_threshold": "what level of rigor is needed"
    }},
    
    "sub_goals": [
        {{
            "title": "Sub-goal 1",
            "description": "What needs to be done",
            "estimated_duration": 2 (days)
        }}
    ],
    
    "required_agents": ["data_agent", "prd_agent"],
    
    "autonomy_level": "supervised|partial|full (based on goal complexity and risk)",
    
    "checkpoints": [
        {{
            "title": "Checkpoint 1",
            "trigger": "When to ask for approval",
            "decision_needed": "What user must decide"
        }}
    ],
    
    "risks": [
        "Potential risk 1",
        "Potential risk 2"
    ],
    
    "estimated_duration_days": 7,
    "estimated_cost_usd": 1500,
    
    "metadata": {{
        "complexity": "low|medium|high",
        "domain": "B2B_SaaS|consumer_app|etc",
        "primary_method": "quantitative|qualitative|mixed"
    }}
}}

IMPORTANT:
- Extract budget and timeline from description if mentioned
- Estimate conservatively if not mentioned
- Identify which agents are needed for this type of research
- Plan checkpoints at critical decision points (not every step)
- Be realistic about what can be achieved
"""
        
        return prompt
    
    def _validate_mission(self, mission_data: Dict[str, Any], description: str = "") -> Dict[str, Any]:
        """
        Validate and normalize mission data.
        
        FIXED: No longer overwrites required_agents with hardcoded default.
        Now uses intelligent keyword-based agent detection as fallback.
        """
        
        # CRITICAL FIX: Save LLM-provided agents before applying defaults
        llm_agents = mission_data.get("required_agents", [])
        
        # Ensure required fields exist (without required_agents in defaults)
        defaults = {
            "intent": "Conduct research as requested",
            "goal_type": "general",
            "success_criteria": ["Complete analysis"],
            "constraints": {
                "budget_usd": 1000,
                "timeline_days": 7,
                "urgency": "medium",
            },
            "sub_goals": [],
            # FIXED: removed "required_agents" from defaults
            "autonomy_level": "supervised",
            "checkpoints": [],
            "risks": [],
            "estimated_duration_days": 7,
            "estimated_cost_usd": 1000,
            "metadata": {},
        }
        
        # Merge with defaults (excluding required_agents)
        for key, default_value in defaults.items():
            if key not in mission_data or not mission_data[key]:
                mission_data[key] = default_value
        
        # CRITICAL FIX: Smart agent determination
        if not llm_agents or llm_agents == ["data_agent"]:
            # LLM didn't provide agents or provided only default
            # Use keyword-based detection
            mission_data["required_agents"] = self._determine_agents_from_keywords(description)
        else:
            # Use LLM-provided agents
            mission_data["required_agents"] = llm_agents
        
        # Normalize values
        if mission_data["estimated_duration_days"] < 1:
            mission_data["estimated_duration_days"] = 1
        
        if mission_data["estimated_cost_usd"] < 0:
            mission_data["estimated_cost_usd"] = 0
        
        # Ensure autonomy level is valid
        valid_autonomy = ["supervised", "partial", "full"]
        if mission_data["autonomy_level"] not in valid_autonomy:
            mission_data["autonomy_level"] = "supervised"
        
        return mission_data
    
    def _determine_agents_from_keywords(self, description: str) -> List[str]:
        """
        Determine required agents based on keywords in goal description.
        
        This is a fallback when LLM doesn't provide proper agent selection.
        """
        agents = ["data_agent"]  # Always include data agent as base
        desc_lower = description.lower()
        
        # Check for PRD keywords
        prd_keywords = ["prd", "requirements", "product strategy", "roadmap", 
                       "product requirements", "feature spec", "specification"]
        if any(keyword in desc_lower for keyword in prd_keywords):
            agents.append("prd_agent")
        
        # Check for UI/UX keywords
        design_keywords = ["ui", "ux", "design", "mockup", "wireframe", 
                          "interface", "user experience", "user interface", 
                          "visual design", "interaction design", "prototype"]
        if any(keyword in desc_lower for keyword in design_keywords):
            agents.append("ui_ux_agent")
        
        # Check for validation keywords
        validation_keywords = ["validate", "test", "experiment", "a/b", 
                              "statistical", "hypothesis", "verify", "significance"]
        if any(keyword in desc_lower for keyword in validation_keywords):
            agents.append("validation_agent")
        
        # Check for competitor keywords
        competitor_keywords = ["competitor", "competitive", "market analysis", 
                              "competitive landscape", "benchmark", "industry analysis"]
        if any(keyword in desc_lower for keyword in competitor_keywords):
            agents.append("competitor_agent")
        
        # Check for interview keywords
        interview_keywords = ["interview", "user research", "qualitative", 
                             "user interview", "talk to users", "customer research"]
        if any(keyword in desc_lower for keyword in interview_keywords):
            agents.append("interview_agent")
        
        # Check for feedback keywords
        feedback_keywords = ["feedback", "reviews", "user comments", 
                            "customer feedback", "user feedback", "satisfaction"]
        if any(keyword in desc_lower for keyword in feedback_keywords):
            agents.append("feedback_agent")
        
        print(f"✅ Goal Parser: Determined agents from keywords: {agents}")
        return agents
    
    def _create_fallback_mission(self, description: str) -> ParsedGoal:
        """
        Create basic mission if parsing fails.
        
        FIXED: Now uses keyword-based agent detection instead of hardcoded single agent.
        """
        
        # Determine agents from keywords
        agents = self._determine_agents_from_keywords(description)
        
        return ParsedGoal({
            "raw_description": description,
            "intent": description,
            "goal_type": "general",
            "success_criteria": ["Complete the requested research"],
            "constraints": {
                "budget_usd": 1000,
                "timeline_days": 7,
                "urgency": "medium",
            },
            "sub_goals": [
                {
                    "title": "Data collection",
                    "description": "Gather relevant data",
                    "estimated_duration": 2,
                },
                {
                    "title": "Analysis",
                    "description": "Analyze findings",
                    "estimated_duration": 3,
                },
                {
                    "title": "Recommendations",
                    "description": "Generate recommendations",
                    "estimated_duration": 2,
                },
            ],
            "required_agents": agents,  # FIXED: Uses keyword-detected agents
            "autonomy_level": "supervised",
            "checkpoints": [
                {
                    "title": "Initial findings",
                    "trigger": "After data collection",
                    "decision_needed": "Approve analysis direction",
                }
            ],
            "risks": ["Data availability", "Time constraints"],
            "estimated_duration_days": 7,
            "estimated_cost_usd": 1000,
            "metadata": {"complexity": "medium"},
        })
    
    async def extract_constraints(self, description: str) -> Dict[str, Any]:
        """
        Quick extraction of constraints from description.
        
        Useful for pre-validation before full parsing.
        """
        prompt = f"""
Extract constraints from this goal:
"{description}"

Return JSON with:
{{
    "budget_mentioned": true/false,
    "budget_amount": 2000 or null,
    "timeline_mentioned": true/false,
    "timeline_days": 7 or null,
    "urgency_keywords": ["urgent", "ASAP", etc.]
}}
"""
        
        try:
            return await self.ai_manager.generate_json(prompt=prompt)
        except:
            return {
                "budget_mentioned": False,
                "budget_amount": None,
                "timeline_mentioned": False,
                "timeline_days": None,
                "urgency_keywords": [],
            }


# =====================
# Convenience Functions
# =====================

async def parse_goal(
    description: str,
    context: Optional[Dict[str, Any]] = None,
) -> ParsedGoal:
    """
    Parse natural language goal (convenience function).
    
    Usage:
        parsed = await parse_goal("Fix our activation rate")
        print(f"Intent: {parsed.intent}")
        print(f"Agents needed: {parsed.required_agents}")
    """
    parser = GoalParser()
    return await parser.parse(description, context)


async def quick_estimate(description: str) -> Dict[str, Any]:
    """
    Get quick time/cost estimate without full parsing.
    
    Returns:
        Dict with estimated_days, estimated_cost, complexity
    """
    parser = GoalParser()
    
    prompt = f"""
Quickly estimate resources for this goal:
"{description}"

Return JSON:
{{
    "estimated_days": 7,
    "estimated_cost_usd": 1500,
    "complexity": "low|medium|high",
    "feasibility": "easy|moderate|challenging|very_challenging"
}}
"""
    
    try:
        return await parser.ai_manager.generate_json(prompt=prompt)
    except:
        return {
            "estimated_days": 7,
            "estimated_cost_usd": 1000,
            "complexity": "medium",
            "feasibility": "moderate",
        }
