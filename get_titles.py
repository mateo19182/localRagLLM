import json
import requests
import os
import re
import subprocess
import argparse

# API endpoint URL
url = "https://docs.m19182.dev/api/documents/"

# Authentication credentials
username = "mateo"
password = "1612"

# Directories
local_dir = "/home/mateo/localRagLLM/data/archive/"
docker_dir = "/var/lib/docker/volumes/paperless_media/_data/documents/archive/"

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def copy_new_files():
    print("Checking for new files in Docker volume...")
    try:
        result = subprocess.run(['sudo', 'ls', docker_dir], capture_output=True, text=True)
        docker_files = set(result.stdout.split())
        local_files = set(os.listdir(local_dir))
        
        new_files = docker_files - local_files
        
        for file in new_files:
            src = os.path.join(docker_dir, file)
            dst = os.path.join(local_dir, file)
            print(f"Copying {file} to local directory...")
            subprocess.run(['sudo', 'cp', src, dst])
            subprocess.run(['sudo', 'chown', f'{os.getuid()}:{os.getgid()}', dst])
        
        print(f"Copied {len(new_files)} new files.")
    except subprocess.CalledProcessError as e:
        print(f"Error accessing Docker volume: {e}")
        return False
    return True

def rename_and_delete_files(id_title_map):
    for filename in os.listdir(local_dir):
        if filename.endswith(".pdf"):
            file_id = str(int(filename.split('.')[0]))  # Remove leading zeros and convert to string
            
            if file_id in id_title_map:
                new_filename = sanitize_filename(id_title_map[file_id]) + ".pdf"
                old_path = os.path.join(local_dir, filename)
                new_path = os.path.join(local_dir, new_filename)
                
                try:
                    subprocess.run(['sudo', 'mv', old_path, new_path], check=True)
                    print(f"Renamed {filename} to {new_filename}")
                except subprocess.CalledProcessError as e:
                    print(f"Error renaming {filename}: {e}")
            else:
                try:
                    subprocess.run(['sudo', 'rm', os.path.join(local_dir, filename)], check=True)
                    print(f"Deleted {filename} as its ID was not found in the API response")
                except subprocess.CalledProcessError as e:
                    print(f"Error deleting {filename}: {e}")

def main():

    if not copy_new_files():
        return

    response = requests.get(url, auth=(username, password))

    if response.status_code == 200:
        data = json.loads(response.text)
        id_title_map = {str(doc['id']): doc['title'] for doc in data['results']}
        rename_and_delete_files(id_title_map)
    elif response.status_code == 401:
        print("Authentication failed. Please check your username and password.")
    else:
        print(f"Failed to retrieve data. Status code: {response.status_code}")

if __name__ == "__main__":
    main()