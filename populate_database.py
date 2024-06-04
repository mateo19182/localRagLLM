import argparse
import os
import shutil
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma
 
CHROMA_PATH = "chroma"
DATA_PATH = "data"

def load_documents():
    #loader = PyPDFDirectoryLoader(DATA_PATH)
    text_loader_kwargs={'autodetect_encoding': True}
    loader = DirectoryLoader(DATA_PATH, loader_kwargs=text_loader_kwargs,  show_progress=True, silent_errors=True)  #loader_cls=TextLoader
    docs = loader.load()
    print("n_docs: " + str(len(docs)))
    return docs

def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def add_to_chroma(chunks: list[Document]):
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embedding_function()
    )

    chunks_with_ids = calculate_chunk_ids(chunks)

    existing_items = db.get(include=[]) 
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        #db.persist()
    else:
        print("No new documents to add")

def calculate_chunk_ids(chunks):
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        chunk_id = f"{source}:{current_chunk_index}"
        chunk.metadata["id"] = chunk_id
        current_chunk_index += 1

    return chunks


def delete_file(file_path):
    """Helper function to delete a file."""
    try:
        delete_document(file_path)
        os.remove(file_path)
        print(f"Deleted {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"Error deleting {os.path.basename(file_path)}: {e}")
        return False

def delete_document(path):
    try:
        print(path)
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embedding_function())
        ids_to_delete = db.get(where = {'source': path})['ids']
        db.delete(ids=ids_to_delete)
    except Exception as e:
        raise e


def list_chroma_documents():
    try:
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
        return db.get()
    except Exception as e:
        raise e
    
def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)


if __name__ == "__main__":
    main()
