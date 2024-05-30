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

    files = os.listdir(data_dir)
    return files

def delete_file(file_name):
    """Helper function to delete a file."""
    try:
        os.remove(os.path.join("data",file_name))
        st.success(f"Deleted {file_name}")
        app.update_db()
    except Exception as e:
        st.error(f"Error deleting {file_name}: {e}")


def list_documents_section():
    st.subheader("Currently Loaded Documents")

    # Use Streamlit session state to manage the list of files
    if 'files' not in st.session_state:
        st.session_state.files = list_files_in_data()

    if st.session_state.files:
        # Make a copy of the list to modify while iterating
        files_to_display = st.session_state.files[:]
        for file in files_to_display:
            file_name = os.path.basename(file)
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {file_name}")
            with col2:
                # Create a unique key for the button using the file name
                if st.button("Delete", key=file):
                    if delete_file(file):
                        # If file is deleted, remove it from the session state list
                        st.session_state.files.remove(file)
    else:
        st.write("No files found.")
    
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
