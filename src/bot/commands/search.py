from discord.ext.commands import Context
from pydantic import BaseModel

from src.bot.bot import bot
from src.core import logger
from src.core.llm import get_llm
from src.utils.embedding import find_similar_messages

llm = get_llm()


class SearchResult(BaseModel):
    summary: str


@bot.command()
async def searchs(ctx: Context, *, query: str):
    """Search command that responds with the search query."""
    logger.info(f"Search command invoked with query: {query}")

    similar_messages = await find_similar_messages(query)
    similar_messages_txt = [msg.content for msg in similar_messages]

    structured_llm = llm.with_structured_output(SearchResult)

    SEARCH_PROMPT = """You are an AI assistant that helps users by providing information based on relevant context. Use the provided context to answer the user's query accurately and concisely. If the context does not contain the information needed to answer the query, respond with "I don't know".

    Context: {similar_messages_txt}
    Question: {query}

    """

    response = await structured_llm.ainvoke(
        input=SEARCH_PROMPT.format(
            similar_messages_txt=similar_messages_txt, query=query
        )
    )

    await ctx.send(response.summary)  # type: ignore
