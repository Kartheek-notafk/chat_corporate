import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from styles import SHARED_CSS
from database import (
    get_user_conversations, get_messages, send_message, 
    get_all_users_for_chat, get_or_create_direct_conversation, 
    create_group_conversation, get_registered_users
)
from datetime import timezone, datetime

st.set_page_config(page_title="Messages - CSM", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# Auth guard
if not st.session_state.get("logged_in"):
    st.switch_page("pages/streamlit_login.py")

current_user_id = st.session_state.get("login_id")
current_user_name = f"{st.session_state.get('first_name')} {st.session_state.get('last_name')}"

# Autorefresh every 7000 milliseconds (7 seconds) and add caching
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Only refresh if it's been more than 7 seconds
if (datetime.now() - st.session_state.last_refresh).seconds >= 7:
    st_autorefresh(interval=7000, limit=1, key="chat_autorefresh")
    st.session_state.last_refresh = datetime.now()

st.markdown("""
<style>
.whatsapp-container { display: flex; height: 80vh; border: 1px solid #e0e0e0; border-radius: 10px; overflow: hidden; }
.chat-list-container {
    width: 100%;
    border-right: 1px solid #e0e0e0;
    background-color: #f8f9fa;
    box-sizing: border-box;
    min-height: 75vh;
}
.chat-list-content {
    padding: 0;
    margin: 0;
}
.chat-list-header { padding: 1rem; font-weight: bold; border-bottom: 2px solid #A87B33; color: #A87B33; background-color: #f8f9fa; position: sticky; top: 0; z-index: 10;}
.chat-list-content button { margin: 0 !important; padding: 0.8rem !important; border-bottom: 1px solid #e0e0e0 !important; }
.chat-list-content [data-testid="stVerticalBlock"] { gap: 0 !important; }
.chat-list-content > div { margin: 0 !important; padding: 0 !important; }
.chat-list-content > div > div { margin: 0 !important; }
.chat-window { width: 100%; background-color: #ffffff; min-height: 400px;}
.chat-header { padding: 1.5rem; background-color: #A87B33; color: white; font-weight: bold; display: flex; justify-content: space-between;}
.chat-messages { 
    padding: 1rem; 
    overflow-y: auto; 
    background-color: #e5ddd5; 
    min-height: 300px;
    max-height: 500px;
}
.chat-input { padding: 1rem; border-top: 1px solid #e0e0e0; background-color: #ffffff; }
.chat-item { padding: 0.8rem; border-bottom: 1px solid #e0e0e0; cursor: pointer; transition: background-color 0.3s; margin-bottom: 0px;}
.chat-item:hover { background-color: #e8e8e8; }
.chat-item.active { background-color: #d1d1d1; }
.message { margin-bottom: 0.5rem; display: flex; flex-direction: column; clear: both;}
.message.sent { align-items: flex-end; }
.message.received { align-items: flex-start; }
.message:first-child { margin-top: 0; }
.message-bubble { max-width: 70%; padding: 0.5rem 1rem; border-radius: 15px; word-wrap: break-word; }
.message.sent .message-bubble { background-color: #dcf8c6; color: #000; border-bottom-right-radius: 2px;}
.message.received .message-bubble { background-color: #ffffff; color: #000; border-bottom-left-radius: 2px;}
.message-time { font-size: 0.7rem; color: #999; margin-top: 0.2rem; text-align: right;}
.message-sender { font-size: 0.75rem; color: #A87B33; margin-bottom: 0.2rem; font-weight: bold;}
.open-chat-btn-container button {
    background-color: transparent !important;
    border: 1px solid #A87B33 !important;
    color: #A87B33 !important;
    padding: 0.2rem !important;
    font-size: 0.8rem !important;
    margin-top: 5px !important;
}
</style>
""", unsafe_allow_html=True)

col_title, col_back = st.columns([6, 1])
with col_title:
    st.markdown("### 💬 Real-Time Messages")
with col_back:
    if st.button("← Back", use_container_width=True):
        if st.session_state.get("role") == "admin":
            st.switch_page("pages/admin_dashboard.py")
        else:
            st.switch_page("pages/user_dashboard.py")

st.divider()

if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None

# Modals for creating chats
col_new_chat, col_new_group, _ = st.columns([2, 2, 6])
with col_new_chat:
    if st.button("➕ New Direct Chat", use_container_width=True):
        st.session_state.show_new_chat = True
        st.session_state.show_new_group = False
with col_new_group:
    if st.button("👥 New Group", use_container_width=True):
        st.session_state.show_new_group = True
        st.session_state.show_new_chat = False

if st.session_state.get("show_new_chat"):
    with st.expander("Select User to Chat", expanded=True):
        all_users = get_all_users_for_chat(exclude_id=current_user_id)
        user_options = {u['login_id']: f"{u['first_name']} {u['last_name']} ({u['department']} - {u['role']})" for u in all_users}
        
        selected_user = st.selectbox("Select User", options=list(user_options.keys()), format_func=lambda x: user_options[x], key="new_chat_user")
        if st.button("Start Chat"):
            new_c = get_or_create_direct_conversation(current_user_id, selected_user)
            st.session_state.selected_chat = new_c["conversation_id"]
            st.session_state.show_new_chat = False
            st.rerun()

if st.session_state.get("show_new_group"):
    with st.expander("Create New Group", expanded=True):
        group_name = st.text_input("Group Name")
        all_users = get_all_users_for_chat(exclude_id=current_user_id)
        user_options = {u['login_id']: f"{u['first_name']} {u['last_name']}" for u in all_users}
        
        selected_users = st.multiselect("Select Participants", options=list(user_options.keys()), format_func=lambda x: user_options[x], key="new_group_users")
        if st.button("Create Group"):
            if group_name and selected_users:
                new_g = create_group_conversation(current_user_id, group_name, selected_users)
                st.session_state.selected_chat = new_g["conversation_id"]
                st.session_state.show_new_group = False
                st.rerun()
            else:
                st.error("Enter a group name and select at least one participant.")

# Fetch Conversations
all_my_convos = get_user_conversations(current_user_id)
# Fetch all users for name lookup
all_registered = get_registered_users()
user_lookup = {u['login_id']: f"{u['first_name']} {u['last_name']}" for u in all_registered}
user_lookup["Unknown"] = "System Notification"

def get_convo_display_name(convo):
    if convo.get('is_group'):
        return f"👥 {convo.get('name', 'Group')}"
    else:
        other_id = next((pid for pid in convo['participants'] if pid != current_user_id), current_user_id)
        return user_lookup.get(other_id, other_id)

col_chat_list, col_chat_window = st.columns([3, 7])

with col_chat_list:
    st.markdown('<div style="border:1px solid #ddd; border-radius:10px; background:#f8f9fa; overflow:hidden;">', unsafe_allow_html=True)
    st.markdown('<div class="chat-list-header">Conversations</div>', unsafe_allow_html=True)
    st.markdown('<div style="max-height:500px; overflow-y:auto;">', unsafe_allow_html=True)

    if not all_my_convos:
        st.markdown('<div style="padding: 1rem; color: gray;">No conversations yet. Start a new chat!</div>', unsafe_allow_html=True)
    else:
        for c in all_my_convos:
            c_id = c["conversation_id"]
            c_name = get_convo_display_name(c)
            c_last = c.get("last_message", "No messages yet")
            
            time_obj = c.get("last_message_time")
            if time_obj:
                c_time = time_obj.strftime("%H:%M")
            else:
                c_time = ""

            if st.button(f"**{c_name}**\n\n{c_last}", 
                         key=f"open_{c_id}", 
                         use_container_width=True,
                         help=f"Last message: {c_time}"):
                st.session_state.selected_chat = c_id
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)

with col_chat_window:
    if st.session_state.selected_chat:
        active_c = next((c for c in all_my_convos if c["conversation_id"] == st.session_state.selected_chat), None)
        if active_c:
            c_name = get_convo_display_name(active_c)
            st.markdown(f"### {c_name}")
            st.divider()
            
            # Message history
            messages = get_messages(active_c["conversation_id"])
            
            if not messages:
                st.info("No messages here yet. Say hi!")
            else:
                for m in messages:
                    is_mine = m["sender_id"] == current_user_id
                    sender_name = user_lookup.get(m["sender_id"], m["sender_id"])
                    
                    # Check timestamp format safely
                    try:
                        time_str = m["timestamp"].strftime("%H:%M")
                    except:
                        time_str = ""
                    
                    if is_mine:
                        st.markdown(f"<div style='text-align: right; margin: 10px 0;'><span style='background-color: #dcf8c6; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 70%;'>{m['content']}<br><small style='color: #999;'>{time_str}</small></span></div>", unsafe_allow_html=True)
                    else:
                        if active_c.get('is_group'):
                            st.markdown(f"**{sender_name}**", unsafe_allow_html=True)
                        st.markdown(f"<div style='text-align: left; margin: 10px 0;'><span style='background-color: #ffffff; padding: 8px 12px; border-radius: 15px; display: inline-block; max-width: 70%; border: 1px solid #e0e0e0;'>{m['content']}<br><small style='color: #999;'>{time_str}</small></span></div>", unsafe_allow_html=True)
            
            # Message input
            st.divider()
            with st.form(key="chat_input_form", clear_on_submit=True):
                col_inp, col_btn = st.columns([5, 1])
                with col_inp:
                    msg_text = st.text_input("Type a message...", label_visibility="collapsed")
                with col_btn:
                    if st.form_submit_button("Send", use_container_width=True):
                        if msg_text.strip():
                            send_message(active_c["conversation_id"], current_user_id, msg_text.strip())
                            st.rerun()
    else:
        st.markdown("### 💬 Select a Chat")
        st.info("Select a conversation from the list to start messaging.")