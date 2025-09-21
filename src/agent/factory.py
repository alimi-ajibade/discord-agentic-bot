from langchain_core.language_models.chat_models import (
    BaseChatModel,
)

from src.agent.graph import AgentGraph
from src.agent.tools.add import AddTool
from src.agent.tools.subtract import SubtractTool
from src.core.llm import get_llm

tools = [AddTool(), SubtractTool()]  # type: ignore
LLM = get_llm()


def create_agent(
    llm: BaseChatModel = LLM,
    tools: list[object] = tools,
):
    agent = AgentGraph(
        llm=llm,
        tools=tools,  # type: ignore
    )
    return agent
