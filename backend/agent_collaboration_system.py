"""
Agent Collaboration System - Enables agents to communicate and coordinate.
Provides real-time event bus for agent-to-agent communication.
"""
import logging
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger(__name__)

class AgentCollaborationSystem:
    """
    Manages inter-agent communication and task delegation.
    Agents publish events and subscribe to relevant tasks.
    """
    
    def __init__(self, db):
        self.db = db
        self.events_collection = db.agent_events
        self.tasks_collection = db.agent_tasks
        
        # In-memory event subscribers (for real-time updates)
        self.subscribers = {}
        
        logger.info("Agent Collaboration System initialized")
    
    async def publish_event(
        self,
        agent_name: str,
        event_type: str,
        data: Dict[str, Any],
        user_id: str = None,
        conversation_id: str = None
    ) -> str:
        """
        Publish an event that other agents can see.
        
        Event types:
        - task_started
        - task_completed
        - task_failed
        - agent_delegating
        - result_available
        - needs_input
        """
        try:
            event_id = str(uuid.uuid4())
            event_doc = {
                "event_id": event_id,
                "agent_name": agent_name,
                "event_type": event_type,
                "data": data,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "published"
            }
            
            # Store in database
            await self.events_collection.insert_one(event_doc)
            
            logger.info(f"[{agent_name}] Published event: {event_type}")
            
            # Notify subscribers (for real-time UI updates)
            await self._notify_subscribers(event_doc)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
            return None
    
    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task_description: str,
        task_data: Dict[str, Any],
        priority: str = "normal",
        user_id: str = None,
        conversation_id: str = None
    ) -> str:
        """
        Delegate a task from one agent to another.
        """
        try:
            task_id = str(uuid.uuid4())
            task_doc = {
                "task_id": task_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "task_description": task_description,
                "task_data": task_data,
                "priority": priority,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "result": None
            }
            
            # Store task
            await self.tasks_collection.insert_one(task_doc)
            
            # Publish delegation event
            await self.publish_event(
                agent_name=from_agent,
                event_type="agent_delegating",
                data={
                    "task_id": task_id,
                    "to_agent": to_agent,
                    "description": task_description
                },
                user_id=user_id,
                conversation_id=conversation_id
            )
            
            logger.info(f"[{from_agent}] Delegated task to [{to_agent}]: {task_description[:50]}...")
            
            return task_id
            
        except Exception as e:
            logger.error(f"Error delegating task: {str(e)}")
            return None
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        agent_name: str
    ) -> bool:
        """Mark task as completed and publish result."""
        try:
            # Update task status
            await self.tasks_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "result": result
                    }
                }
            )
            
            # Publish completion event
            task = await self.tasks_collection.find_one({"task_id": task_id})
            if task:
                await self.publish_event(
                    agent_name=agent_name,
                    event_type="task_completed",
                    data={
                        "task_id": task_id,
                        "from_agent": task.get("from_agent"),
                        "result_summary": str(result)[:200]
                    },
                    user_id=task.get("user_id"),
                    conversation_id=task.get("conversation_id")
                )
            
            logger.info(f"[{agent_name}] Completed task: {task_id[:8]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error completing task: {str(e)}")
            return False
    
    async def get_conversation_events(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all agent events for a conversation (for UI display).
        """
        try:
            events = await self.events_collection.find(
                {"conversation_id": conversation_id},
                {"_id": 0}
            ).sort("timestamp", 1).limit(limit).to_list(limit)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting conversation events: {str(e)}")
            return []
    
    async def get_agent_activity(
        self,
        agent_name: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a specific agent."""
        try:
            events = await self.events_collection.find(
                {"agent_name": agent_name},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit).to_list(limit)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting agent activity: {str(e)}")
            return []
    
    async def _notify_subscribers(self, event: Dict[str, Any]):
        """Notify real-time subscribers of new events (for WebSocket updates)."""
        # This will be used for WebSocket connections in the future
        conversation_id = event.get("conversation_id")
        if conversation_id and conversation_id in self.subscribers:
            for callback in self.subscribers[conversation_id]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error notifying subscriber: {str(e)}")
    
    def subscribe(self, conversation_id: str, callback):
        """Subscribe to events for a conversation (for WebSocket)."""
        if conversation_id not in self.subscribers:
            self.subscribers[conversation_id] = []
        self.subscribers[conversation_id].append(callback)
    
    def unsubscribe(self, conversation_id: str, callback):
        """Unsubscribe from conversation events."""
        if conversation_id in self.subscribers:
            self.subscribers[conversation_id].remove(callback)
