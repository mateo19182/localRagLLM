import streamlit as st
import os
import re
import query_data
import populate_database

# Initialize session state
if 'update_triggered' not in st.session_state:
    st.session_state.update_triggered = False
if 'new_files' not in st.session_state:
    st.session_state.new_files = []

def escape_markdown(text: str) -> str:
    """Escape special characters in Markdown."""
    md_special_chars = r"[\*\_\`\[\]\(\)\#\+\-\.\!\|]"
    return re.sub(md_special_chars, lambda m: f"\\{m.group(0)}", text)

def update_db():
    with st.spinner("Updating archive contents and database..."):
        try:
            new_files = populate_database.update_titles()
            documents = populate_database.load_documents()
            chunks = populate_database.split_documents(documents)
            populate_database.add_to_chroma(chunks)
            st.session_state.update_triggered = True
            st.session_state.new_files = new_files
        except Exception as e:
            st.error(f"An error occurred while updating: {e}")

def query_section():
    st.subheader("Query Section")
    query_text = st.text_input("Enter your query:", key="query_text")
    if st.button("Run Query"):
        with st.spinner("Querying..."):
            try:
                response, sources = query_data.query_rag(query_text)
                escaped_response = escape_markdown(response)
                st.write(escaped_response)
                if sources:
                    st.markdown("---")
                    st.subheader("Sources")
                    st.write(sources)
            except Exception as e:
                st.error(f"An error occurred: {e}")

def add_documents_section():
    st.subheader("Add Documents")
    uploaded_files = st.file_uploader("Choose a file to add to the database:", type=["pdf", "md", "txt"], accept_multiple_files=True)
    if uploaded_files:
        new_docs = []
        for uploaded_file in uploaded_files:
            if save_uploaded_file(uploaded_file):
                new_docs.append(uploaded_file.name)
        if new_docs:
            st.session_state.update_triggered = True
            st.session_state.new_files = new_docs

def save_uploaded_file(uploaded_file):
    try:
        data_dir = os.path.join("data", "archive")
        os.makedirs(data_dir, exist_ok=True)
        file_path = os.path.join(data_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        st.error(f"An error occurred while saving the file: {e}")
        return False

def list_documents_section():
    st.subheader("Currently Loaded Documents")
    data_dir = os.path.join("data", "archive")
    if not os.path.exists(data_dir):
        st.write("No files found in 'data/archive' directory.")
        return
    
    files = os.listdir(data_dir)
    if files:
        for file in files:
            st.write(f"- {file}")
    else:
        st.write("No files found.")

def clear_database_section():
    st.subheader("Clear Database")
    if st.button("Clear Database"):
        with st.spinner("Clearing database..."):
            try:
                populate_database.clear_database()
                st.session_state.update_triggered = True
                st.session_state.new_files = []
            except Exception as e:
                st.error(f"An error occurred while clearing the database: {e}")

def main():
    st.set_page_config(page_title="Ask docs")
    
    if st.button("Update Database"):
        update_db()
    
    if st.session_state.update_triggered:
        st.success("Archive contents and database updated successfully.")
        if st.session_state.new_files:
            st.info(f"New documents added: {', '.join(st.session_state.new_files)}")
        st.session_state.update_triggered = False
        st.session_state.new_files = []
    
    query_section()
    #add_documents_section()
    list_documents_section()
    #clear_database_section()

if __name__ == "__main__":
    main()