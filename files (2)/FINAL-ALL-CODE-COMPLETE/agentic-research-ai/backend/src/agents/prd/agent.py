"""
PRD Agent - Complete Implementation
===================================

Senior Product Manager agent that:
- Synthesizes research into product strategy
- Writes comprehensive PRD documents
- Creates user stories and acceptance criteria
- Defines success metrics
- Plans rollout strategy
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from backend.src.agents.base import BaseAgent
from backend.src.core.ai_manager import get_ai_manager
from backend.src.core.config import get_settings


settings = get_settings()
ai_manager = get_ai_manager()


class PRDAgent(BaseAgent):
    """
    Product Requirements Document Agent.
    
    Role: Senior Product Manager
    Personality: Strategic, evidence-driven, user-focused
    Voice: Professional, persuasive, cites data
    """
    
    agent_name = "prd_agent"
    agent_description = "Synthesizes research into product requirements"
    required_tools = []
    
    async def execute(self) -> Dict[str, Any]:
        """
        Main PRD generation workflow.
        
        Steps:
        1. Understand research findings
        2. Identify user needs & pain points
        3. Define solution approach
        4. Write comprehensive PRD
        5. Plan rollout strategy
        """
        await self.update_progress("Understanding research findings", 10)
        
        # Get context from previous agents
        context = self.working_memory.get("shared_context", {})
        data_findings = context.get("data_findings", {})
        
        # Step 1: Synthesize research
        await self.update_progress("Synthesizing research insights", 20)
        synthesis = await self._synthesize_research(data_findings)
        
        # Step 2: Define user personas
        await self.update_progress("Creating user personas", 35)
        personas = await self._create_personas(synthesis)
        
        # Step 3: Write user stories
        await self.update_progress("Writing user stories", 50)
        user_stories = await self._write_user_stories(personas, synthesis)
        
        # Step 4: Define requirements
        await self.update_progress("Defining requirements", 65)
        requirements = await self._define_requirements(user_stories)
        
        # Step 5: Plan metrics
        await self.update_progress("Defining success metrics", 80)
        metrics = await self._define_metrics(requirements)
        
        # Step 6: Create rollout plan
        await self.update_progress("Planning rollout", 90)
        rollout = await self._plan_rollout(requirements)
        
        # Step 7: Generate final PRD
        await self.update_progress("Generating PRD document", 95)
        prd = await self._generate_prd_document(
            synthesis, personas, user_stories, requirements, metrics, rollout
        )
        
        await self.update_progress("Complete", 100)
        
        return {
            "agent": self.agent_name,
            "prd_document": prd,
            "personas": personas,
            "user_stories": user_stories,
            "requirements": requirements,
            "success_metrics": metrics,
            "rollout_plan": rollout,
            "completed_at": datetime.utcnow().isoformat(),
        }
    
    # =====================
    # Research Synthesis
    # =====================
    
    async def _synthesize_research(self, data_findings: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize data agent findings into actionable insights"""
        
        prompt = f"""
You are a Senior Product Manager synthesizing research findings.

RESEARCH FINDINGS:
{json.dumps(data_findings, indent=2)}

GOAL: {self.goal.description}

Synthesize this into product strategy in JSON:
{{
    "problem_statement": "Clear definition of the problem",
    "root_causes": [
        {{"cause": "Root cause 1", "confidence": 0.90, "evidence": "Supporting data"}}
    ],
    "user_pain_points": [
        {{"pain": "Pain point 1", "severity": "high|medium|low", "frequency": "how often"}}
    ],
    "opportunity_size": {{
        "users_affected": 10000,
        "revenue_impact_annual": 240000,
        "time_to_roi": "3 months"
    }},
    "strategic_direction": "High-level solution approach",
    "key_insights": ["Insight 1", "Insight 2"]
}}

Be specific with numbers and evidence.
"""
        
        try:
            return await ai_manager.generate_json(
                prompt=prompt,
                system="You are a strategic product thinker who transforms data into decisions.",
            )
        except:
            return {
                "problem_statement": self.goal.description,
                "root_causes": [],
                "user_pain_points": [],
                "strategic_direction": "Analyze and improve user experience",
            }
    
    # =====================
    # Persona Creation
    # =====================
    
    async def _create_personas(self, synthesis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed user personas"""
        
        prompt = f"""
Based on this research synthesis, create 2-3 detailed user personas.

SYNTHESIS:
{json.dumps(synthesis, indent=2)}

Create personas in JSON format:
[
    {{
        "name": "Mobile Maria",
        "role": "Product Manager",
        "demographics": {{"age": 29, "location": "San Francisco"}},
        "goals": ["Goal 1", "Goal 2"],
        "pain_points": ["Pain 1", "Pain 2"],
        "behaviors": ["Uses mobile primarily", "Values speed"],
        "quote": "I need research to happen fast without me being the bottleneck",
        "tech_savvy": "high|medium|low",
        "decision_driver": "What drives their decisions"
    }}
]

Make them realistic and specific.
"""
        
        try:
            return await ai_manager.generate_json(prompt=prompt)
        except:
            return [{
                "name": "Primary User",
                "role": "Product Manager",
                "goals": ["Complete research quickly"],
                "pain_points": ["Time-consuming research"],
            }]
    
    # =====================
    # User Stories
    # =====================
    
    async def _write_user_stories(
        self,
        personas: List[Dict[str, Any]],
        synthesis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Write comprehensive user stories"""
        
        prompt = f"""
Write user stories for this product based on personas and research.

PERSONAS:
{json.dumps(personas, indent=2)}

PROBLEM:
{synthesis.get("problem_statement", "")}

Create 5-8 user stories in JSON:
[
    {{
        "id": "US-001",
        "persona": "Mobile Maria",
        "story": "As a [persona], I want to [action] so that [benefit]",
        "acceptance_criteria": [
            "Given [context], when [action], then [outcome]",
            "And [additional criterion]"
        ],
        "priority": "must-have|should-have|nice-to-have",
        "estimated_effort": "small|medium|large",
        "dependencies": ["US-002"],
        "success_metrics": ["Metric that indicates success"]
    }}
]

Write from user perspective, be specific about outcomes.
"""
        
        try:
            return await ai_manager.generate_json(prompt=prompt)
        except:
            return [{
                "id": "US-001",
                "story": f"As a user, I want to {self.goal.description}",
                "priority": "must-have",
            }]
    
    # =====================
    # Requirements
    # =====================
    
    async def _define_requirements(
        self,
        user_stories: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Define functional and non-functional requirements"""
        
        prompt = f"""
Based on these user stories, define detailed requirements.

USER STORIES:
{json.dumps(user_stories, indent=2)}

Create requirements in JSON:
{{
    "functional": [
        {{
            "id": "FR-001",
            "title": "Guest Checkout",
            "description": "Users can checkout without creating account",
            "user_stories": ["US-001", "US-002"],
            "must_have": true,
            "acceptance_criteria": ["Criterion 1", "Criterion 2"]
        }}
    ],
    "non_functional": [
        {{
            "id": "NFR-001",
            "category": "performance|security|usability|accessibility",
            "requirement": "Page load time < 2 seconds",
            "rationale": "Why this matters",
            "measurement": "How to verify"
        }}
    ],
    "technical_constraints": [
        "Constraint 1",
        "Constraint 2"
    ]
}}

Be specific and measurable.
"""
        
        try:
            return await ai_manager.generate_json(prompt=prompt)
        except:
            return {
                "functional": [],
                "non_functional": [],
                "technical_constraints": [],
            }
    
    # =====================
    # Success Metrics
    # =====================
    
    async def _define_metrics(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Define success metrics and KPIs"""
        
        prompt = f"""
Define success metrics for this product.

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

GOAL: {self.goal.description}

Create metrics in JSON:
{{
    "north_star": {{
        "metric": "Primary metric name",
        "definition": "How it's calculated",
        "target": "Specific target value",
        "current_baseline": "Current value if known"
    }},
    "primary_metrics": [
        {{
            "metric": "Activation rate",
            "target": "42% (from 28%)",
            "timeframe": "30 days post-launch",
            "measurement_method": "How to track"
        }}
    ],
    "secondary_metrics": [
        {{"metric": "Time to checkout", "target": "< 2 minutes"}}
    ],
    "guardrail_metrics": [
        {{"metric": "Error rate", "threshold": "< 0.5%", "action_if_exceeded": "Rollback"}}
    ]
}}

Make targets specific and measurable.
"""
        
        try:
            return await ai_manager.generate_json(prompt=prompt)
        except:
            return {
                "north_star": {"metric": "User satisfaction", "target": "Improve"},
                "primary_metrics": [],
            }
    
    # =====================
    # Rollout Planning
    # =====================
    
    async def _plan_rollout(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Plan phased rollout strategy"""
        
        prompt = f"""
Create a phased rollout plan for this product.

REQUIREMENTS:
{json.dumps(requirements, indent=2)}

Create rollout plan in JSON:
{{
    "phases": [
        {{
            "phase": 1,
            "name": "Alpha Test",
            "duration_days": 7,
            "audience": "Internal team (20 people)",
            "goal": "Verify core functionality",
            "success_criteria": ["No critical bugs", "Core flows work"],
            "rollback_triggers": ["Critical bug", "Performance degradation"]
        }}
    ],
    "launch_sequence": [
        {{"step": "Enable feature flag", "owner": "Engineering", "dependencies": []}}
    ],
    "monitoring_plan": {{
        "metrics_to_watch": ["Error rate", "Load time", "Conversion"],
        "alert_thresholds": {{"error_rate": "> 1%"}},
        "dashboards": ["Real-time metrics", "User feedback"]
    }},
    "rollback_plan": {{
        "triggers": ["Trigger 1", "Trigger 2"],
        "process": "Step-by-step rollback",
        "estimated_time": "< 30 minutes"
    }}
}}

Include 3-4 phases (alpha, beta, gradual rollout, full launch).
"""
        
        try:
            return await ai_manager.generate_json(prompt=prompt)
        except:
            return {
                "phases": [{
                    "phase": 1,
                    "name": "Beta Launch",
                    "duration_days": 14,
                    "audience": "10% of users",
                }],
            }
    
    # =====================
    # PRD Document Generation
    # =====================
    
    async def _generate_prd_document(
        self,
        synthesis: Dict[str, Any],
        personas: List[Dict[str, Any]],
        user_stories: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        metrics: Dict[str, Any],
        rollout: Dict[str, Any],
    ) -> str:
        """Generate final PRD document in markdown"""
        
        prd = f"""# Product Requirements Document

## Executive Summary

**Product:** {self.goal.description}
**Date:** {datetime.utcnow().strftime("%Y-%m-%d")}
**Status:** Draft
**Owner:** Product Team

### Problem Statement
{synthesis.get("problem_statement", "")}

### Strategic Direction
{synthesis.get("strategic_direction", "")}

### Opportunity Size
- Users Affected: {synthesis.get("opportunity_size", {}).get("users_affected", "TBD")}
- Revenue Impact: ${synthesis.get("opportunity_size", {}).get("revenue_impact_annual", 0):,}/year
- Time to ROI: {synthesis.get("opportunity_size", {}).get("time_to_roi", "TBD")}

---

## User Personas

{self._format_personas(personas)}

---

## User Stories

{self._format_user_stories(user_stories)}

---

## Requirements

### Functional Requirements

{self._format_requirements(requirements.get("functional", []))}

### Non-Functional Requirements

{self._format_requirements(requirements.get("non_functional", []))}

---

## Success Metrics

### North Star Metric
- **{metrics.get("north_star", {}).get("metric", "TBD")}**
- Target: {metrics.get("north_star", {}).get("target", "TBD")}

### Primary Metrics
{self._format_metrics(metrics.get("primary_metrics", []))}

### Guardrail Metrics
{self._format_metrics(metrics.get("guardrail_metrics", []))}

---

## Rollout Plan

{self._format_rollout(rollout)}

---

## Next Steps

1. Review and approve PRD
2. Design phase (UI/UX Agent)
3. Engineering estimation
4. Alpha launch

---

**Generated by:** PRD Agent
**Date:** {datetime.utcnow().isoformat()}
"""
        
        return prd
    
    # =====================
    # Formatting Helpers
    # =====================
    
    def _format_personas(self, personas: List[Dict[str, Any]]) -> str:
        """Format personas for markdown"""
        formatted = []
        for persona in personas:
            formatted.append(f"""
### {persona.get("name", "User")}
**Role:** {persona.get("role", "N/A")}

**Goals:**
{self._format_list(persona.get("goals", []))}

**Pain Points:**
{self._format_list(persona.get("pain_points", []))}

> "{persona.get("quote", "")}"
""")
        return "\n".join(formatted)
    
    def _format_user_stories(self, stories: List[Dict[str, Any]]) -> str:
        """Format user stories for markdown"""
        formatted = []
        for story in stories:
            formatted.append(f"""
#### {story.get("id", "US-XXX")}: {story.get("story", "")}
**Priority:** {story.get("priority", "TBD")}
**Effort:** {story.get("estimated_effort", "TBD")}

**Acceptance Criteria:**
{self._format_list(story.get("acceptance_criteria", []))}
""")
        return "\n".join(formatted)
    
    def _format_requirements(self, reqs: List[Dict[str, Any]]) -> str:
        """Format requirements for markdown"""
        formatted = []
        for req in reqs:
            formatted.append(f"""
#### {req.get("id", "REQ-XXX")}: {req.get("title", "")}
{req.get("description", "")}
""")
        return "\n".join(formatted)
    
    def _format_metrics(self, metrics_list: List[Dict[str, Any]]) -> str:
        """Format metrics for markdown"""
        formatted = []
        for metric in metrics_list:
            formatted.append(f"- **{metric.get('metric', 'N/A')}**: {metric.get('target', 'TBD')}")
        return "\n".join(formatted)
    
    def _format_rollout(self, rollout: Dict[str, Any]) -> str:
        """Format rollout plan for markdown"""
        formatted = []
        for phase in rollout.get("phases", []):
            formatted.append(f"""
### Phase {phase.get("phase", "X")}: {phase.get("name", "TBD")}
- Duration: {phase.get("duration_days", "TBD")} days
- Audience: {phase.get("audience", "TBD")}
- Goal: {phase.get("goal", "TBD")}
""")
        return "\n".join(formatted)
    
    def _format_list(self, items: List[str]) -> str:
        """Format list for markdown"""
        return "\n".join(f"- {item}" for item in items)
