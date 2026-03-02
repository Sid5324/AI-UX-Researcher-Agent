"""
Memory System
============

Multi-layer memory with ChromaDB:
- Working memory: Current goal context (volatile)
- Episodic memory: Session history (SQLite)
- Semantic memory: Long-term insights (ChromaDB)
- Procedural memory: Learned skills (ChromaDB)
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except Exception as e:
    CHROMADB_AVAILABLE = False
    print(f"Warning: ChromaDB unavailable, running without semantic memory: {e}")

from src.core.config import get_settings
from src.database.models import MemoryEntry, Insight
from src.database.session import AsyncSession


settings = get_settings()


class MemoryManager:
    """
    Manages all memory layers for agentic AI.
    
    Provides:
    - Semantic search across past insights
    - Pattern detection across projects
    - Skill learning and retrieval
    """
    
    def __init__(self, session: Optional[AsyncSession] = None):
        # Optional session accepted for backwards compatibility with existing tests.
        self.session = session
        self.chromadb_client = None
        self.insights_collection = None
        self.skills_collection = None
        
        if CHROMADB_AVAILABLE:
            self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collections"""
        try:
            # Create data directory if needed
            chroma_path = Path(settings.chromadb_path)
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize client (persistent storage)
            self.chromadb_client = chromadb.Client(
                ChromaSettings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(chroma_path),
                )
            )
            
            # Get or create collections
            self.insights_collection = self.chromadb_client.get_or_create_collection(
                name="semantic_insights",
                metadata={"description": "Validated insights from all projects"},
            )
            
            self.skills_collection = self.chromadb_client.get_or_create_collection(
                name="procedural_skills",
                metadata={"description": "Learned skills and patterns"},
            )
            
            print(f"ChromaDB initialized: {settings.chromadb_path}")
            
        except Exception as e:
            print(f"Warning: ChromaDB initialization failed: {e}")
            self.chromadb_client = None
    
    # =====================
    # Semantic Memory (Insights)
    # =====================
    
    async def store_insight(
        self,
        session: AsyncSession,
        content: str,
        insight_type: str,
        confidence: float,
        evidence: Dict[str, Any],
        tags: List[str],
        effect_size: Optional[str] = None,
    ) -> str:
        """
        Store validated insight in semantic memory.
        
        Args:
            session: Database session
            content: Insight content
            insight_type: Type (user_behavior, pain_point, etc.)
            confidence: Confidence score (0-1)
            evidence: Supporting evidence
            tags: Tags for categorization
            effect_size: Measured impact (e.g., "+47% activation")
            
        Returns:
            Insight ID
        """
        # Create database record
        insight = Insight(
            insight_type=insight_type,
            content=content,
            confidence=confidence,
            evidence=evidence,
            validation_method=evidence.get("method", "unknown"),
            tags=tags,
            effect_size=effect_size,
            applicable_contexts=tags,  # Same as tags initially
        )
        
        session.add(insight)
        await session.commit()
        
        # Store in ChromaDB for semantic search
        if self.chromadb_client:
            try:
                self.insights_collection.add(
                    documents=[content],
                    metadatas=[{
                        "insight_id": insight.id,
                        "type": insight_type,
                        "confidence": confidence,
                        "tags": ",".join(tags),
                        "created_at": insight.created_at.isoformat(),
                    }],
                    ids=[insight.id],
                )
            except Exception as e:
                print(f"Warning: ChromaDB storage failed: {e}")
        
        return insight.id
    
    async def search_insights(
        self,
        query: str,
        top_k: int = 5,
        min_confidence: float = 0.7,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search semantic memory for relevant insights.
        
        Args:
            query: Search query (natural language)
            top_k: Number of results to return
            min_confidence: Minimum confidence threshold
            tags: Filter by tags
            
        Returns:
            List of relevant insights with metadata
        """
        if not self.chromadb_client:
            return []
        
        try:
            # Build filter
            where = {"confidence": {"$gte": min_confidence}}
            if tags:
                where["tags"] = {"$contains": tags[0]}  # Simplified
            
            # Search ChromaDB
            results = self.insights_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where if where else None,
            )
            
            # Format results
            insights = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    insights.append({
                        "content": doc,
                        "insight_id": metadata.get("insight_id"),
                        "type": metadata.get("type"),
                        "confidence": metadata.get("confidence"),
                        "tags": metadata.get("tags", "").split(","),
                        "distance": results["distances"][0][i] if "distances" in results else None,
                    })
            
            return insights
            
        except Exception as e:
            print(f"Warning: Insight search failed: {e}")
            return []
    
    # =====================
    # Procedural Memory (Skills)
    # =====================
    
    async def store_skill(
        self,
        skill_name: str,
        description: str,
        pattern: List[str],
        success_rate: float,
        contexts: List[str],
    ) -> str:
        """
        Store learned skill in procedural memory.
        
        Args:
            skill_name: Unique skill identifier
            description: What this skill does
            pattern: Steps in the skill
            success_rate: Success rate (0-1)
            contexts: Where this skill applies
            
        Returns:
            Skill ID
        """
        if not self.chromadb_client:
            return ""
        
        try:
            skill_id = hashlib.md5(skill_name.encode()).hexdigest()[:16]
            
            # Combine description and pattern for embedding
            skill_doc = f"{description}\n\nSteps:\n" + "\n".join(
                f"{i+1}. {step}" for i, step in enumerate(pattern)
            )
            
            self.skills_collection.add(
                documents=[skill_doc],
                metadatas=[{
                    "skill_name": skill_name,
                    "success_rate": success_rate,
                    "contexts": ",".join(contexts),
                    "steps_count": len(pattern),
                    "created_at": datetime.utcnow().isoformat(),
                }],
                ids=[skill_id],
            )
            
            return skill_id
            
        except Exception as e:
            print(f"Warning: Skill storage failed: {e}")
            return ""
    
    async def search_skills(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant learned skills.
        
        Args:
            query: What we're trying to do
            context: Current context (e.g., "B2B_SaaS")
            top_k: Number of skills to return
            
        Returns:
            List of relevant skills
        """
        if not self.chromadb_client:
            return []
        
        try:
            where = {}
            if context:
                where["contexts"] = {"$contains": context}
            
            results = self.skills_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where if where else None,
            )
            
            skills = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i]
                    skills.append({
                        "description": doc,
                        "skill_name": metadata.get("skill_name"),
                        "success_rate": metadata.get("success_rate"),
                        "contexts": metadata.get("contexts", "").split(","),
                        "steps_count": metadata.get("steps_count"),
                    })
            
            return skills
            
        except Exception as e:
            print(f"Warning: Skill search failed: {e}")
            return []
    
    # =====================
    # Pattern Detection
    # =====================
    
    async def detect_patterns(
        self,
        session: AsyncSession,
        min_occurrences: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Detect patterns across multiple projects.
        
        Args:
            session: Database session
            min_occurrences: Minimum times pattern must appear
            
        Returns:
            List of detected patterns
        """
        # This would analyze all insights and find common themes
        # For MVP, return empty (implement in Phase 2)
        return []
    
    # =====================
    # Utility Methods
    # =====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            "chromadb_available": CHROMADB_AVAILABLE,
            "chromadb_path": settings.chromadb_path,
        }
        
        if self.chromadb_client:
            try:
                stats["insights_count"] = self.insights_collection.count()
                stats["skills_count"] = self.skills_collection.count()
            except:
                stats["insights_count"] = 0
                stats["skills_count"] = 0
        else:
            stats["insights_count"] = 0
            stats["skills_count"] = 0
        
        return stats
    
    def reset_memory(self) -> None:
        """
        Clear all memory (⚠️ destructive operation).
        
        Use with caution - this deletes all learned insights and skills.
        """
        if self.chromadb_client:
            try:
                self.chromadb_client.delete_collection("semantic_insights")
                self.chromadb_client.delete_collection("procedural_skills")
                self._initialize_chromadb()
                print("Memory reset complete")
            except Exception as e:
                print(f"Warning: Memory reset failed: {e}")


# =====================
# Global Instance
# =====================

_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create memory manager singleton"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


# Export for convenience
memory_manager = get_memory_manager()


# =====================
# Convenience Functions
# =====================

async def store_insight(
    session: AsyncSession,
    content: str,
    **kwargs
) -> str:
    """Shortcut for storing insights"""
    return await memory_manager.store_insight(session, content, **kwargs)


async def search_memory(query: str, **kwargs) -> List[Dict[str, Any]]:
    """Shortcut for searching semantic memory"""
    return await memory_manager.search_insights(query, **kwargs)


async def find_similar_skills(query: str, **kwargs) -> List[Dict[str, Any]]:
    """Shortcut for finding relevant skills"""
    return await memory_manager.search_skills(query, **kwargs)
