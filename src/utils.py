import os
from pydantic import SecretStr
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from dotenv import load_dotenv

load_dotenv()


def setup_llm():
    """
    Setup LLM client based on available environment variables.

    Priority:
    1. If Azure OpenAI environment variables are present, use Azure OpenAI
    2. If OpenAI API key is present, use OpenAI
    3. Otherwise, raise an error

    Returns:
        Configured LLM client (either AzureChatOpenAI or ChatOpenAI)
    """
    # Check for Azure OpenAI configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")

    # Check for OpenAI configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if azure_endpoint and azure_api_key:
        # Use Azure OpenAI
        return setup_azure_openai()
    elif openai_api_key:
        # Use OpenAI
        return setup_openai()
    else:
        raise ValueError(
            "Either AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY or OPENAI_API_KEY must be provided"
        )


def setup_azure_openai():
    """Setup Azure OpenAI client."""
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    if not azure_endpoint or not azure_api_key:
        raise ValueError("AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY required")

    return AzureChatOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=SecretStr(azure_api_key),
        azure_deployment=azure_deployment,
        api_version=azure_api_version,
        temperature=0,
    )


def setup_openai():
    """Setup OpenAI client."""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY required")

    return ChatOpenAI(
        api_key=SecretStr(openai_api_key),
        model=openai_model,
        temperature=0,
    )
