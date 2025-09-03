from pathlib import Path
from pydantic_settings import BaseSettings , SettingsConfigDict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


class settings(BaseSettings):
    
    TAVILY_API_KEY: str
    
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_API_VERSION: str    
    
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str
    AZURE_OPENAI_EMBEDDING_VERSION: str
    
    class Config:
        env_file = ".env"


def get_setting():
    return settings()

