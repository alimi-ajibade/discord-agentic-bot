from contextlib import redirect_stdout
import io
from typing import Literal, TypedDict

from discord import Message as DiscordMessageContext
from discord.ext.commands import Context as DiscordCommandContext
from langchain.tools import BaseTool
from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from src.core import logger
from src.core.llm import get_llm

CUSTOM_AGENT_INSTRUCTION = ""


class AgentState(TypedDict):
    instruction: str
    messageCtx: DiscordMessageContext | None
    commandCtx: DiscordCommandContext | None
    user_id: str | None
    user_request: str
    validation_approved: bool
    validation_feedback: str | None
    messages: list[BaseMessage]
    remaining_steps: int


class AgentGraph:
    def __init__(
        self,
        tools: list[BaseTool],
        llm: BaseChatModel | None = None,
    ):
        self.llm = llm or get_llm()
        self.compiled_graph = StateGraph(AgentState)  # Will be set in _build_graph
        self.tools = tools
        self._builder = StateGraph(AgentState)
        self.tools_dict = {t.name: t for t in tools}
        self.executor_agent = None

    async def _build_graph(self, state: AgentState):
        executor_graph = await self._get_agent(state)

        # NODES
        self._builder.add_node(node="validate_task", action=self._validate_task)
        self._builder.add_node(node="execute_task", action=executor_graph)

        # EDGES
        self._builder.add_edge(start_key=START, end_key="validate_task")
        self._builder.add_conditional_edges(
            source="validate_task",
            path=self._handle_validation,
            path_map={"success": "execute_task", "failure": END},
        )
        self._builder.add_edge(start_key="execute_task", end_key=END)

        checkpointer = InMemorySaver()
        self.compiled_graph = self._builder.compile(checkpointer=checkpointer)

    async def _validate_task(self, state: AgentState) -> dict:
        logger.info("--------📝 validating task--------")
        logger.info(f"User request: {state['user_request']}")

        class ValidationResult(BaseModel):
            is_valid: bool
            reason: str | None

        structured_llm = self.llm.with_structured_output(ValidationResult)
        VALIDATION_PROMPT = f"You are an expert at determining and rejecting requests that are stupid, unsuitable, harmful, illegal, or inappropriate for an AI agent to handle. Tell me if this prompt is suitable to be validated or not {state['user_request']}"

        is_valid = False
        reason = "Validation error"

        try:
            response = await structured_llm.ainvoke(VALIDATION_PROMPT)
            logger.info(f"Validation result: {response}, type: {response}")
            is_valid = response.is_valid
            reason = response.reason
        except Exception as e:
            logger.error(f"Error during validation: {e}")

        logger.warning(f"is_valid: {is_valid}, reason: {reason}")

        return {
            "validation_approved": is_valid,
            "validation_feedback": reason,
        }

    async def _get_agent(self, state: AgentState):
        prompt = f"perform the task {state['user_request']}. Keep in mind that this is your base instruction {state['instruction']}"
        if self.executor_agent:
            return self.executor_agent
        logger.info("--------📝 executing task--------")
        checkpointer = InMemorySaver()
        self.executor_agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            name="executor_agent",
            state_schema=AgentState,
            prompt=prompt,
            checkpointer=checkpointer,
        )

        return self.executor_agent

    async def _handle_validation(
        self, state: AgentState
    ) -> Literal["success", "failure"]:
        logger.info("--------📝 handling validation--------")
        if state.get("validation_approved"):
            return "success"
        return "failure"

    async def ainvoke(
        self,
        user_request: str,
        messageCtx: DiscordMessageContext | None,
        commandCtx: DiscordCommandContext | None = None,
        instruction: str = CUSTOM_AGENT_INSTRUCTION,
        config: RunnableConfig | None = None,
        user_id: str | None = None,
    ):
        # # Initialize with system message and user request
        # initial_messages = [
        #     SystemMessage(
        #         content=instruction
        #         or "You are a helpful assistant that can use tools to answer questions."
        #     ),
        #     HumanMessage(content=user_request),
        # ]

        initial_state = AgentState(
            instruction=instruction,
            messageCtx=messageCtx,
            commandCtx=commandCtx,
            user_id=user_id,
            user_request=user_request,
            validation_approved=False,
            validation_feedback=None,
            messages=[],
            remaining_steps=10,
        )

        await self._build_graph(state=initial_state)

        # Generate a thread config if none provided
        if config is None:
            config = {"configurable": {"thread_id": f"user_{user_id or 'unknown'}"}}

        # Ensure compiled_graph is available
        if self.compiled_graph is None:
            raise RuntimeError("Graph not compiled properly")

        await self._alog_executor_stream(
            stream=self.compiled_graph.astream(
                input=initial_state, config=config, stream_mode="values", subgraphs=True
            )
        )

        graph_state = await self.compiled_graph.aget_state(config)
        return graph_state.values.get("validation_feedback")

    async def _alog_executor_stream(self, stream):
        async for s in stream:
            try:
                messages = s[-1].get("messages", [])

                if len(messages) > 0:
                    message = messages[-1]

                    if isinstance(message, tuple):
                        logger.debug(message)

                    else:
                        with io.StringIO() as buf, redirect_stdout(buf):
                            message.pretty_print()
                            pretty_out = buf.getvalue()

                        logger.debug(f"\n{pretty_out}")
            except Exception as e:
                logger.error(f"Error processing stream item: {e}")
