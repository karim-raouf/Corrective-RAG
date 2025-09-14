from langchain_tavily import TavilySearch
from helpers.config import get_setting

app_settings = get_setting()

# Initialize search tool
tavily_search = TavilySearch(
    max_results=5,
    tavily_api_key=app_settings.TAVILY_API_KEY,
    )