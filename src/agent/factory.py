from langchain_core.language_models.chat_models import (
    BaseChatModel,
)

from src.agent.graph import AgentGraph
from src.agent.tools import (
    GetChannelInfo,
    GetServerInfo,
    GetUserInfo,
    ReactToMessage,
    SendMessage,
)
from src.core.llm import get_llm

LLM = get_llm()


def build_base_tools(message_ctx=None, command_ctx=None) -> list[object]:
    base_tools = [
        SendMessage,
        GetChannelInfo,
        GetUserInfo,
        GetServerInfo,
        ReactToMessage,
    ]
    tools = []
    tools.extend(
        tool(message_ctx=message_ctx, command_ctx=command_ctx) for tool in base_tools
    )
    return tools


def create_agent(
    llm: BaseChatModel = LLM,
    tools: list[object] = [],
    message_ctx=None,
    command_ctx=None,
):
    base_tools = build_base_tools(message_ctx=message_ctx, command_ctx=command_ctx)
    tools.extend(base_tools)
    agent = AgentGraph(
        llm=llm,
        tools=tools,  # type: ignore
    )
    return agent
