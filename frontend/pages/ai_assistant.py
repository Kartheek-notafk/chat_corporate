# frontend/pages/ai_assistant.py
import streamlit as st
from backend.rag_assistant import answer
import anthropic

client = anthropic.Anthropic()

st.title("AI Assistant")
query = st.chat_input("Ask about schedules, projects, or teammates...")

if query:
    st.chat_message("user").write(query)
    with st.spinner("Thinking..."):
        response = answer(query, st.session_state["user_id"], client)
        st.chat_message("assistant").write(response)