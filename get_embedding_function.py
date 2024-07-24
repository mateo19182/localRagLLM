from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.embeddings.bedrock import BedrockEmbeddings
from langchain_openai import OpenAIEmbeddings

def get_embedding_function():
    embeddings = OllamaEmbeddings(model="snowflake-arctic-embed")
    return embeddings

    #embeddings = OllamaEmbeddings(model="llama3")

    #openai_api_key = ""
    # if not openai_api_key:
    #     raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # embeddings = OpenAIEmbeddings(
    #     model="text-embedding-ada-002",  # This specifies the Ada-002 model
    #     openai_api_key=openai_api_key
    # )
