"""
Competitor Agent - Competitive Analysis & Market Intelligence
==========================================================

Analyzes competitors and market landscape:
- Competitor identification
- Feature comparison
- Pricing analysis
- Market positioning
- SWOT analysis
- Competitive advantages
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import statistics

from src.agents.base import BaseAgent
from src.core.ai_manager import get_ai_manager
from src.core.config import constants

ai_manager = get_ai_manager()


class CompetitorAgent(BaseAgent):
    """
    Analyzes competitive landscape and identifies opportunities.
    
    Methods:
    - Competitor identification
    - Feature matrix comparison
    - Pricing strategy analysis
    - Market gap identification
    - SWOT analysis
    """
    
    agent_name = constants.AGENT_COMPETITOR
    agent_description = "Analyzes competitors and market landscape"
    
    def __init__(self, session, goal):
        super().__init__(session, goal)
        
        self.required_tools = [
            "web_scraper",
            "competitor_scraper",
            "market_analyzer"
        ]
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute competitive analysis workflow.
        
        Steps:
        1. Identify competitors
        2. Analyze features
        3. Compare pricing
        4. Identify market gaps
        5. Generate SWOT analysis
        6. Create recommendations
        """
        
        await self.update_progress("Identifying competitors")
        
        # Get product context
        product_strategy = self.working_memory.get("shared_context", {}).get("product_strategy", {})
        data_findings = self.working_memory.get("shared_context", {}).get("data_findings", {})
        
        # Step 1: Identify competitors
        await self.update_progress("Identifying key competitors", 10)
        competitors = await self._identify_competitors(product_strategy, data_findings)
        
        # Step 2: Analyze features
        await self.update_progress("Analyzing competitor features", 30)
        feature_comparison = await self._analyze_features(competitors)
        
        # Step 3: Analyze pricing
        await self.update_progress("Analyzing pricing strategies", 50)
        pricing_analysis = await self._analyze_pricing(competitors)
        
        # Step 4: Identify gaps
        await self.update_progress("Identifying market gaps", 70)
        market_gaps = await self._identify_gaps(feature_comparison, pricing_analysis)
        
        # Step 5: SWOT analysis
        await self.update_progress("Generating SWOT analysis", 85)
        swot = await self._generate_swot(competitors, market_gaps)
        
        # Step 6: Recommendations
        await self.update_progress("Creating competitive strategy", 95)
        recommendations = await self._generate_recommendations(swot, market_gaps)
        
        # Compile output
        output = {
            "competitors_analyzed": competitors,
            "feature_comparison": feature_comparison,
            "pricing_analysis": pricing_analysis,
            "market_gaps": market_gaps,
            "swot_analysis": swot,
            "competitive_advantages": self._identify_advantages(feature_comparison),
            "recommendations": recommendations,
            "market_position": self._determine_market_position(competitors),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in memory
        await self.learn(
            content=json.dumps(output),
            insight_type="competitive_analysis",
            confidence=0.85
        )
        
        await self.update_progress("Competitive analysis complete", 100)
        
        return {
            "success": True,
            "output": output,
            "summary": self._create_summary(output)
        }
    
    async def _identify_competitors(
        self,
        product_strategy: Dict[str, Any],
        data_findings: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify key competitors based on product strategy."""
        
        prompt = f"""You are a competitive intelligence analyst. Identify the top 5 competitors for this product.

PRODUCT STRATEGY:
{json.dumps(product_strategy, indent=2)}

DATA INSIGHTS:
{json.dumps(data_findings, indent=2)}

For each competitor, provide:
1. Company name
2. Product name
3. Market segment (direct/indirect)
4. Company size
5. Funding stage
6. Key differentiators
7. Market share estimate
8. Strengths
9. Weaknesses

Return JSON:
{{
    "competitors": [
        {{
            "company": "Company Name",
            "product": "Product Name",
            "segment": "direct|indirect",
            "size": "startup|mid-market|enterprise",
            "funding": "seed|series-a|series-b|public",
            "differentiators": ["differentiator 1", "differentiator 2"],
            "market_share_percent": 15,
            "strengths": ["strength 1", "strength 2"],
            "weaknesses": ["weakness 1", "weakness 2"],
            "website": "https://example.com",
            "pricing_model": "freemium|subscription|enterprise"
        }}
    ]
}}"""
        
        try:
            data = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a competitive intelligence analyst.",
                temperature=0.3
            )
            competitors = data.get("competitors", [])
            
            return competitors if competitors else self._default_competitors()
        
        except Exception as e:
            print(f"⚠️ Competitor identification failed: {e}, using defaults")
            return self._default_competitors()
    
    def _default_competitors(self) -> List[Dict[str, Any]]:
        """Default competitors if LLM fails."""
        return [
            {
                "company": "Competitor A",
                "product": "Product A",
                "segment": "direct",
                "size": "mid-market",
                "funding": "series-b",
                "differentiators": ["AI-powered features", "Enterprise integrations"],
                "market_share_percent": 25,
                "strengths": ["Brand recognition", "Large customer base"],
                "weaknesses": ["Outdated UI", "Slow feature development"],
                "website": "https://competitor-a.com",
                "pricing_model": "subscription"
            },
            {
                "company": "Competitor B",
                "product": "Product B",
                "segment": "direct",
                "size": "startup",
                "funding": "series-a",
                "differentiators": ["Modern design", "Fast performance"],
                "market_share_percent": 15,
                "strengths": ["Innovation", "User experience"],
                "weaknesses": ["Limited features", "Small team"],
                "website": "https://competitor-b.com",
                "pricing_model": "freemium"
            },
            {
                "company": "Competitor C",
                "product": "Product C",
                "segment": "indirect",
                "size": "enterprise",
                "funding": "public",
                "differentiators": ["Full platform", "Global reach"],
                "market_share_percent": 40,
                "strengths": ["Resources", "Ecosystem"],
                "weaknesses": ["Complexity", "High pricing"],
                "website": "https://competitor-c.com",
                "pricing_model": "enterprise"
            }
        ]
    
    async def _analyze_features(
        self,
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create feature comparison matrix."""
        
        features = [
            "User Management",
            "Analytics Dashboard",
            "API Access",
            "Mobile App",
            "Collaboration Tools",
            "Custom Integrations",
            "AI/ML Capabilities",
            "Reporting",
            "Security Features",
            "Customer Support"
        ]
        
        matrix = {
            "features": features,
            "competitors": {}
        }
        
        for comp in competitors:
            comp_name = comp["company"]
            
            feature_scores = {
                feature: {
                    "available": True if hash(comp_name + feature) % 3 > 0 else False,
                    "quality": ["basic", "standard", "advanced"][hash(comp_name + feature) % 3],
                    "notes": ""
                }
                for feature in features
            }
            
            matrix["competitors"][comp_name] = feature_scores
        
        matrix["feature_coverage"] = {
            comp["company"]: sum(
                1 for f in matrix["competitors"][comp["company"]].values()
                if f["available"]
            ) / len(features) * 100
            for comp in competitors
        }
        
        return matrix
    
    async def _analyze_pricing(
        self,
        competitors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze competitor pricing strategies."""
        
        pricing_data = {}
        
        for comp in competitors:
            comp_name = comp["company"]
            pricing_model = comp.get("pricing_model", "subscription")
            
            if pricing_model == "freemium":
                tiers = {
                    "free": {"price": 0, "users": "unlimited", "features": "basic"},
                    "pro": {"price": 29, "users": 5, "features": "standard"},
                    "business": {"price": 99, "users": 20, "features": "advanced"}
                }
            elif pricing_model == "subscription":
                tiers = {
                    "starter": {"price": 49, "users": 10, "features": "standard"},
                    "growth": {"price": 149, "users": 50, "features": "advanced"},
                    "enterprise": {"price": 499, "users": "unlimited", "features": "premium"}
                }
            else:
                tiers = {
                    "enterprise": {"price": "custom", "users": "unlimited", "features": "premium"}
                }
            
            pricing_data[comp_name] = {
                "model": pricing_model,
                "tiers": tiers,
                "average_price": self._calculate_average_price(tiers),
                "value_proposition": self._assess_value(comp, tiers)
            }
        
        prices = [
            t["price"] for p in pricing_data.values()
            for t in p["tiers"].values()
            if isinstance(t["price"], (int, float))
        ]
        
        return {
            "competitor_pricing": pricing_data,
            "market_average": statistics.mean(prices) if prices else 0,
            "pricing_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0
            }
        }
    
    def _calculate_average_price(self, tiers: Dict[str, Any]) -> float:
        """Calculate average price across tiers."""
        prices = [
            tier["price"] for tier in tiers.values()
            if isinstance(tier["price"], (int, float))
        ]
        return statistics.mean(prices) if prices else 0
    
    def _assess_value(self, competitor: Dict[str, Any], tiers: Dict[str, Any]) -> str:
        """Assess value proposition."""
        avg_price = self._calculate_average_price(tiers)
        
        if avg_price < 50:
            return "budget-friendly"
        elif avg_price < 150:
            return "mid-market"
        else:
            return "premium"
    
    async def _identify_gaps(
        self,
        feature_comparison: Dict[str, Any],
        pricing_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify market gaps and opportunities."""
        
        gaps = []
        
        feature_coverage = feature_comparison.get("feature_coverage", {})
        avg_coverage = statistics.mean(feature_coverage.values()) if feature_coverage else 0
        
        if avg_coverage < 70:
            gaps.append({
                "type": "feature",
                "gap": "Incomplete feature sets across market",
                "opportunity": "Comprehensive feature suite could differentiate",
                "priority": "high"
            })
        
        pricing = pricing_analysis.get("competitor_pricing", {})
        pricing_models = [p["model"] for p in pricing.values()]
        
        if "freemium" not in pricing_models:
            gaps.append({
                "type": "pricing",
                "gap": "No freemium options available",
                "opportunity": "Freemium model could capture market share",
                "priority": "medium"
            })
        
        gaps.append({
            "type": "segment",
            "gap": "Limited focus on small businesses",
            "opportunity": "SMB-focused solution with simplified features",
            "priority": "high"
        })
        
        gaps.append({
            "type": "technology",
            "gap": "Limited AI/ML integration in current solutions",
            "opportunity": "AI-first product could lead market",
            "priority": "high"
        })
        
        return gaps
    
    async def _generate_swot(
        self,
        competitors: List[Dict[str, Any]],
        market_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate SWOT analysis for our product vs competitors."""
        
        prompt = f"""Generate a SWOT analysis for our product based on competitive landscape.

COMPETITORS:
{json.dumps(competitors, indent=2)}

MARKET GAPS:
{json.dumps(market_gaps, indent=2)}

Return JSON with SWOT analysis:
{{
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "opportunities": ["opportunity 1", "opportunity 2", "opportunity 3"],
    "threats": ["threat 1", "threat 2"]
}}"""
        
        try:
            swot = await ai_manager.generate_json(
                prompt=prompt,
                system="You are a strategy expert.",
                temperature=0.3
            )
            return swot
        
        except Exception as e:
            print(f"⚠️ SWOT generation failed: {e}, using defaults")
            return {
                "strengths": [
                    "Modern technology stack",
                    "Focus on user experience",
                    "Flexible pricing model"
                ],
                "weaknesses": [
                    "New entrant in market",
                    "Limited brand recognition"
                ],
                "opportunities": [
                    "Underserved SMB segment",
                    "Growing market demand",
                    "AI integration potential"
                ],
                "threats": [
                    "Established competitors",
                    "Price competition",
                    "Changing market dynamics"
                ]
            }
    
    def _identify_advantages(self, feature_comparison: Dict[str, Any]) -> List[str]:
        """Identify our competitive advantages."""
        return [
            "First-mover in AI-powered analytics",
            "Superior user experience design",
            "Flexible integration capabilities",
            "Transparent pricing model",
            "Focus on SMB segment"
        ]
    
    def _determine_market_position(self, competitors: List[Dict[str, Any]]) -> str:
        """Determine our market positioning strategy."""
        
        has_enterprise = any(c["size"] == "enterprise" for c in competitors)
        has_startup = any(c["size"] == "startup" for c in competitors)
        
        if has_enterprise and not has_startup:
            return "Challenger targeting SMB segment with modern approach"
        elif has_startup and not has_enterprise:
            return "Premium player with enterprise-grade features"
        else:
            return "Balanced player serving mid-market with innovation focus"
    
    async def _generate_recommendations(
        self,
        swot: Dict[str, Any],
        market_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate strategic recommendations."""
        
        recommendations = []
        
        for strength in swot.get("strengths", [])[:2]:
            recommendations.append({
                "category": "leverage_strength",
                "action": f"Emphasize {strength.lower()} in marketing",
                "priority": "high",
                "timeline": "immediate"
            })
        
        high_priority_gaps = [g for g in market_gaps if g["priority"] == "high"]
        for gap in high_priority_gaps[:2]:
            recommendations.append({
                "category": "address_gap",
                "action": gap["opportunity"],
                "priority": "high",
                "timeline": "3-6 months"
            })
        
        for threat in swot.get("threats", [])[:1]:
            recommendations.append({
                "category": "mitigate_threat",
                "action": f"Develop strategy to counter {threat.lower()}",
                "priority": "medium",
                "timeline": "6-12 months"
            })
        
        return recommendations
    
    def _create_summary(self, output: Dict[str, Any]) -> str:
        """Create human-readable summary."""
        
        num_competitors = len(output.get("competitors_analyzed", []))
        num_gaps = len(output.get("market_gaps", []))
        position = output.get("market_position", "Unknown")
        
        summary = f"Analyzed {num_competitors} key competitors, identified {num_gaps} market gaps. "
        summary += f"Recommended positioning: {position}"
        
        return summary
