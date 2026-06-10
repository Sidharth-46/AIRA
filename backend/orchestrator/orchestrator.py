"""
AIRA — Agent Orchestrator
Central coordination for the multi-agent pipeline.
Routes: User Request → Planner → Research → Coder → Reviewer → Response
"""

from typing import Generator

from agents.planner_agent import PlannerAgent
from agents.research_agent import ResearchAgent
from agents.coder_agent import CoderAgent
from agents.reviewer_agent import ReviewerAgent
from agents.general_agent import GeneralAgent
from orchestrator.context_manager import ContextManager
from orchestrator.token_manager import TokenManager
from services.model_providers.model_registry import get_provider
from services.model_router import get_model_router
import time
from utils.logger import get_logger

logger = get_logger("orchestrator")


class AgentOrchestrator:
    """
    Central orchestrator for AIRA's multi-agent system.
    
    Pipeline:
        Simple queries → Coder only (fast path)
        Complex tasks  → Planner → Research → Coder → Reviewer (full pipeline)
    
    Yields SSE events:
        {"event": "agent_status", "data": "planner|research|coder|reviewer"}
        {"event": "token", "data": "..."}
        {"event": "done", "data": ""}
    """

    def __init__(self):
        self.context_manager = ContextManager()
        provider = get_provider()
        context_window = provider.get_context_window()
        self.token_manager = TokenManager(context_window)

        # Initialize agents with the active model provider
        self.planner = PlannerAgent(provider)
        self.research = ResearchAgent(provider)
        self.coder = CoderAgent(provider)
        self.reviewer = ReviewerAgent(provider)
        self.general = GeneralAgent(provider)

        self._agents = {
            "planner": self.planner,
            "research": self.research,
            "coder": self.coder,
            "reviewer": self.reviewer,
            "general": self.general,
        }
        
        self.router = get_model_router()

    def process(self, message: str, history: list = None,
                project_info: str = None, file_contents: str = None,
                rag_results: str = None, user_preferences: str = None,
                workspace_context_string: str = None) -> Generator[dict, None, None]:
        """
        Process a user message through the agent pipeline.
        Yields SSE-formatted events.
        """
        history = history or []

        # Step 1: Intelligent Routing
        context_size = len(file_contents or "") + len(project_info or "") + len(rag_results or "")
        workspace_context = bool(file_contents or project_info)
        
        route_info = self.router.route_request(message, workspace_context=workspace_context, context_size=context_size)
        intent = route_info["intent"]
        model = route_info["model"]
        routing_reason = route_info["routing_reason"]
        timeout = route_info["timeout"]

        logger.info(f"Routed: intent={intent}, model={model}, reason={routing_reason}")
        
        # Emit intent and model status
        yield {"event": "task_intent", "data": intent}
        yield {"event": "model_status", "data": {"model": model, "intent": intent}}
        
        # Inject the selected provider
        selected_provider = get_provider(model)
        for agent in self._agents.values():
            agent.provider = selected_provider

        # Determine Pipeline
        if intent == "GENERAL_CHAT":
            pipeline = ["general"]
        elif intent == "CODING":
            # For complex coding, maybe planner + coder + reviewer? 
            # Prompt says "Planner and Reviewer only when required. Do not invoke them for every coding request."
            # We'll stick to just coder for now, or maybe planner/coder/reviewer for large context. Let's do coder.
            pipeline = ["coder"]
        elif intent == "REPOSITORY_ANALYSIS":
            pipeline = ["research", "coder"]
        elif intent == "DOCUMENTATION":
            pipeline = ["coder"]
        else:
            pipeline = ["coder"]

        # Build initial context
        context = self.context_manager.build_context(
            history=history,
            project_info=project_info,
            file_contents=file_contents,
            rag_results=rag_results,
            user_preferences=user_preferences,
            workspace_context_string=workspace_context_string,
            original_request=message,
        )

        task = {"message": message, "intent": intent}
        full_response = ""

        # Step 2: Execute pipeline
        start_time = time.time()
        first_token_time = 0

        for agent_name in pipeline:
            agent = self._agents.get(agent_name)
            if not agent:
                continue

            yield {"event": "agent_status", "data": agent_name}
            
            try:
                # Synchronous agents
                if agent_name in ["planner", "research", "reviewer"]:
                    result = agent.execute(task, context)
                    if agent_name == "planner":
                        context["plan"] = result.get("plan", {})
                    elif agent_name == "research":
                        context["research"] = result.get("content", "")
                    elif agent_name == "reviewer":
                        review = result.get("review", {})
                        if review.get("verdict") == "fail":
                            yield {"event": "agent_status", "data": "coder"}
                            context["review_feedback"] = result.get("content", "")
                            full_response = ""
                            for token in self.coder.stream_execute(task, context):
                                if time.time() - start_time > timeout:
                                    raise TimeoutError("Request timed out")
                                full_response += token
                                yield {"event": "token", "data": token}

                # Streaming agents
                elif agent_name in ["coder", "general"]:
                    for token in agent.stream_execute(task, context):
                        if first_token_time == 0:
                            first_token_time = time.time() - start_time
                        
                        if time.time() - start_time > timeout:
                            raise TimeoutError("Request timed out")
                            
                        full_response += token
                        yield {"event": "token", "data": token}

            except TimeoutError as e:
                error_msg = str(e)
                logger.error(f"MODEL_TIMEOUT: {error_msg}")
                yield {"event": "timeout", "data": f"\n\n[Error: {error_msg}]"}
                self.router.record_metrics(model, False, 0, 0, 0)
                return
            except Exception as exc:
                error_msg = str(exc)
                logger.error(f"Agent {agent_name} failed: {error_msg}")
                yield {"event": "token", "data": f"\n\n[Error: Generation failed — {error_msg}]"}
                self.router.record_metrics(model, False, 0, 0, 0)
                return

        # Track usage and record metrics
        completion_time = time.time() - start_time



        self.token_manager.track_usage(
            "pipeline",
            self.token_manager.estimate_tokens(message),
            self.token_manager.estimate_tokens(full_response),
        )

        logger.info("MODEL_GENERATION_COMPLETE")
        self.router.record_metrics(model, True, first_token_time, first_token_time, completion_time)

        # Done event
        yield {"event": "done", "data": full_response}
