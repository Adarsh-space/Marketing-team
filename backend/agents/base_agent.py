from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all AI agents in the marketing automation platform.
    Provides common LLM interaction functionality.
    """
    
    def __init__(self, agent_name: str, system_prompt: str, model: str = "gpt-4o"):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.model = model
        self.api_key = os.environ.get('EMERGENT_LLM_KEY')
        
    async def execute(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task with given payload.
        Returns structured JSON response.
        """
        try:
            # Create unique session for this task
            session_id = f"{self.agent_name}_{task_payload.get('task_id', 'unknown')}"
            
            # Initialize LLM chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_prompt
            ).with_model("openai", self.model)
            
            # Prepare user message
            user_prompt = self._prepare_prompt(task_payload)
            user_message = UserMessage(text=user_prompt)
            
            # Get LLM response
            logger.info(f"{self.agent_name} processing task...")
            response = await chat.send_message(user_message)
            
            # Parse and structure response
            result = self._parse_response(response, task_payload)
            
            return {
                "status": "success",
                "agent": self.agent_name,
                "result": result,
                "task_id": task_payload.get('task_id')
            }
            
        except Exception as e:
            logger.error(f"{self.agent_name} error: {str(e)}")
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e),
                "task_id": task_payload.get('task_id')
            }
    
    def _prepare_prompt(self, task_payload: Dict[str, Any]) -> str:
        """
        Prepare the prompt for the LLM based on task payload.
        Includes vector memory context by default.
        Override in subclasses for agent-specific logic.
        """
        # Extract vector context if available
        vector_context = task_payload.get('vector_context', '')

        # Build prompt with context
        prompt_parts = []

        # Add vector memory context (if available)
        if vector_context:
            prompt_parts.append("📝 RELEVANT CONTEXT FROM MEMORY:")
            prompt_parts.append(vector_context)
            prompt_parts.append("\n⚠️ Use this context to provide better responses!\n")

        # Add main task payload
        prompt_parts.append("TASK DETAILS:")
        prompt_parts.append(json.dumps(task_payload, indent=2))

        return "\n\n".join(prompt_parts)
    
    def _parse_response(self, response: str, task_payload: Dict[str, Any]) -> Any:
        """
        Parse LLM response into structured data.
        Override in subclasses for agent-specific parsing.
        """
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
        return response
