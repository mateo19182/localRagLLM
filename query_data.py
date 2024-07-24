import argparse
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama

from get_embedding_function import get_embedding_function

CHROMA_PATH = "chroma"

PROMPT_TEMPLATE = """
You are an AI assistant tasked with answering queries based on the provided context. Your goal is to provide accurate and relevant information.

The query is: {question}

Context:
{context}

Instructions:
1. If the context contains relevant information to answer the question, use it to formulate your response.
2. If the context does not contain enough information to fully answer the question, state that clearly and provide any partial information that is available.
3. If you're unsure about any part of your answer, express that uncertainty.
4. Keep your answer concise and directly related to the question.

Question: {question}

Answer:
"""

def query_rag(query_text: str):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    results = db.similarity_search_with_score(query_text, k=5)
    
    # Sort results by score (ascending order) and format context
    sorted_results = sorted(results, key=lambda x: x[1])
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _ in sorted_results])
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    print("PROMPT \n")
    print(prompt)

    model = Ollama(model="llama3")
    response_text = model.invoke(prompt)

    sources = [doc.metadata.get("id", None) for doc, _score in sorted_results]
    print("RESPONSE \n")

    formatted_response = f"Response: {response_text}\nSources: {sources}"
    print(formatted_response)
    return response_text, sources

def main():
    parser = argparse.ArgumentParser(description="Query the RAG system")
    parser.add_argument("query", type=str, help="The query to process")
    args = parser.parse_args()
    
    query_rag(args.query)

if __name__ == "__main__":
    main()