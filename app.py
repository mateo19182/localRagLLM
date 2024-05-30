# app.py
import streamlit as st
import query_data
import re
import populate_database

def escape_markdown(text):
    """
    Helper function to escape special characters in Markdown.
    """
    md_special_chars = r"[\*\_\`\[\]\(\)\#\+\-\.\!\|]"
    return re.sub(md_special_chars, lambda m: f"\\{m.group(0)}", text)


def main():
    st.title("RAG LLM Query Interface")

    # Query section
    query_text = st.text_input("Enter your query:")
    if query_text:
        response = query_data.query_rag(query_text)
        escaped_response = escape_markdown_characters(response)
        st.write(escaped_response)

    # Add documents section
    st.subheader("Add Documents")
    uploaded_file = st.file_uploader("Choose a file to add to the database:", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        # Save the uploaded file to the /data folder
        with open(f"data/{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File '{uploaded_file.name}' added to the /data folder.")

    # Update database section
    st.subheader("Update Database")
    if st.button("Update Database"):
        documents = populate_database.load_documents()
        chunks = populate_database.split_documents(documents)
        populate_database.add_to_chroma(chunks)
        st.success("Database updated.")

if __name__ == "__main__":
    main()
