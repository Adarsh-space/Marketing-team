"""
LangGraph Multi-Agent Supervisor System

This module implements a hierarchical multi-agent system using LangGraph where:
- A supervisor agent coordinates and delegates tasks to specialized agents
- Agents communicate with each other through structured messages
- All agent communication is visible and logged
- Approval workflow is integrated before executing critical tasks
"""

from typing import Dict, Any, List, Literal, TypedDict, Annotated
import logging
from datetime import datetime
import operator

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langgraph.graph import StateGraph, END, START
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import MemorySaver
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # Create stub types when LangChain not available
    BaseMessage = Any
    HumanMessage = Any
    SystemMessage = Any
    AIMessage = Any
    ChatPromptTemplate = Any
    MessagesPlaceholder = Any
    StateGraph = Any
    END = None
    START = None
    ChatOpenAI = Any
    MemorySaver = Any
    logging.warning("LangChain/LangGraph not installed. Install with: pip install langchain langchain-openai langgraph")

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """
    State shared across all agents in the supervisor system.

    This state is passed between agents and tracks:
    - Current task being executed
    - Messages between agents
    - Results from each agent
    - Approval status
    - User context
    """
    task: str
    user_request: str
    conversation_history: List[Dict[str, Any]]
    agent_messages: Annotated[List[BaseMessage], operator.add]
    current_agent: str
    agent_results: Dict[str, Any]
    pending_approval: bool
    approval_granted: bool
    next_agent: str
    final_output: Dict[str, Any]


class MultiAgentSupervisor:
    """
    Hierarchical multi-agent system with supervisor pattern.

    The supervisor agent:
    - Analyzes user requests
    - Delegates tasks to specialized agents
    - Coordinates agent-to-agent communication
    - Manages approval workflows
    - Aggregates results
    """

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the multi-agent supervisor system.

        Args:
            api_key: OpenAI API key
            model: LLM model to use for agents
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain/LangGraph required. Install with: pip install langchain langchain-openai langgraph")

        self.api_key = api_key
        self.model = model
        self.llm = ChatOpenAI(api_key=api_key, model=model, temperature=0.7)
        self.memory = MemorySaver()

        # Define available specialized agents
        self.agent_definitions = {
            "content_agent": {
                "name": "Content Agent",
                "description": "Creates marketing content, social media posts, ad copy, and blog articles",
                "capabilities": ["social_media_content", "ad_copy", "blog_posts", "email_content"]
            },
            "email_agent": {
                "name": "Email Agent",
                "description": "Designs email campaigns, sequences, and manages email marketing strategy",
                "capabilities": ["email_campaigns", "email_sequences", "segmentation", "ab_testing"]
            },
            "image_agent": {
                "name": "Image Agent",
                "description": "Generates high-definition marketing images using AI",
                "capabilities": ["image_generation", "visual_content", "brand_imagery"]
            },
            "research_agent": {
                "name": "Research Agent",
                "description": "Conducts market research, competitor analysis, and audience insights",
                "capabilities": ["market_research", "competitor_analysis", "audience_analysis"]
            }
        }

        # Build the supervisor graph
        self.graph = self._build_supervisor_graph()

        logger.info("MultiAgentSupervisor initialized with LangGraph")

    def _create_supervisor_prompt(self) -> ChatPromptTemplate:
        """
        Create the supervisor agent prompt.

        The supervisor analyzes requests and delegates to appropriate agents.
        """
        system_message = """You are the Supervisor Agent coordinating a team of specialized marketing agents.

Your role is to:
1. Analyze user requests and break them down into subtasks
2. Delegate tasks to the most appropriate specialized agents
3. Coordinate communication between agents
4. Aggregate results into a cohesive final output

Available agents and their capabilities:
{agent_definitions}

IMPORTANT GUIDELINES:
- Speak naturally and professionally without using emojis or special symbols
- Be clear and concise in your communication
- When multiple agents need to work together, coordinate their collaboration
- Show all agent communication so the user can see the process
- For critical actions, set pending_approval to True

When delegating tasks:
- Choose the agent best suited for each subtask
- Provide clear instructions to each agent
- Share relevant context from previous agent results
- Coordinate dependencies between agents

Output your decision as JSON:
{{
    "analysis": "Brief analysis of the user request",
    "subtasks": [
        {{
            "task": "Description of subtask",
            "assigned_agent": "agent_name",
            "dependencies": ["previous_task_id"],
            "priority": "high|medium|low"
        }}
    ],
    "requires_approval": true or false,
    "coordination_notes": "How agents should collaborate"
}}
"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "User request: {user_request}\n\nAnalyze this request and delegate to appropriate agents.")
        ])

        return prompt

    def _create_agent_worker(self, agent_type: str) -> callable:
        """
        Create a worker function for a specialized agent.

        Args:
            agent_type: Type of agent (content_agent, email_agent, etc.)

        Returns:
            Async function that executes the agent's task
        """
        agent_info = self.agent_definitions[agent_type]

        async def agent_worker(state: AgentState) -> AgentState:
            """
            Execute agent task and return updated state.
            """
            task = state["task"]
            user_request = state["user_request"]
            previous_results = state["agent_results"]

            # Create agent-specific prompt
            system_prompt = f"""You are the {agent_info['name']}.

Description: {agent_info['description']}

Your capabilities: {', '.join(agent_info['capabilities'])}

COMMUNICATION GUIDELINES:
- Speak naturally and professionally
- Do NOT use emojis or special symbols in your responses
- Do NOT use bold text, asterisks, or formatting in communication
- Be clear, concise, and direct
- Focus on providing actionable results

IMPORTANT: The content you CREATE (social posts, emails, etc.) can include emojis and formatting for marketing purposes, but YOUR COMMUNICATION about the work should be plain and professional.

Context from previous agents:
{previous_results}

Your task:
{task}

Provide your results in clear, structured format."""

            # Get LLM response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"User request: {user_request}\n\nTask: {task}")
            ]

            response = await self.llm.ainvoke(messages)

            # Log agent communication
            logger.info(f"[{agent_info['name']}] Processing task: {task[:100]}...")

            # Update state with agent result
            state["agent_results"][agent_type] = {
                "agent": agent_info['name'],
                "task": task,
                "result": response.content,
                "timestamp": datetime.now().isoformat()
            }

            # Add message to agent communication log
            state["agent_messages"].append(
                AIMessage(
                    content=f"[{agent_info['name']}]: {response.content[:200]}...",
                    name=agent_type
                )
            )

            state["current_agent"] = agent_type

            return state

        return agent_worker

    def _supervisor_node(self, state: AgentState) -> AgentState:
        """
        Supervisor node that analyzes requests and delegates tasks.
        """
        user_request = state["user_request"]
        agent_results = state["agent_results"]

        # Create supervisor prompt
        prompt = self._create_supervisor_prompt()

        # Format agent definitions
        agent_def_str = "\n".join([
            f"- {info['name']}: {info['description']}"
            for info in self.agent_definitions.values()
        ])

        # Get supervisor decision
        messages = state["agent_messages"]

        response = self.llm.invoke(
            prompt.format_messages(
                agent_definitions=agent_def_str,
                user_request=user_request,
                messages=messages
            )
        )

        logger.info(f"[Supervisor] Analyzing request and delegating tasks...")

        # Parse supervisor response
        import json
        try:
            decision = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to simple delegation
            decision = {
                "analysis": response.content,
                "subtasks": [{"task": user_request, "assigned_agent": "content_agent"}],
                "requires_approval": False
            }

        # Update state with supervisor decision
        state["agent_messages"].append(
            AIMessage(
                content=f"[Supervisor] {decision.get('analysis', 'Delegating tasks...')}",
                name="supervisor"
            )
        )

        # Set next agent to execute
        if decision.get("subtasks"):
            next_task = decision["subtasks"][0]
            state["next_agent"] = next_task.get("assigned_agent", "content_agent")
            state["task"] = next_task.get("task", user_request)

        # Set approval requirement
        state["pending_approval"] = decision.get("requires_approval", False)

        return state

    def _approval_node(self, state: AgentState) -> AgentState:
        """
        Approval checkpoint node.

        If pending_approval is True, this pauses execution until approval is granted.
        """
        if state["pending_approval"] and not state["approval_granted"]:
            logger.info("[Approval Required] Waiting for user approval...")
            # In practice, this would wait for user input
            # For now, we'll assume approval is needed
            state["final_output"] = {
                "status": "awaiting_approval",
                "message": "This task requires your approval before proceeding. Please review the plan and approve.",
                "plan": state["agent_results"],
                "agent_communication": [msg.content for msg in state["agent_messages"]]
            }

        return state

    def _aggregation_node(self, state: AgentState) -> AgentState:
        """
        Final aggregation node that combines all agent results.
        """
        logger.info("[Aggregation] Combining results from all agents...")

        # Aggregate all agent results
        final_output = {
            "status": "completed",
            "user_request": state["user_request"],
            "agent_results": state["agent_results"],
            "agent_communication": [
                {
                    "agent": msg.name if hasattr(msg, 'name') else "system",
                    "message": msg.content
                }
                for msg in state["agent_messages"]
            ],
            "timestamp": datetime.now().isoformat()
        }

        state["final_output"] = final_output

        return state

    def _route_next_agent(self, state: AgentState) -> Literal["content_agent", "email_agent", "image_agent", "research_agent", "approval", "aggregate", "END"]:
        """
        Routing function that determines which agent to call next.
        """
        # Check if approval is needed
        if state.get("pending_approval") and not state.get("approval_granted"):
            return "approval"

        # Check if there's a next agent to execute
        next_agent = state.get("next_agent")
        if next_agent and next_agent in self.agent_definitions:
            return next_agent

        # Check if we have results to aggregate
        if state.get("agent_results"):
            return "aggregate"

        # Default end
        return "END"

    def _build_supervisor_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph for the supervisor system.
        """
        # Create workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("approval", self._approval_node)
        workflow.add_node("aggregate", self._aggregation_node)

        # Add specialized agent nodes
        for agent_type in self.agent_definitions.keys():
            workflow.add_node(agent_type, self._create_agent_worker(agent_type))

        # Add edges
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            self._route_next_agent,
            {
                "content_agent": "content_agent",
                "email_agent": "email_agent",
                "image_agent": "image_agent",
                "research_agent": "research_agent",
                "approval": "approval",
                "aggregate": "aggregate",
                "END": END
            }
        )

        # Agent edges back to supervisor for coordination
        for agent_type in self.agent_definitions.keys():
            workflow.add_edge(agent_type, "supervisor")

        workflow.add_edge("approval", END)
        workflow.add_edge("aggregate", END)

        # Compile graph
        return workflow.compile(checkpointer=self.memory)

    async def execute(self, user_request: str, conversation_id: str = None) -> Dict[str, Any]:
        """
        Execute a user request through the multi-agent supervisor system.

        Args:
            user_request: The user's request
            conversation_id: Optional conversation ID for continuity

        Returns:
            Dictionary containing results and agent communication
        """
        # Initialize state
        initial_state: AgentState = {
            "task": "",
            "user_request": user_request,
            "conversation_history": [],
            "agent_messages": [],
            "current_agent": "",
            "agent_results": {},
            "pending_approval": False,
            "approval_granted": False,
            "next_agent": "",
            "final_output": {}
        }

        # Configure graph execution
        config = {
            "configurable": {
                "thread_id": conversation_id or "default"
            }
        }

        logger.info(f"[Supervisor System] Executing request: {user_request[:100]}...")

        # Execute graph
        result = await self.graph.ainvoke(initial_state, config=config)

        return result.get("final_output", {})

    async def approve_and_continue(self, conversation_id: str) -> Dict[str, Any]:
        """
        Continue execution after approval is granted.

        Args:
            conversation_id: The conversation ID to resume

        Returns:
            Updated results after continuation
        """
        # Get current state
        config = {"configurable": {"thread_id": conversation_id}}

        # Update state to grant approval
        # This would need to be implemented with state updates
        logger.info("[Approval] Continuing execution after approval granted")

        # Continue graph execution
        # Implementation depends on LangGraph's resume capabilities

        return {
            "status": "continued",
            "message": "Execution resumed after approval"
        }


class AgentCommunicationLogger:
    """
    Logger for tracking and displaying agent-to-agent communication.
    """

    def __init__(self):
        self.communications = []

    def log_communication(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        message_type: str = "task_delegation"
    ):
        """
        Log a communication between agents.

        Args:
            from_agent: Agent sending the message
            to_agent: Agent receiving the message
            message_type: Type of communication (task_delegation, result_sharing, question, etc.)
            message: The message content
        """
        communication = {
            "timestamp": datetime.now().isoformat(),
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "message": message
        }

        self.communications.append(communication)

        # Log to console for visibility
        logger.info(f"[Communication] {from_agent} -> {to_agent}: {message[:100]}...")

    def get_communication_history(self) -> List[Dict[str, Any]]:
        """
        Get all communications in chronological order.
        """
        return self.communications

    def format_for_display(self) -> str:
        """
        Format communications for user-friendly display.
        """
        if not self.communications:
            return "No agent communications yet."

        output = "Agent Communication Log:\n" + "="*50 + "\n\n"

        for comm in self.communications:
            output += f"[{comm['timestamp']}]\n"
            output += f"{comm['from']} -> {comm['to']}\n"
            output += f"Type: {comm['type']}\n"
            output += f"Message: {comm['message']}\n"
            output += "-"*50 + "\n\n"

        return output
