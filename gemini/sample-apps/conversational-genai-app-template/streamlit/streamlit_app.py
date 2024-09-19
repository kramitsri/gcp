# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import uuid
from functools import partial

from langchain_core.messages import HumanMessage
from side_bar import SideBar
from streamlit_feedback import streamlit_feedback
from style.app_markdown import markdown_str
from utils.local_chat_history import LocalChatMessageHistory
from utils.message_editing import MessageEditing
from utils.multimodal_utils import format_content, get_parts_from_files
from utils.stream_handler import Client, StreamHandler, get_chain_response

import streamlit as st

USER = "my_user"
EMPTY_CHAT_NAME = "Empty chat"

st.set_page_config(
    page_title="Playground",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("Playground")
st.markdown(markdown_str, unsafe_allow_html=True)

# First time Init of session variables
if "user_chats" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
    st.session_state.uploader_key = 0
    st.session_state.run_id = None
    st.session_state.user_id = USER

    st.session_state["gcs_uris_to_be_sent"] = ""
    st.session_state.modified_prompt = None
    st.session_state.session_db = LocalChatMessageHistory(
        session_id=st.session_state["session_id"],
        user_id=st.session_state["user_id"],
    )
    st.session_state.user_chats = st.session_state.session_db.get_all_conversations()
    st.session_state.user_chats[st.session_state["session_id"]] = {
        "title": EMPTY_CHAT_NAME,
        "messages": [],
    }

side_bar = SideBar(st=st)
side_bar.init_side_bar()
client = Client(
    url=side_bar.url_input_field,
    authenticate_request=side_bar.should_authenticate_request,
)

# Write all messages of current conversation
messages = st.session_state.user_chats[st.session_state["session_id"]]["messages"]
for i, message in enumerate(messages):
    with st.chat_message(message["type"]):
        if message["type"] == "ai":
            if message.get("tool_calls") and len(message.get("tool_calls")) > 0:
                tool_expander = st.expander(label="Tool Calls:", expanded=False)
                with tool_expander:
                    for index, tool_call in enumerate(message["tool_calls"]):
                        # ruff: noqa: E501
                        tool_call_output = message["additional_kwargs"][
                            "tool_calls_outputs"
                        ][index]
                        msg = (
                            f"\n\nEnding tool: `{tool_call['name']}` with\n **args:**\n"
                            f"```\n{json.dumps(tool_call['args'], indent=2)}\n```\n"
                            f"\n\n**output:**\n "
                            f"```\n{json.dumps(tool_call_output['output'], indent=2)}\n```"
                        )
                        st.markdown(msg, unsafe_allow_html=True)

        st.markdown(format_content(message["content"]), unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 94])
        edit_button = f"{i}_edit"
        refresh_button = f"{i}_refresh"
        delete_button = f"{i}_delete"
        content = message["content"]

        if isinstance(message["content"], list):
            content = message["content"][-1]["text"]
        with col1:
            st.button(label="✎", key=edit_button, type="primary")
        if message["type"] == "human":
            with col2:
                st.button(
                    label="⟳",
                    key=refresh_button,
                    type="primary",
                    on_click=partial(MessageEditing.refresh_message, st, i, content),
                )
            with col3:
                st.button(
                    label="X",
                    key=delete_button,
                    type="primary",
                    on_click=partial(MessageEditing.delete_message, st, i),
                )

        if st.session_state[edit_button]:
            edited_text = st.text_area(
                "Edit your message:",
                value=content,
                key=f"edit_box_{i}",
                on_change=partial(MessageEditing.edit_message, st, i, message["type"]),
            )


# Handle new (or modified) user prompt and response
prompt = st.chat_input()
if prompt is None:
    prompt = st.session_state.modified_prompt

if prompt:
    st.session_state.modified_prompt = None
    parts = get_parts_from_files(
        upload_gcs_checkbox=st.session_state.checkbox_state,
        uploaded_files=side_bar.uploaded_files,
        gcs_uris=side_bar.gcs_uris,
    )
    st.session_state["gcs_uris_to_be_sent"] = ""
    parts.append({"type": "text", "text": prompt})
    st.session_state.user_chats[st.session_state["session_id"]]["messages"].append(
        HumanMessage(content=parts).model_dump()
    )

    human_message = st.chat_message("human")
    with human_message:
        existing_user_input = format_content(parts)
        user_input = st.markdown(existing_user_input, unsafe_allow_html=True)

    ai_message = st.chat_message("ai")
    with ai_message:
        status = st.status("Generating answer🤖")
        stream_handler = StreamHandler(st=st)

        get_chain_response(st=st, client=client, stream_handler=stream_handler)

        status.update(label="Finished!", state="complete", expanded=False)

        if (
            st.session_state.user_chats[st.session_state["session_id"]]["title"]
            == EMPTY_CHAT_NAME
        ):
            st.session_state.session_db.set_title(
                st.session_state.user_chats[st.session_state["session_id"]]
            )
        st.session_state.session_db.upsert_session(
            st.session_state.user_chats[st.session_state["session_id"]]
        )
    if len(parts) > 1:
        st.session_state.uploader_key += 1
    st.rerun()

if st.session_state.run_id is not None:
    feedback = streamlit_feedback(
        feedback_type="faces",
        optional_text_label="[Optional] Please provide an explanation",
        key=f"feedback-{st.session_state.run_id}",
    )
    if feedback is not None:
        client.log_feedback(
            feedback_dict=feedback,
            run_id=st.session_state.run_id,
        )
