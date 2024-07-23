import argparse
import os
import shutil
import json
import requests
import re
import subprocess
from typing import Dict, Any, Set
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema.document import Document
from get_embedding_function import get_embedding_function
from langchain_community.vectorstores import Chroma

CHROMA_PATH = "chroma"
DATA_PATH = os.path.join("data", "archive")
DOCKER_DIR = "/var/lib/docker/volumes/paperless_media/_data/documents/archive/"
API_URL = "https://docs.m19182.dev/api/documents/"
API_CREDENTIALS = ("mateo", "1612")


def sanitize_filename(filename: str) -> str:
    return ''.join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

def get_docker_files() -> Set[str]:
    result = subprocess.run(['sudo', 'ls', DOCKER_DIR], capture_output=True, text=True, check=True)
    return set(result.stdout.split())

def copy_file(src: str, dst: str):
    subprocess.run(['sudo', 'cp', src, dst], check=True)
    subprocess.run(['sudo', 'chown', f'{os.getuid()}:{os.getgid()}', dst], check=True)

def get_api_data() -> Dict[str, Any]:
    response = requests.get(API_URL, auth=API_CREDENTIALS)
    response.raise_for_status()
    return response.json()

def format_docker_filename(file_id: str) -> str:
    return f"{int(file_id):07d}.pdf"

def update_titles():
    print("Updating file titles...")
    
    try:
        # Step 1: Get current IDs and titles from API
        api_data = get_api_data()
        api_id_title_map = {str(doc['id']): doc['title'] for doc in api_data['results']}
        api_ids = set(api_id_title_map.keys())
        
        # Step 2: Check current local files
        local_files = set(os.listdir(DATA_PATH))
        local_ids = set(filename.split('_')[0] for filename in local_files if filename.endswith('.pdf'))
        
        # Step 3: Identify missing IDs
        missing_ids = api_ids - local_ids
        
        # Step 4: Get missing files from Docker volume
        new_files = []
        if missing_ids:
            docker_files = get_docker_files()
            for file_id in missing_ids:
                docker_filename = format_docker_filename(file_id)
                if docker_filename in docker_files:
                    src = os.path.join(DOCKER_DIR, docker_filename)
                    sanitized_title = sanitize_filename(api_id_title_map[file_id])
                    new_filename = f"{file_id}_{sanitized_title}.pdf"
                    dst = os.path.join(DATA_PATH, new_filename)
                    if not os.path.exists(dst):
                        print(f"Copying {docker_filename} to local directory as {new_filename}...")
                        copy_file(src, dst)
                        new_files.append(new_filename)
                    else:
                        print(f"File {new_filename} already exists in local directory.")
                else:
                    print(f"File with ID {file_id} not found in Docker volume.")
        
        # Step 5: Update local file titles
        for filename in os.listdir(DATA_PATH):
            if filename.endswith(".pdf"):
                file_id = filename.split('_')[0]
                
                if file_id in api_id_title_map:
                    sanitized_title = sanitize_filename(api_id_title_map[file_id])
                    new_filename = f"{file_id}_{sanitized_title}.pdf"
                    old_path = os.path.join(DATA_PATH, filename)
                    new_path = os.path.join(DATA_PATH, new_filename)
                    
                    if filename != new_filename:
                        try:
                            os.rename(old_path, new_path)
                            print(f"Renamed {filename} to {new_filename}")
                        except OSError as e:
                            print(f"Error renaming {filename}: {e}")
                else:
                    try:
                        os.remove(os.path.join(DATA_PATH, filename))
                        print(f"Deleted {filename} as its ID was not found in the API response")
                    except OSError as e:
                        print(f"Error deleting {filename}: {e}")
        
        return new_files
        
    except subprocess.CalledProcessError as e:
        print(f"Error accessing Docker volume: {e}")
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")


def load_documents():
    loader = DirectoryLoader(DATA_PATH, loader_kwargs={'autodetect_encoding': True}, show_progress=True, silent_errors=True)
    docs = loader.load()
    print(f"Number of documents loaded: {len(docs)}")
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

    new_chunks = [chunk for chunk in chunks_with_ids if chunk.metadata["id"] not in existing_ids]

    if new_chunks:
        print(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("No new documents to add")

def calculate_chunk_ids(chunks):
    for i, chunk in enumerate(chunks):
        source = chunk.metadata.get("source")
        chunk.metadata["id"] = f"{source}:{i}"
    return chunks

def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        print("Existing database cleared.")

def main():
    parser = argparse.ArgumentParser(description="Populate the database with documents from data/archive")
    parser.add_argument("--clear", action="store_true", help="Clear the existing database before populating")
    args = parser.parse_args()

    if args.clear:
        clear_database()

    update_titles()
    documents = load_documents()
    chunks = split_documents(documents)
    add_to_chroma(chunks)
    print("Database population complete.")

if __name__ == "__main__":
    main()