"""
Vector Memory Service for persistent, semantic memory across all agents.
Uses MongoDB Atlas Vector Search + OpenAI Embeddings.
"""
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np

logger = logging.getLogger(__name__)

class VectorMemoryService:
    """
    Manages long-term memory using vector embeddings and semantic search.
    Enables agents to remember context across sessions and users.
    """
    
    def __init__(self, db, embedding_model="text-embedding-ada-002"):
        self.db = db
        self.embedding_model = embedding_model
        self.embedding_dimension = 1536  # OpenAI embedding dimension
        
        # Collections
        self.global_memory = db.global_memory  # Shared across all users
        self.user_memory = db.user_memory  # User-specific memories
        self.agent_memory = db.agent_memory  # Agent-specific memories
        self.tenants = db.tenants  # User tenant management
        
        logger.info("Vector Memory Service initialized")
    
    async def create_tenant(self, user_id: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new tenant (user) with their own memory space.
        Called automatically on first visit.
        """
        try:
            # Check if tenant already exists
            existing = await self.tenants.find_one({"user_id": user_id})
            if existing:
                logger.info(f"Tenant {user_id} already exists")
                return {
                    "tenant_id": existing.get("tenant_id"),
                    "user_id": user_id,
                    "is_new": False
                }
            
            tenant_id = str(uuid.uuid4())
            tenant_doc = {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {},
                "total_memories": 0,
                "last_active": datetime.now(timezone.utc).isoformat()
            }
            
            await self.tenants.insert_one(tenant_doc)
            logger.info(f"Created new tenant: {tenant_id} for user: {user_id}")
            
            return {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "is_new": True
            }
            
        except Exception as e:
            logger.error(f"Error creating tenant: {str(e)}")
            raise
    
    async def get_or_create_tenant(self, user_id: str) -> Dict[str, Any]:
        """Get existing tenant or create new one."""
        tenant = await self.tenants.find_one({"user_id": user_id})
        if tenant:
            # Update last active
            await self.tenants.update_one(
                {"user_id": user_id},
                {"$set": {"last_active": datetime.now(timezone.utc).isoformat()}}
            )
            return {
                "tenant_id": tenant.get("tenant_id"),
                "user_id": user_id,
                "is_new": False
            }
        else:
            return await self.create_tenant(user_id)
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate OpenAI embedding for text using OpenAI SDK directly.
        """
        try:
            from openai import AsyncOpenAI
            import os
            
            # Use OpenAI API key for embeddings
            api_key = os.environ.get('OPENAI_API_KEY')
            
            if not api_key:
                logger.error("OPENAI_API_KEY not found in environment")
                return None
            
            # Use standard OpenAI endpoint
            client = AsyncOpenAI(api_key=api_key)
            
            # Generate embedding (use ada-002 which all keys have access to)
            response = await client.embeddings.create(
                input=text[:8000],  # Limit text length
                model="text-embedding-ada-002"
            )
            
            if response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                logger.info(f"✅ Generated embedding: {len(embedding)} dimensions")
                return embedding
            else:
                logger.error("No embedding returned")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {str(e)}")
            return None
    
    async def store_memory(
        self,
        user_id: str,
        content: str,
        memory_type: str = "conversation",
        agent_name: str = None,
        metadata: Dict[str, Any] = None,
        scope: str = "user"  # "user", "agent", or "global"
    ) -> str:
        """
        Store a memory with its embedding for semantic retrieval.
        
        Args:
            user_id: User identifier
            content: Text content to store
            memory_type: Type of memory (conversation, fact, result, etc.)
            agent_name: Which agent created this memory
            metadata: Additional metadata
            scope: Memory scope (user, agent, global)
        
        Returns:
            memory_id
        """
        try:
            # Get or create tenant
            tenant = await self.get_or_create_tenant(user_id)
            
            # Generate embedding
            embedding = await self.generate_embedding(content)
            if not embedding:
                logger.error("Failed to generate embedding")
                return None
            
            memory_id = str(uuid.uuid4())
            memory_doc = {
                "memory_id": memory_id,
                "tenant_id": tenant["tenant_id"],
                "user_id": user_id,
                "content": content,
                "memory_type": memory_type,
                "agent_name": agent_name,
                "metadata": metadata or {},
                "embedding": embedding,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "scope": scope
            }
            
            # Store in appropriate collection
            if scope == "global":
                await self.global_memory.insert_one(memory_doc)
            elif scope == "agent":
                await self.agent_memory.insert_one(memory_doc)
            else:
                await self.user_memory.insert_one(memory_doc)
            
            # Update tenant memory count
            await self.tenants.update_one(
                {"user_id": user_id},
                {"$inc": {"total_memories": 1}}
            )
            
            logger.info(f"Stored {scope} memory: {memory_id[:8]}... for user: {user_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return None
    
    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        scope: str = "user",
        memory_type: str = None,
        agent_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for relevant memories using vector similarity.
        
        Args:
            user_id: User identifier
            query: Search query
            limit: Number of results
            scope: Memory scope to search
            memory_type: Filter by memory type
            agent_name: Filter by agent
        
        Returns:
            List of relevant memories with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Get tenant
            tenant = await self.tenants.find_one({"user_id": user_id})
            if not tenant:
                logger.warning(f"No tenant found for user: {user_id}")
                return []
            
            # Build filter
            filter_query = {"user_id": user_id}
            if memory_type:
                filter_query["memory_type"] = memory_type
            if agent_name:
                filter_query["agent_name"] = agent_name
            
            # Select collection
            if scope == "global":
                collection = self.global_memory
                filter_query = {}  # Global is shared
            elif scope == "agent":
                collection = self.agent_memory
            else:
                collection = self.user_memory
            
            # MongoDB Vector Search aggregation pipeline
            # Note: This requires Atlas Vector Search index to be created
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": f"{scope}_memory_vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": limit * 10,
                        "limit": limit,
                        "filter": filter_query
                    }
                },
                {
                    "$project": {
                        "memory_id": 1,
                        "content": 1,
                        "memory_type": 1,
                        "agent_name": 1,
                        "metadata": 1,
                        "created_at": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            # Execute vector search
            try:
                results = await collection.aggregate(pipeline).to_list(limit)
                logger.info(f"Vector search found {len(results)} memories for query: {query[:50]}...")
                return results
            except Exception as e:
                # Fallback to simple text search if vector search not set up
                logger.warning(f"Vector search failed, using text fallback: {str(e)}")
                return await self._fallback_text_search(collection, filter_query, query, limit)
                
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    async def _fallback_text_search(
        self,
        collection,
        filter_query: Dict,
        query: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fallback text search when vector search is not available - searches ALL user memories."""
        try:
            # Remove regex filter, just get ALL user's memories
            user_id = filter_query.get("user_id")
            if user_id:
                # Get ALL memories for this user, sorted by most recent
                results = await collection.find(
                    {"user_id": user_id}
                ).sort("created_at", -1).limit(limit * 3).to_list(limit * 3)
                
                # Remove _id and embedding for cleaner response
                clean_results = []
                for result in results:
                    result.pop("_id", None)
                    result.pop("embedding", None)
                    result["score"] = 0.7  # Give decent score for recency
                    clean_results.append(result)
                
                logger.info(f"Fallback search found {len(clean_results)} memories for user: {user_id}")
                return clean_results[:limit]  # Return top limit
            else:
                return []
                
        except Exception as e:
            logger.error(f"Fallback search error: {str(e)}")
            return []
    
    async def get_context_for_agent(
        self,
        user_id: str,
        agent_name: str,
        query: str,
        max_memories: int = 5
    ) -> str:
        """
        Get relevant context for an agent to use in its reasoning.
        Searches user, agent, and global memories.
        """
        try:
            context_parts = []
            
            # Search user memories
            user_memories = await self.search_memories(
                user_id=user_id,
                query=query,
                limit=max_memories,
                scope="user"
            )
            
            if user_memories:
                context_parts.append("**User Context:**")
                for mem in user_memories:
                    context_parts.append(f"- {mem.get('content')}")
            
            # Search agent-specific memories
            agent_memories = await self.search_memories(
                user_id=user_id,
                query=query,
                limit=max_memories // 2,
                scope="agent",
                agent_name=agent_name
            )
            
            if agent_memories:
                context_parts.append(f"\n**{agent_name} Memories:**")
                for mem in agent_memories:
                    context_parts.append(f"- {mem.get('content')}")
            
            # Search global memories (best practices, guidelines)
            global_memories = await self.search_memories(
                user_id=user_id,
                query=query,
                limit=2,
                scope="global"
            )
            
            if global_memories:
                context_parts.append("\n**Global Knowledge:**")
                for mem in global_memories:
                    context_parts.append(f"- {mem.get('content')}")
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error getting agent context: {str(e)}")
            return ""
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Build user profile from stored memories.
        Returns key facts about the user.
        """
        try:
            tenant = await self.tenants.find_one({"user_id": user_id})
            if not tenant:
                return None
            
            # Get recent memories
            recent_memories = await self.user_memory.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(20).to_list(20)
            
            # Extract key information
            profile = {
                "user_id": user_id,
                "tenant_id": tenant.get("tenant_id"),
                "created_at": tenant.get("created_at"),
                "total_memories": tenant.get("total_memories", 0),
                "last_active": tenant.get("last_active"),
                "recent_topics": [],
                "websites": [],
                "business_info": []
            }
            
            # Parse memories for key info
            for mem in recent_memories:
                content = mem.get("content", "").lower()
                
                # Look for websites
                if "website" in content or ".com" in content or "http" in content:
                    profile["websites"].append(mem.get("content"))
                
                # Look for business info
                if any(word in content for word in ["company", "business", "product", "service"]):
                    profile["business_info"].append(mem.get("content"))
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
