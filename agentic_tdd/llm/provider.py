from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from agentic_tdd.config import Settings

def get_llm_client(settings: Settings) -> BaseChatModel:
    """
    Initializes and returns an OpenAI-compatible LLM client.
    
    Uses LangChain's ChatOpenAI, which supports custom base_url for
    providers like Perplexity, DeepSeek, etc.
    """
    
    # Use the ChatOpenAI class as it is compatible with the OpenAI API standard
    # and allows setting a custom base_url.
    llm = ChatOpenAI(
        model=settings.model_name,
        api_key=settings.api_key,
        base_url=settings.base_url,
        temperature=0.2, # A low temperature for more deterministic code generation
        # streaming=True # Optional: can be added later for live output
    )
    
    return llm
