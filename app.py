import streamlit as st
import query_data
import re
import populate_database
import os

def escape_markdown(text):
    """
    Helper function to escape special characters in Markdown.
    """
    md_special_chars = r"[\*\_\`\[\]\(\)\#\+\-\.\!\|]"
    return re.sub(md_special_chars, lambda m: f"\\{m.group(0)}", text)


def main():
    st.set_page_config(page_title="RAG LLM Query Interface")
    
    st.title("RAG LLM Query Interface")


    # Query section
    query_section()

    # Add documents section
    add_documents_section()

    # 
    clear_database_section()

def query_section():
    st.subheader("Query Section")
    query_text = st.text_input("Enter your query:", key="query_text")
    if st.button("Run Query") and query_text:
        with st.spinner("Querying..."):
            try:
                response, sources = query_data.query_rag(query_text)
                escaped_response = escape_markdown(response)
                st.write(escaped_response)
                if sources:
                    st.markdown("---")  # Separator line
                    st.subheader("Sources")
                    st.write(sources)
            except Exception as e:
                st.error(f"An error occurred: {e}")


def add_documents_section():
    st.subheader("Add Documents")
    uploaded_file = st.file_uploader("Choose a file to add to the database:", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        save_uploaded_file(uploaded_file)
        st.success(f"File '{uploaded_file.name}' added successfully.")
        if st.button("Update Database"):
            with st.spinner("Updating database..."):
                try:
                    documents = populate_database.load_documents()
                    chunks = populate_database.split_documents(documents)
                    result = populate_database.add_to_chroma(chunks)
                    st.success(f"Database updated successfully.")
                except Exception as e:
                    st.error(f"An error occurred while updating the database: {e}")    
        


def save_uploaded_file(uploaded_file):
    try:
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
    except Exception as e:
        st.error(f"An error occurred while saving the file: {e}")


def clear_database_section():
    st.subheader("Clear Database")
    if st.button("Clear Database"):
        with st.spinner("Updating database..."):
            try:
                populate_database.clear_database()
                st.success(f"Database cleared successfully.")
            except Exception as e:
                st.error(f"An error occurred while clearing the database: {e}")

if __name__ == "__main__":
    main()
