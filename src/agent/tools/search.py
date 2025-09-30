import dotenv
from langchain_core.tools import StructuredTool
from langchain_google_community import GoogleSearchAPIWrapper

from src.core.config import settings

dotenv.load_dotenv()


PROMPT = "Search {search_engine}'s search API for general web results and information. Does not involve browser interaction."

# Google search Tool
google_search_tool = GoogleSearchAPIWrapper(
    google_api_key=settings.GEMINI_API_KEY, google_cse_id=settings.GOOGLE_CLIENT_SECRET
)
google_search = StructuredTool.from_function(
    name="google_search",
    description=PROMPT.format(search_engine="Google"),
    func=google_search_tool.run,
    return_direct=False,
)
