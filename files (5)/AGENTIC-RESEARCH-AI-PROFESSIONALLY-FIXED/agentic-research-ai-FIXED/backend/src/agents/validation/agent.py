"""
Validation Agent
"""
from src.agents.base import BaseAgent
from src.core.ai_manager import get_ai_manager
import json
from scipy import stats
import numpy as np
from typing import Dict, Any

class ValidationAgent(BaseAgent):
    """
    Validation Agent - Designs and analyzes A/B tests.
    
    Capabilities:
    - Design experiments
    - Calculate sample sizes
    - Run statistical tests
    - Generate recommendations
    """
    
    agent_name = "validation_agent"
    agent_description = "Validates hypotheses through experiments"
    required_tools = ["ab_test_analyzer"]
    
    async def execute(self) -> Dict[str, Any]:
        """Main validation workflow."""
        
        await self.update_progress("Analyzing hypothesis", 10)
        
        # Get context
        context = self.working_memory.get("shared_context", {})
        prd = context.get("product_strategy", {})
        
        # Step 1: Design experiment
        await self.update_progress("Designing A/B test", 25)
        test_design = await self._design_experiment(prd)
        
        # Step 2: Calculate sample size
        await self.update_progress("Calculating sample size", 40)
        sample_size = await self._calculate_sample_size(test_design)
        
        # Step 3: Run analysis (simulated or real data)
        await self.update_progress("Running statistical analysis", 70)
        results = await self._analyze_results(test_design)
        
        # Step 4: Generate recommendation
        await self.update_progress("Generating recommendation", 90)
        recommendation = await self._generate_recommendation(results)
        
        await self.update_progress("Complete", 100)
        
        return {
            "agent": self.agent_name,
            "test_design": test_design,
            "sample_size": sample_size,
            "results": results,
            "recommendation": recommendation,
        }
    
    async def _design_experiment(self, prd: Dict) -> Dict[str, Any]:
        """Design A/B test based on PRD."""
        
        ai_manager = get_ai_manager()
        
        prompt = f"""
Design an A/B test for this product requirement.

PRD: {json.dumps(prd, indent=2)[:1000]}

Create test design in JSON:
{{
    "hypothesis": "Specific hypothesis statement",
    "metric": "Primary metric to measure",
    "variants": [
        {{"name": "control", "description": "Current experience"}},
        {{"name": "treatment", "description": "New experience"}}
    ],
    "duration_days": 14,
    "success_criteria": "What determines success"
}}
"""
        
        try:
            design = await ai_manager.generate_json(prompt=prompt)
            return design
        except:
            return {
                "hypothesis": "Testing hypothesis",
                "metric": "conversion_rate",
                "variants": [
                    {"name": "control", "description": "Current"},
                    {"name": "treatment", "description": "New"}
                ],
                "duration_days": 14,
            }
    
    async def _calculate_sample_size(self, test_design: Dict) -> Dict[str, Any]:
        """Calculate required sample size for statistical power."""
        
        # Parameters
        baseline_rate = 0.10  # Assume 10% baseline conversion
        mde = 0.20  # Minimum detectable effect (20% relative lift)
        alpha = 0.05  # Significance level
        power = 0.80  # Statistical power
        
        # Calculate using standard formula
        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)
        
        z_alpha = stats.norm.ppf(1 - alpha/2)
        z_beta = stats.norm.ppf(power)
        
        p_pooled = (p1 + p2) / 2
        
        n = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta)**2) / (p1 - p2)**2
        
        return {
            "sample_size_per_variant": int(np.ceil(n)),
            "total_sample_size": int(np.ceil(n * 2)),
            "baseline_rate": baseline_rate,
            "mde": mde,
            "alpha": alpha,
            "power": power,
            "estimated_duration_days": int(np.ceil(n * 2 / 1000)),  # Assume 1000 users/day
        }
    
    async def _analyze_results(self, test_design: Dict) -> Dict[str, Any]:
        """Analyze A/B test results (simulated for demo)."""
        
        # Simulate results
        control_users = 5000
        treatment_users = 5000
        
        control_conversions = 500  # 10% conversion
        treatment_conversions = 600  # 12% conversion
        
        control_rate = control_conversions / control_users
        treatment_rate = treatment_conversions / treatment_users
        
        # Statistical test
        z_score, p_value = stats.proportions_ztest(
            [control_conversions, treatment_conversions],
            [control_users, treatment_users]
        )
        
        # Effect size
        lift = (treatment_rate - control_rate) / control_rate
        
        # Confidence interval
        se = np.sqrt(
            (control_rate * (1 - control_rate) / control_users) +
            (treatment_rate * (1 - treatment_rate) / treatment_users)
        )
        ci_lower = lift - 1.96 * se / control_rate
        ci_upper = lift + 1.96 * se / control_rate
        
        return {
            "control": {
                "users": control_users,
                "conversions": control_conversions,
                "conversion_rate": round(control_rate, 4),
            },
            "treatment": {
                "users": treatment_users,
                "conversions": treatment_conversions,
                "conversion_rate": round(treatment_rate, 4),
            },
            "lift": f"+{round(lift * 100, 1)}%",
            "p_value": round(p_value, 4),
            "significant": p_value < 0.05,
            "confidence_level": "99%" if p_value < 0.01 else "95%" if p_value < 0.05 else "not significant",
            "confidence_interval": f"[{round(ci_lower * 100, 1)}%, {round(ci_upper * 100, 1)}%]",
        }
    
    async def _generate_recommendation(self, results: Dict) -> Dict[str, Any]:
        """Generate recommendation based on results."""
        
        if results["significant"]:
            lift = float(results["lift"].replace("+", "").replace("%", ""))
            
            if lift > 10:
                decision = "Ship immediately"
                confidence = "high"
                rationale = f"Significant lift of {results['lift']} with {results['confidence_level']} confidence."
            elif lift > 5:
                decision = "Ship with monitoring"
                confidence = "medium"
                rationale = f"Moderate lift of {results['lift']}, monitor closely for regressions."
            else:
                decision = "Run longer"
                confidence = "low"
                rationale = "Lift is significant but small, run test longer for more data."
        else:
            decision = "Do not ship"
            confidence = "low"
            rationale = f"No significant difference (p={results['p_value']}), treatment did not improve metric."
        
        return {
            "decision": decision,
            "confidence": confidence,
            "rationale": rationale,
            "next_steps": [
                "Review test implementation for bugs" if decision == "Do not ship" else "Prepare rollout plan",
                "Monitor guardrail metrics",
                "Plan follow-up experiments",
            ],
        }


# =================================================================
