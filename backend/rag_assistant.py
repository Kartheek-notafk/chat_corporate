# backend/rag_assistant.py
import os
from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

# Initialize embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Use same absolute path as rag_indexer.py
rag_store_path = os.path.join(os.path.dirname(__file__), "../rag_store")
chroma_client = chromadb.PersistentClient(path=rag_store_path)
collection = chroma_client.get_or_create_collection("messages")

# Initialize Groq client
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def retrieve_context(query: str, user_id: str, top_k=15):
    """
    Retrieve relevant messages from conversations the user participates in.
    We fetch broadly (no sender filter) so we get full conversation context,
    not just messages the user themselves sent.
    """
    if collection.count() == 0:
        return []

    q_embedding = model.encode(query).tolist()

    # First try: get messages from conversations where this user is a participant
    # We search all messages and filter by conversation_id later if needed
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=min(top_k, collection.count()),
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    # Filter to only messages from conversations the user is part of
    # (messages sent by the user will have sender == user_id)
    # We include all messages from those conversations for full context
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    # Find conversation IDs the user participates in
    user_conversations = set()
    for meta in metas:
        if meta.get("sender") == user_id:
            user_conversations.add(meta.get("conversation_id"))

    # If user has conversations, return all retrieved messages from those convos
    if user_conversations:
        filtered = [
            doc for doc, meta in zip(docs, metas)
            if meta.get("conversation_id") in user_conversations
        ]
        return filtered if filtered else docs  # fallback to all if filter returns nothing

    # Fallback: return all retrieved docs (useful when index has messages but user_id mismatch)
    return docs


def answer(query: str, user_id: str, llm_client=None) -> str:
    context_chunks = retrieve_context(query, user_id)

    if not context_chunks:
        context_str = "No relevant messages found in the chat history."
    else:
        context_str = "\n".join(context_chunks)

    system_prompt = """You are a workplace assistant for a corporate messaging app.
Your job is to help employees by reading their chat history and answering questions.

You can help with:
- Finding scheduled meetings or calls mentioned in chat
- Tracking project status from messages (blocked, in progress, done)
- Summarizing what was discussed in a conversation
- Finding who said what about a topic

Answer based only on the chat history provided. If there is no relevant information, say so clearly.
Be concise and specific — quote the relevant message if it helps."""

    user_prompt = f"""Chat history retrieved:
{context_str}

User question: {query}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with AI assistant: {str(e)}. Please check your GROQ_API_KEY in the .env file."