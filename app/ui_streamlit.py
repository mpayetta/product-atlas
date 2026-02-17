import os
import sys

# Ensure project root is on sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import app  # loads config/settings.env via app.__init__
from app.rag import conversational_rag_answer
from app.db import init_schema
from app.conversations_sqlite import (
    list_projects,
    create_project,
    list_conversations,
    create_conversation,
    load_conversation_messages,
    append_message,
    get_conversation,
    update_conversation_title,
    delete_conversation, 
)

APP_TITLE = os.getenv("APP_TITLE", "Product Atlas")
DEFAULT_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Initialize DB schema
init_schema()

st.set_page_config(page_title=APP_TITLE, layout="wide")

# ----- Session state init -----
if "current_project_id" not in st.session_state:
    st.session_state.current_project_id = None

if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"|"assistant", "content": str}

if "is_renaming_conversation" not in st.session_state:
    st.session_state.is_renaming_conversation = False

# ----- Sidebar: compact Settings -----
with st.sidebar:
    st.markdown("## Product Atlas")
    with st.expander("Settings", expanded=False):
        top_k = st.slider(
            "Top-k documents per question",
            min_value=3,
            max_value=20,
            value=DEFAULT_TOP_K,
            step=1,
        )
        st.write(f"Collection: {os.getenv('INGEST_COLLECTION_NAME', 'pm_docs')}")
        st.write(f"Data dir: {os.getenv('INGEST_DATA_DIR', 'data/raw')}")

# ----- Sidebar: compact Projects -----
with st.sidebar:
    with st.expander("Projects", expanded=False):
        projects = list_projects()
        project_names = [p["name"] for p in projects]
        project_id_by_name = {p["name"]: p["id"] for p in projects}

        selected_project_name = None
        if project_names:
            selected_project_name = st.selectbox(
                "Select project",
                options=project_names,
                index=0,
                key="project_select",
            )

        new_project_name = st.text_input("New project name", value="")
        if st.button("Create project"):
            if new_project_name.strip():
                pid = create_project(new_project_name.strip(), "")
                st.session_state.current_project_id = pid
                st.session_state.current_conversation_id = None
                st.session_state.messages = []
                st.rerun()

# Sync current project from selection
if "projects" not in locals():
    projects = list_projects()
    project_names = [p["name"] for p in projects]
    project_id_by_name = {p["name"]: p["id"] for p in projects}

if project_names:
    selected_project_name = st.session_state.get("project_select", project_names[0])
else:
    selected_project_name = None

if selected_project_name:
    selected_project_id = project_id_by_name[selected_project_name]
    if selected_project_id != st.session_state.current_project_id:
        st.session_state.current_project_id = selected_project_id
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.session_state.is_renaming_conversation = False

current_project_id = st.session_state.current_project_id

# ----- Sidebar: Conversations list (compact, link-like) -----
with st.sidebar:
    col_title, col_button = st.sidebar.columns([0.6, 0.4])
    with col_title:
        st.markdown("## Conversations")
    with col_button:
        if st.button("➕ New Chat", key="new_chat_button", type="primary", width="content"):
            if current_project_id is None and projects:
                current_project_id = projects[0]["id"]
                st.session_state.current_project_id = current_project_id

            conv_id = create_conversation(project_id=current_project_id)
            st.session_state.current_conversation_id = conv_id
            st.session_state.messages = []
            st.session_state.is_renaming_conversation = False
            st.rerun()

    conv_list = []
    if current_project_id:
        conv_list = list_conversations(project_id=current_project_id)

    current_conv_id = st.session_state.current_conversation_id

    if conv_list:
        for conv in conv_list:
            cid = conv["id"]
            title = conv.get("title") or cid
            is_current = (cid == current_conv_id)

            # render as link-like text
            if is_current:
                # current convo: plain bold text, no button
                st.button(title, key=f"conv_button_{cid}", type="secondary")
            else:
                # other convos: very small, text-like button
                if st.button(title, key=f"conv_button_{cid}", type="tertiary"):
                    st.session_state.current_conversation_id = cid
                    st.session_state.messages = load_conversation_messages(cid)
                    st.session_state.is_renaming_conversation = False
                    st.rerun()
    else:
        st.write("No conversations yet. Click 'New chat' to start one.")


# ----- Main area: conversation title + rename + delete -----
current_conv_id = st.session_state.current_conversation_id
current_conv_title = "Untitled conversation"

if current_conv_id:
    conv_row = get_conversation(current_conv_id)
    if conv_row:
        current_conv_title = conv_row.get("title") or current_conv_id

if "confirm_delete_conv" not in st.session_state:
    st.session_state.confirm_delete_conv = False

# Header row: title + icons
col_title, col_actions = st.columns([0.7, 0.3])

with col_title:
    st.subheader(current_conv_title)

with col_actions:
    if current_conv_id:
        col_rename, col_delete = st.columns([0.5, 0.5])
        with col_rename:
            if st.button("✏️ Rename", key="rename_toggle_button", help="Rename conversation"):
                st.session_state.is_renaming_conversation = True
                st.rerun()
        with col_delete:
            if not st.session_state.confirm_delete_conv:
                if st.button("🗑", key="delete_conv_button", help="Delete conversation"):
                    # Ask for confirmation
                    st.session_state.confirm_delete_conv = True
                    st.rerun()

# Confirm delete UI
if current_conv_id and st.session_state.confirm_delete_conv:
    st.warning("Are you sure you want to delete this conversation? This cannot be undone.")
    col_yes, col_no = st.columns([0.5, 0.5])
    with col_yes:
        if st.button("Yes, delete", key="confirm_delete_yes"):
            # Delete and select first remaining conversation (if any)
            delete_conversation(current_conv_id)
            st.session_state.confirm_delete_conv = False
            st.session_state.is_renaming_conversation = False

            # Reload conversations for current project
            convs_after = list_conversations(project_id=st.session_state.current_project_id)
            if convs_after:
                first_conv = convs_after[0]
                st.session_state.current_conversation_id = first_conv["id"]
                st.session_state.messages = load_conversation_messages(first_conv["id"])
            else:
                st.session_state.current_conversation_id = None
                st.session_state.messages = []

            st.rerun()
    with col_no:
        if st.button("Cancel", key="confirm_delete_no"):
            st.session_state.confirm_delete_conv = False
            st.rerun()

# Rename UI below header
if current_conv_id and st.session_state.is_renaming_conversation and not st.session_state.confirm_delete_conv:
    new_title = st.text_input(
        "Edit conversation title",
        value=current_conv_title,
        key="conversation_title_edit",
    )
    col_save, col_cancel = st.columns([0.5, 0.5])
    with col_save:
        if st.button("Save title", key="save_title_button"):
            if new_title.strip():
                update_conversation_title(current_conv_id, new_title.strip())
            st.session_state.is_renaming_conversation = False
            st.rerun()
    with col_cancel:
        if st.button("Cancel", key="cancel_title_button"):
            st.session_state.is_renaming_conversation = False
            st.rerun()

st.markdown("---")




# ----- Main area: chat history -----
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ----- Main area: chat input -----
user_input = st.chat_input("Ask a question about your product or docs...")
if user_input:
    # Ensure we have a project
    if st.session_state.current_project_id is None:
        pid = create_project("Default project", "")
        st.session_state.current_project_id = pid

    # Ensure we have a conversation
    if st.session_state.current_conversation_id is None:
        conv_id = create_conversation(project_id=st.session_state.current_project_id)
        st.session_state.current_conversation_id = conv_id

    conv_id = st.session_state.current_conversation_id

    # If conversation has no title yet, set it from first user message (truncated)
    conv_row = get_conversation(conv_id)
    if conv_row and not conv_row.get("title"):
        max_len = 120
        first_question = user_input.strip().replace("\n", " ")
        title = first_question[:max_len]
        if len(first_question) > max_len:
            title += "..."
        update_conversation_title(conv_id, title)

    # Save user message
    append_message(conv_id, "user", user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Build history for LLM (all messages so far)
    history_for_llm = st.session_state.messages.copy()

    # Get assistant answer via conversational RAG
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = conversational_rag_answer(
                user_message=user_input,
                history=history_for_llm,
                k=top_k,
            )
            st.markdown(answer)

    # Save assistant message
    append_message(conv_id, "assistant", answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
