import os
import streamlit as st
from service.cheese_chatbot import chatbot
from pinecone import Pinecone
from dotenv import load_dotenv


load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Custom CSS for chat interface
st.markdown("""
<style>
    /* Chat container styling */
    .stChatMessage {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 10px;
        background: linear-gradient(145deg, #2d3748, #1a202c);
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        color: #e2e8f0;
    }
    
    /* Custom title styling */
    .main-title {
        text-align: center;
        background: linear-gradient(120deg, #60a5fa, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 20px;
        font-size: 2.8em;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Welcome message styling */
    .welcome-message {
        text-align: center;
        color: #e2e8f0;
        font-style: italic;
        margin-bottom: 30px;
        background: linear-gradient(135deg, #374151, #1f2937);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    /* Theme overrides */
    .stApp {
        background: linear-gradient(135deg, #1a202c, #2d3748) !important;
    }

    .stChatInputContainer {
        background: linear-gradient(145deg, #2d3748, #1a202c);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 15px;
        padding: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    /* Enhance chat input */
    .stChatInput {
        border-radius: 10px !important;
        border: 1px solid #4a5568 !important;
        background: #2d3748 !important;
        color: #e2e8f0 !important;
    }

    /* Style for user messages */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(145deg, #3b82f6, #1d4ed8);
        color: #ffffff;
    }

    /* Style for assistant messages */
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(145deg, #4c1d95, #5b21b6);
        color: #ffffff;
    }

    /* Header container with gradient border */
    .header-container {
        padding: 20px;
        margin-bottom: 30px;
        border-radius: 20px;
        background: linear-gradient(145deg, #2d3748, #1a202c);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }

    /* Spinner animation enhancement */
    .stSpinner {
        border-width: 3px !important;
        border-color: #60a5fa !important;
        border-bottom-color: transparent !important;
    }

    /* Additional elements styling */
    .stMarkdown {
        color: #e2e8f0 !important;
    }

    .stButton button {
        background: linear-gradient(145deg, #3b82f6, #1d4ed8) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        background: #1a202c;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(145deg, #3b82f6, #1d4ed8);
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_pinecone():
    """Initialize Pinecone connection"""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        return pc.Index("cheese-index")
    except Exception as e:
        st.error(f"Error initializing Pinecone: {e}")
        return None
            
def main():
    st.markdown("""
        <div class='header-container'>
            <h1 class='main-title'>🧀 Cheese Expert Chatbot</h1>
            <div class='welcome-message'>
                <span style='font-size: 24px;'>👋</span> 
                Welcome to your personal cheese expert! I'm here to help you discover and learn about our amazing selection of cheeses.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Initialize Pinecone
    index = initialize_pinecone()
    if not index:
        st.error("Failed to initialize Pinecone. Please check your API key and connection.")
        return

    chat_container = st.container()
    with chat_container:
        # Display chat messages from history
        for message in st.session_state.messages:
            if message["role"] == "user":
                # User avatar can be an emoji, image URL, or a PIL Image
                avatar_user = "🧑‍🍳"  # Using an emoji as avatar
                # Or use an image: avatar_user = "https://path-to-user-image.jpg"
                
                with st.chat_message(message["role"], avatar=avatar_user):
                    st.markdown(message["content"])
                    
            elif message["role"] == "assistant":
                # Assistant avatar
                avatar_assistant = "🤖"  # Using an emoji as avatar
                # Or use an image: avatar_assistant = "https://path-to-assistant-image.jpg"
                
                with st.chat_message(message["role"], avatar=avatar_assistant):
                    st.markdown(message["content"])


    # Accept user input
    if prompt := st.chat_input("Ask about cheese..."):
        # Display user message in chat message container
        with st.chat_message("user", avatar="🧑‍🍳"):
            st.markdown(prompt)
        
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "🧑‍🍳"})

        # Display assistant response in chat message container with loading indicator
        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            with st.spinner("..."):
                response = chatbot(prompt, index, st)
                message_placeholder.markdown(response)
            
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()