import os
import streamlit as st
import populate_database
import app

def list_files_in_data():
    """
    List all files in the 'data' directory.
    """
    data_dir = "data"
    if not os.path.exists(data_dir):
        st.write("No files found in 'data' directory.")
        return []

    files = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    return files

def delete_file(file_path):
    """Helper function to delete a file."""
    try:
        os.remove(file_path)
        st.success(f"Deleted {os.path.basename(file_path)}")
        app.update_db()
        return True
    except Exception as e:
        st.error(f"Error deleting {os.path.basename(file_path)}: {e}")
        return False

def list_documents_section():
    st.subheader("Currently Loaded Documents")

    # Refresh the file list each time the function is called
    st.session_state.files = list_files_in_data()

    if st.session_state.files:
        files_to_display = st.session_state.files[:]
        for file in files_to_display:
            file_name = os.path.basename(file)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {file_name}")
            with col2:
                if st.button("Delete", key=file):
                    if delete_file(file):
                        # Update the list in the session state after deletion
                        st.session_state.files = list_files_in_data()
    else:
        st.write("No files found.")

# Ensuring the session state is initialized properly
if 'files' not in st.session_state:
    st.session_state.files = list_files_in_data()

    # List documents in Chroma database
    # st.write("### Documents in Chroma database:")
    # try:
    #     documents = populate_database.list_chroma_documents()
    #     if documents:
    #         for doc in documents:
    #             st.write(f"- {doc}")
    #     else:
    #         st.write("No documents found in Chroma database.")
    # except Exception as e:
    #     st.error(f"An error occurred while listing documents from the Chroma database: {e}")
